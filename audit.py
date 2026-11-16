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

# Pricing for Gemini 3.5 Flash Lite (per 1,000,000 tokens)
PRICE_INPUT_PER_MILLION = 0.075
PRICE_OUTPUT_PER_MILLION = 0.30


def _ensure_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def calculate_cost(prompt_tokens: int, output_tokens: int) -> float:
    """Calculate USD cost based on prompt and candidate token counts."""
    cost = (
        prompt_tokens * PRICE_INPUT_PER_MILLION
        + output_tokens * PRICE_OUTPUT_PER_MILLION
    ) / 1_000_000
    return round(cost, 8)


def log_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Append a structured JSON record to the audit ledger."""
    _ensure_dir()
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()

    line = json.dumps(entry, ensure_ascii=False)
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return entry


def log_ask_request(
    *,
    question: str,
    outcome: dict[str, Any],
    duration_ms: float,
    prompt_tokens: int = 0,
    output_tokens: int = 0,
    status_code: int = 200,
) -> dict[str, Any]:
    """Record an answered or refused /ask query."""
    answer = outcome.get("answer") or ""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": "/ask",
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "input": {
            "question": question,
            "corpus": outcome.get("corpus") or config.CORPUS,
        },
        "output": {
            "refused": outcome.get("refused", False),
            "best_distance": outcome.get("best_distance"),
            "threshold": outcome.get("threshold"),
            "sources": outcome.get("sources", []),
            "answer_length": len(answer),
            "answer_preview": (answer[:120] + "...") if len(answer) > 120 else answer,
        },
        "tokens": {
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "total_tokens": prompt_tokens + output_tokens,
        },
        "cost_usd": calculate_cost(prompt_tokens, output_tokens),
    }
    return log_entry(entry)


def log_rejection(
    *,
    endpoint: str = "/ask",
    input_payload: Any,
    reason: str,
    duration_ms: float,
    status_code: int = 400,
) -> dict[str, Any]:
    """Record a rejected or invalid request (400 Bad Request)."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "input": input_payload,
        "output": {
            "error": "bad_request",
            "reason": reason,
        },
        "tokens": {
            "prompt_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        },
        "cost_usd": 0.0,
    }
    return log_entry(entry)


def log_health(
    *,
    health_data: dict[str, Any],
    duration_ms: float,
    status_code: int = 200,
) -> dict[str, Any]:
    """Record a health check request."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": "/health",
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "input": {},
        "output": health_data,
        "tokens": {
            "prompt_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        },
        "cost_usd": 0.0,
    }
    return log_entry(entry)


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
