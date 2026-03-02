"""Helpers for live MCP artifact naming and ownership checks."""

from __future__ import annotations

from datetime import datetime, timezone


def build_artifact_name(prefix: str, suffix: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{prefix}{suffix}-{timestamp}"


def is_owned_test_artifact(name: str, prefix: str) -> bool:
    return name.startswith(prefix)
