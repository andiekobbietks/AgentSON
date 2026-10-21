"""Tests for the premium structure pipeline and the network doctor."""
import json
import os
import tempfile
from pathlib import Path

from agentson_platform import netdoctor, structure


def _write_stream(directory: Path) -> Path:
    fp = directory / "s1.agentson"
    lines = [
        {"type": "stream-meta", "stream_id": "sess-1", "agents": [{"id": "opencode", "capabilities": ["conversation"]}, {"id": "user", "capabilities": ["query"]}], "source": {"platform": "opencode", "sessionId": "sess-1"}},
        {"type": "agent", "agent": {"id": "opencode"}, "text": "hello", "timestamp": 1},
    ]
    fp.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
    return fp


def test_build_graph_reads_real_stream():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _write_stream(d)
        graph = structure.build_graph(str(d))
        assert graph["schema"] == "agentson.structure/v1"
        node_ids = {n["id"] for n in graph["nodes"]}
        assert "opencode" in node_ids
        assert any(e["relation"] == "produced-by" for e in graph["edges"])


def test_build_csv_writes_files():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _write_stream(d)
        out = d / "out"
        files = structure.build_csv(str(d), str(out))
        assert len(files) == 2
        for f in files:
            assert Path(f).exists()


def test_training_export():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _write_stream(d)
        path = structure.build_training_export(str(d), str(d / "out"))
        assert Path(path).exists()


def test_offline_check_makes_no_network_call():
    result = netdoctor.offline_check()
    assert result["ok"] is True
    assert result["network_calls_by_core"] == 0


def test_proxy_env_shape():
    result = netdoctor.proxy_env()
    assert result["probe"] == "proxy"
    assert "variables" in result


def test_dns_probe_reports_failure_without_raising():
    result = netdoctor.dns_probe("nonexistent-host-for-agentson-test.invalid")
    assert result["probe"] == "dns"
    assert result["ok"] is False
    assert "error" in result
