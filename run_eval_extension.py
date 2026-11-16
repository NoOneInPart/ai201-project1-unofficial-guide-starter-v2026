#!/usr/bin/env python3
"""
Evaluation harness for Shape A Extension Criteria.

Runs 3 distinct evaluation trials testing all 5 acceptance criteria:
  1. Structured Log Schema Completeness (100% of requests have 7 required keys)
  2. Health & Readiness Probe Latency (HTTP 200, duration_ms < 100, indexed_chunks > 0)
  3. Bad-Path Rejection & Audit Trace (HTTP 400, duration_ms < 10, error: bad_request)
  4. Gate Refusal Short-Circuit & Zero Spend (refused: true, distance >= 0.6, tokens == 0, cost == 0.0)
  5. Token & Latency Instrumentation (duration_ms > 0, prompt/output tokens > 0, cost > 0)

Usage:
    python run_eval_extension.py --label before
    python run_eval_extension.py --label after
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import audit
import config
from questions import QUESTIONS, OUT_OF_SCOPE
from serve import app

REQUIRED_KEYS = {
    "timestamp",
    "endpoint",
    "status_code",
    "duration_ms",
    "input",
    "output",
    "tokens",
}


def run_one_trial(client, trial_num: int) -> dict[str, Any]:
    print(f"\n--- Running Trial {trial_num} ---")
    trial_start_idx = len(audit.read_entries())

    # --- Test 1: Health Probe (Criterion 2) ---
    health_resp = client.get("/health")
    health_status = health_resp.status_code
    health_data = health_resp.get_json() or {}
    health_duration = health_data.get("duration_ms")
    # if duration_ms wasn't directly in response body, check last audit log entry
    if health_duration is None:
        last_entry = audit.read_entries(limit=1)[0]
        health_duration = last_entry.get("duration_ms", 999.0)

    c2_passed = (
        health_status == 200
        and health_data.get("ok") is True
        and health_data.get("index_ready") is True
        and health_data.get("indexed_chunks", 0) > 0
        and health_duration < 100.0
    )
    c2_result = 1 if c2_passed else 0

    # --- Test 2: In-Corpus Answered Queries (Criterion 5) ---
    c5_passed_count = 0
    in_corpus_samples = []
    for item in QUESTIONS:
        q = item["question"]
        resp = client.post(
            "/ask",
            data=json.dumps({"question": q, "cache": False}),
            content_type="application/json",
        )
        data = resp.get_json() or {}
        tokens = data.get("tokens") or {}
        duration = data.get("duration_ms", 0.0)
        p_tok = tokens.get("prompt_tokens", 0)
        o_tok = tokens.get("output_tokens", 0)
        cost = data.get("cost_usd", 0.0)

        passed = (
            resp.status_code == 200
            and data.get("refused") is False
            and duration > 0.0
            and p_tok > 0
            and o_tok > 0
            and cost > 0.0
        )
        if passed:
            c5_passed_count += 1
        in_corpus_samples.append({
            "question": q,
            "status": resp.status_code,
            "refused": data.get("refused"),
            "duration_ms": duration,
            "tokens": tokens,
            "cost_usd": cost,
            "answer_preview": (data.get("answer", "")[:80] + "..."),
        })

    # --- Test 3: Out-of-Scope Queries (Criterion 4) ---
    c4_passed_count = 0
    out_of_scope_samples = []
    for q in OUT_OF_SCOPE:
        resp = client.post(
            "/ask",
            data=json.dumps({"question": q, "cache": False}),
            content_type="application/json",
        )
        data = resp.get_json() or {}
        tokens = data.get("tokens") or {}
        dist = data.get("best_distance", 0.0)
        tot_tok = tokens.get("total_tokens", 0)
        cost = data.get("cost_usd", 0.0)

        passed = (
            resp.status_code == 200
            and data.get("refused") is True
            and dist >= 0.6
            and tot_tok == 0
            and cost == 0.0
        )
        if passed:
            c4_passed_count += 1
        out_of_scope_samples.append({
            "question": q,
            "status": resp.status_code,
            "refused": data.get("refused"),
            "best_distance": dist,
            "total_tokens": tot_tok,
            "cost_usd": cost,
        })

    # --- Test 4: Bad Input Rejections (Criterion 3) ---
    bad_payloads = [
        {"question": "   "},
        ["non", "dict", "payload"],
    ]
    c3_passed_count = 0
    bad_input_samples = []
    for payload in bad_payloads:
        resp = client.post(
            "/ask",
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = resp.get_json() or {}
        # get rejection audit log entry
        recent_log = audit.read_entries(limit=1)[0]
        duration = recent_log.get("duration_ms", 999.0)
        err = data.get("error")

        passed = (
            resp.status_code == 400
            and err == "bad_request"
            and duration < 10.0
        )
        if passed:
            c3_passed_count += 1
        bad_input_samples.append({
            "payload": payload,
            "status": resp.status_code,
            "error": err,
            "duration_ms": duration,
        })

    # --- Test 5: Structured Log Schema Completeness (Criterion 1) ---
    all_entries = audit.read_entries()
    trial_entries = all_entries[trial_start_idx:]
    total_reqs = len(trial_entries)
    valid_entries_count = 0
    for entry in trial_entries:
        if REQUIRED_KEYS.issubset(entry.keys()):
            valid_entries_count += 1

    c1_score_str = f"{valid_entries_count} of {total_reqs}"
    c2_score_str = f"{c2_result} of 1"
    c3_score_str = f"{c3_passed_count} of 2"
    c4_score_str = f"{c4_passed_count} of 5"
    c5_score_str = f"{c5_passed_count} of 5"

    return {
        "trial": trial_num,
        "c1": (valid_entries_count, total_reqs, c1_score_str),
        "c2": (c2_result, 1, c2_score_str, health_duration, health_data),
        "c3": (c3_passed_count, 2, c3_score_str, bad_input_samples),
        "c4": (c4_passed_count, 5, c4_score_str, out_of_scope_samples),
        "c5": (c5_passed_count, 5, c5_score_str, in_corpus_samples),
        "sample_log_entry": trial_entries[0] if trial_entries else {},
    }


def main():
    parser = argparse.ArgumentParser(description="Run 3 evaluation trials for Extension Criteria.")
    parser.add_argument("--label", default="before", choices=["before", "after"])
    args = parser.parse_args()

    app.testing = True
    client = app.test_client()

    print(f"=== Starting Extension Evaluation Runs (Label: {args.label}) ===")

    trials = []
    for trial_idx in range(1, 4):
        trial_data = run_one_trial(client, trial_idx)
        trials.append(trial_data)
        time.sleep(1.0)

    # Compile Verdicts
    # C1: Target 100% (all reqs)
    c1_runs = [t["c1"][2] for t in trials]
    c1_met = all(t["c1"][0] == t["c1"][1] for t in trials)

    # C2: Target 1 of 1 (<100ms)
    c2_runs = [t["c2"][2] for t in trials]
    c2_met = all(t["c2"][0] == 1 for t in trials)

    # C3: Target 2 of 2 (<10ms)
    c3_runs = [t["c3"][2] for t in trials]
    c3_met = all(t["c3"][0] == 2 for t in trials)

    # C4: Target at least 4 of 5
    c4_runs = [t["c4"][2] for t in trials]
    c4_met = all(t["c4"][0] >= 4 for t in trials)

    # C5: Target 5 of 5
    c5_runs = [t["c5"][2] for t in trials]
    c5_met = all(t["c5"][0] == 5 for t in trials)

    table_rows = [
        ("1. Structured Log Schema Completeness", "100%", c1_runs[0], c1_runs[1], c1_runs[2], "MET" if c1_met else "MISSED"),
        ("2. Health & Readiness Probe Latency", "1 of 1 (<100ms)", c2_runs[0], c2_runs[1], c2_runs[2], "MET" if c2_met else "MISSED"),
        ("3. Bad-Path Rejection & Audit Trace", "2 of 2 (<10ms)", c3_runs[0], c3_runs[1], c3_runs[2], "MET" if c3_met else "MISSED"),
        ("4. Gate Refusal Short-Circuit & Zero Spend", "4 of 5 (0 cost)", c4_runs[0], c4_runs[1], c4_runs[2], "MET" if c4_met else "MISSED"),
        ("5. Token & Latency Instrumentation", "5 of 5", c5_runs[0], c5_runs[1], c5_runs[2], "MET" if c5_met else "MISSED"),
    ]

    print("\n" + "=" * 80)
    print(f"RUN LOG — {args.label.upper()}")
    print("=" * 80)
    print(f"{'Criterion':<42} | {'Target':<14} | {'Run 1':<8} | {'Run 2':<8} | {'Run 3':<8} | {'Verdict'}")
    print("-" * 96)
    for crit, target, r1, r2, r3, verdict in table_rows:
        print(f"{crit:<42} | {target:<14} | {r1:<8} | {r2:<8} | {r3:<8} | {verdict}")
    print("=" * 80 + "\n")

    # Generate Markdown Output File in results/
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = config.RESULTS_DIR / f"extension_eval_{args.label}.md"

    md_lines = [
        f"# Extension Evaluation Results — {args.label.title()}",
        f"",
        f"**Date:** {datetime.now(timezone.utc).isoformat()}",
        f"**Corpus:** `{config.CORPUS}`",
        f"**Model:** `{config.MODEL}`",
        f"",
        f"## Run Log — {args.label.title()}",
        f"",
        f"| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |",
        f"|---|---|---|---|---|---|",
    ]
    for crit, target, r1, r2, r3, verdict in table_rows:
        md_lines.append(f"| {crit} | {target} | {r1} | {r2} | {r3} | {verdict} |")

    md_lines.append("\n## Real Output by Criterion (Run 1 Examples)\n")

    # C1 Sample
    md_lines.append("#### 1. Structured Log Schema Completeness")
    md_lines.append("- **Produced by:** `audit.py::log_ask_request` via `serve.py::ask`")
    md_lines.append("- **Real log entry example:**")
    md_lines.append("```json")
    md_lines.append(json.dumps(trials[0]["sample_log_entry"]))
    md_lines.append("```")

    # C2 Sample
    md_lines.append("\n#### 2. Health & Readiness Probe Latency")
    md_lines.append("- **Produced by:** `serve.py::health`")
    md_lines.append(f"- **Run 1 Latency:** `{trials[0]['c2'][3]:.2f} ms` (Target: `< 100 ms`)")
    md_lines.append("- **Real response:**")
    md_lines.append("```json")
    md_lines.append(json.dumps(trials[0]["c2"][4]))
    md_lines.append("```")

    # C3 Sample
    md_lines.append("\n#### 3. Bad-Path Rejection & Audit Trace")
    md_lines.append("- **Produced by:** `serve.py::ask` validation & `audit.py::log_rejection`")
    md_lines.append("- **Real rejection samples:**")
    for b_samp in trials[0]["c3"][3]:
        md_lines.append(f"- Payload: `{b_samp['payload']}` -> HTTP `{b_samp['status']}`, error: `{b_samp['error']}`, latency: `{b_samp['duration_ms']:.2f} ms`")

    # C4 Sample
    md_lines.append("\n#### 4. Gate Refusal Short-Circuit & Zero Spend")
    md_lines.append("- **Produced by:** `gate.py::check` via `serve.py::ask`")
    md_lines.append("- **Real refusal samples table:**")
    md_lines.append("| Question | Best Distance | Refused | Total Tokens | Cost (USD) |")
    md_lines.append("|---|---|---|---|---|")
    for o_samp in trials[0]["c4"][3]:
        md_lines.append(f"| {o_samp['question']} | {o_samp['best_distance']:.4f} | {o_samp['refused']} | {o_samp['total_tokens']} | ${o_samp['cost_usd']:.6f} |")

    # C5 Sample
    md_lines.append("\n#### 5. Token & Latency Instrumentation for Answered Queries")
    md_lines.append("- **Produced by:** `generate.py::generate` & `audit.py::log_ask_request`")
    md_lines.append("- **Real answered query sample (Question 1):**")
    samp_q = trials[0]["c5"][3][0]
    md_lines.append(f"- **Question:** {samp_q['question']}")
    md_lines.append(f"- **Latency:** `{samp_q['duration_ms']:.2f} ms`")
    md_lines.append(f"- **Tokens:** `{samp_q['tokens']}`")
    md_lines.append(f"- **Cost:** `${samp_q['cost_usd']:.6f}`")
    md_lines.append(f"- **Answer Preview:** {samp_q['answer_preview']}")

    out_file.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Results and real outputs saved to {out_file}")


if __name__ == "__main__":
    main()
