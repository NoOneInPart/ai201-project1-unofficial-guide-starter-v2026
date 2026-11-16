#!/usr/bin/env python3
"""
Measurement script to benchmark 10 runs of /ask.

Measures:
  - Latency (seconds of compute)
  - Real prompt and output tokens from Gemini API
  - Exact measured cost per run and average across 10 runs

Also exercises failed runs (rejections & gate refusal) and generates
the Markdown sections for README.md.
"""

from __future__ import annotations

import json
import time

import audit
from serve import app

TEST_QUESTIONS = [
    "How do grade appeals work?",
    "What's the difference between withdrawal and dropping?",
    "What is the workload for CS 210?",
    "What's the dining atrium like?",
    "Where do I get textbooks?",
    "How do grade appeals work?",
    "What's the difference between withdrawal and dropping?",
    "What is the workload for CS 210?",
    "What's the dining atrium like?",
    "Where do I get textbooks?",
]


def run_benchmark():
    app.testing = True
    client = app.test_client()

    print("Clearing previous audit log for a clean benchmark session...")
    audit.clear_entries()

    # 1. Warm-up health check
    print("Running health check...")
    client.get("/health")

    # 2. Run 10 uncached queries to measure real API tokens & compute
    print("\nRunning 10 queries (cache=False for real API token & latency measurement)...")
    runs = []

    for i, q in enumerate(TEST_QUESTIONS, start=1):
        print(f"  [{i}/10] Asking: {q}...")
        resp = client.post(
            "/ask",
            data=json.dumps({"question": q, "cache": False}),
            content_type="application/json",
        )
        assert resp.status_code == 200, f"Query failed: {resp.get_data(as_text=True)}"
        data = resp.get_json()
        duration_s = data["duration_ms"] / 1000.0
        tokens = data["tokens"]
        cost = data["cost_usd"]
        runs.append({
            "run": i,
            "question": q,
            "duration_s": duration_s,
            "prompt_tokens": tokens["prompt_tokens"],
            "output_tokens": tokens["output_tokens"],
            "total_tokens": tokens["total_tokens"],
            "cost_usd": cost,
            "sources": data["sources"],
        })
        time.sleep(0.5)  # brief pacing

    # 3. Exercise failure and refusal paths
    print("\nExercising failure and refusal paths...")
    # Out of scope gate refusal
    client.post(
        "/ask",
        data=json.dumps({"question": "What is the capital of Mongolia?", "cache": False}),
        content_type="application/json",
    )
    # 400 Bad Request - empty question
    client.post(
        "/ask",
        data=json.dumps({"question": "   "}),
        content_type="application/json",
    )
    # 400 Bad Request - non-dict payload
    client.post(
        "/ask",
        data=json.dumps(["invalid", "payload"]),
        content_type="application/json",
    )

    # 4. Compute Averages
    n = len(runs)
    avg_duration = sum(r["duration_s"] for r in runs) / n
    avg_prompt = sum(r["prompt_tokens"] for r in runs) / n
    avg_output = sum(r["output_tokens"] for r in runs) / n
    avg_total = sum(r["total_tokens"] for r in runs) / n
    avg_cost = sum(r["cost_usd"] for r in runs) / n

    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS (10 RUNS)")
    print("=" * 80)
    print(f"Average Compute Duration: {avg_duration:.3f} s  ({avg_duration*1000:.1f} ms)")
    print(f"Average Prompt Tokens:    {avg_prompt:.1f}")
    print(f"Average Output Tokens:    {avg_output:.1f}")
    print(f"Average Total Tokens:     {avg_total:.1f}")
    print(f"Average Cost per Run:     ${avg_cost:.6f} USD")
    print("=" * 80)

    # Print log entries count
    entries = audit.read_entries()
    print(f"\nTotal audit log entries recorded in logs/audit.jsonl: {len(entries)}")

    # Return structured report
    return {
        "runs": runs,
        "avg_duration": avg_duration,
        "avg_prompt": avg_prompt,
        "avg_output": avg_output,
        "avg_total": avg_total,
        "avg_cost": avg_cost,
        "entries": entries,
    }


if __name__ == "__main__":
    run_benchmark()
