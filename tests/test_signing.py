"""Tests for cli/signing.py (ECDSA P-256 + RFC 7638 key id)."""
import json, tempfile
from cli.signing import sign_package, verify_package, load_or_generate


def test_generate_and_verify():
    package = {"test": 1, "nested": {"a": 2}}
    signed = sign_package(package)
    assert "signature" in signed
    assert signed.get("signature_scheme") == "ECDSA-P256-SHA256"
    assert signed.get("signer_kid", "").startswith("sha256:")
    assert verify_package(signed) is True


def test_tampered_package_fails():
    signed = sign_package({"x": 1})
    signed["x"] = 2  # tamper
    assert verify_package(signed) is False


def test_key_persistent():
    # Running a second time should reuse the same key (same kid prefix)
    signed1 = sign_package({"id": 1})
    signed2 = sign_package({"id": 2})
    assert signed1["signer_kid"] == signed2["signer_kid"]
