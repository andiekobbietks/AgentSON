"""AgentSON distribution — cross-registry publishing.

Supports Docker Hub (OCI artifacts) and LXD Hub (system containers).
AgentSON sessions are portable across both registries without conversion.
"""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def publish_docker(
    session_path: str,
    image_tag: str,
    registry: str = "docker.io",
    push: bool = False,
) -> Dict:
    """Package an AgentSON session as a Docker OCI artifact.

    Uses Docker's OCI artifact support to store .agentson files
    with provenance metadata (model-SBOM-style).

    Args:
        session_path: Path to .agentson file
        image_tag: Docker image tag (e.g., "user/session:bug-fix-42")
        registry: Docker registry host
        push: If True, push to registry after building

    Returns:
        Dict with build result metadata
    """
    session_path = Path(session_path)
    if not session_path.exists():
        raise FileNotFoundError(f"Session not found: {session_path}")

    with open(session_path, "r") as f:
        session = json.load(f)

    session_id = session.get("id", session_path.stem)
    full_tag = f"{registry}/{image_tag}" if registry else image_tag

    # Build a minimal Docker image with the .agentson file as a label
    dockerfile = f"""FROM scratch
COPY {session_path.name} /session.agentson
LABEL agentson.session.id="{session_id}"
LABEL agentson.tool="{session.get('tool', {}).get('name', 'unknown')}"
LABEL agentson.entries="{len(session.get('entries', []))}"
LABEL org.opencontainers.image.title="AgentSON Session"
LABEL org.opencontainers.image.description="Agent session provenance artifact"
LABEL org.opencontainers.image.created="{datetime.now(timezone.utc).isoformat()}"
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "Dockerfile").write_text(dockerfile)

        # Copy session file
        dest = tmp / session_path.name
        dest.write_bytes(session_path.read_bytes())

        # Build the image
        result = subprocess.run(
            ["docker", "build", "-t", full_tag, "."],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "tag": full_tag,
                "error": result.stderr.strip(),
                "session_id": session_id,
            }

        tag_info = {"tag": full_tag, "session_id": session_id}

        if push:
            push_result = subprocess.run(
                ["docker", "push", full_tag],
                capture_output=True,
                text=True,
            )
            if push_result.returncode != 0:
                tag_info["push_error"] = push_result.stderr.strip()
            tag_info["pushed"] = push_result.returncode == 0

        tag_info["success"] = True
        return tag_info


def publish_lxd(
    session_path: str,
    image_alias: str,
    remote: Optional[str] = None,
    push: bool = False,
) -> Dict:
    """Package an AgentSON session as an LXD image.

    LXD system containers persist agent state better than Docker's
    ephemeral process model. Sessions are embedded as /root/session.agentson.

    Args:
        session_path: Path to .agentson file
        image_alias: LXD image alias (e.g., "agentson/session/bug-fix-42")
        remote: LXD remote server name (optional)
        push: If True, push to LXD remote after building

    Returns:
        Dict with build result metadata
    """
    session_path = Path(session_path)
    if not session_path.exists():
        raise FileNotFoundError(f"Session not found: {session_path}")

    with open(session_path, "r") as f:
        session = json.load(f)

    session_id = session.get("id", session_path.stem)

    # Create a container, inject the session, publish as image
    container_name = f"agentson-publish-{session_id[:8]}" if len(session_id) > 8 else f"agentson-publish-{session_id}"

    commands = [
        ["lxc", "init", "ubuntu-minimal:24.04", container_name],
        ["lxc", "file", "push", str(session_path), f"{container_name}/root/session.agentson"],
        ["lxc", "exec", container_name, "--", "mkdir", "-p", "/root/.agentson"],
        ["lxc", "exec", container_name, "--", "cp", "/root/session.agentson", f"/root/.agentson/{session_path.name}"],
    ]

    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return {
                "success": False,
                "alias": image_alias,
                "step": " ".join(cmd[:3]),
                "error": result.stderr.strip(),
                "session_id": session_id,
            }

    # Publish as image
    publish_cmd = ["lxc", "publish", container_name, "--alias", image_alias]
    if remote:
        publish_cmd.extend(["--remote", remote])

    result = subprocess.run(publish_cmd, capture_output=True, text=True)

    # Cleanup container
    subprocess.run(["lxc", "delete", container_name, "--force"], capture_output=True)

    tag_info = {
        "alias": image_alias,
        "session_id": session_id,
        "success": result.returncode == 0,
    }

    if result.returncode != 0:
        tag_info["error"] = result.stderr.strip()
    elif push and remote:
        push_result = subprocess.run(
            ["lxc", "image", "copy", f"{image_alias}:", f"{remote}:", "--alias", image_alias],
            capture_output=True,
            text=True,
        )
        tag_info["pushed"] = push_result.returncode == 0
        if push_result.returncode != 0:
            tag_info["push_error"] = push_result.stderr.strip()

    return tag_info


def publish(
    session_path: str,
    registry: str = "docker",
    tag: Optional[str] = None,
    push: bool = False,
) -> Dict:
    """Publish an AgentSON session to any supported registry.

    Args:
        session_path: Path to .agentson file
        registry: Target registry ("docker" or "lxd")
        tag: Image tag or alias (auto-generated if None)
        push: If True, push to remote registry

    Returns:
        Dict with publish result metadata
    """
    session_path = Path(session_path)
    session_id = session_path.stem

    if tag is None:
        tag = f"agentson/session/{session_id}"

    if registry == "docker":
        return publish_docker(str(session_path), tag, push=push)
    elif registry == "lxd":
        return publish_lxd(str(session_path), tag, push=push)
    else:
        raise ValueError(f"Unknown registry: {registry}. Supported: docker, lxd")


def list_local_images(registry: str = "docker") -> List[Dict]:
    """List locally available AgentSON images for a given registry.

    Args:
        registry: "docker" or "lxd"

    Returns:
        List of image metadata dicts
    """
    images = []

    if registry == "docker":
        result = subprocess.run(
            ["docker", "images", "--filter", "label=agentson.session.id", "--format", "json"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        img = json.loads(line)
                        images.append(img)
                    except json.JSONDecodeError:
                        pass

    elif registry == "lxd":
        result = subprocess.run(
            ["lxc", "image", "list", "--format", "json"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            try:
                images = json.loads(result.stdout)
            except json.JSONDecodeError:
                pass

    return images
