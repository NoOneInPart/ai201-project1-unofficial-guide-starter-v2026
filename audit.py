"""Structured audit logger for The Unofficial Guide.

Records operational JSON lines to `logs/audit.jsonl` with timestamps,
request inputs, outputs, status, latency, and cost metadata.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config

LOG_DIR: Path = getattr(config, "LOG_DIR", config.ROOT / "logs")
AUDIT_LOG: Path = getattr(config, "AUDIT_LOG", LOG_DIR / "audit.jsonl")


def _ensure_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Append a structured JSON record to the audit ledger."""
    _ensure_dir()
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()

    line = json.dumps(entry, ensure_ascii=False)
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return entry


def read_entries(limit: int | None = None) -> list[dict[str, Any]]:
    """Read entries from the audit log, oldest first (or last `limit` entries)."""
    if not AUDIT_LOG.exists():
        return []

    entries: list[dict[str, Any]] = []
    with open(AUDIT_LOG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if limit is not None and limit > 0:
        return entries[-limit:]
    return entries


def clear_entries() -> None:
    """Reset the audit log file."""
    if AUDIT_LOG.exists():
        AUDIT_LOG.unlink()
