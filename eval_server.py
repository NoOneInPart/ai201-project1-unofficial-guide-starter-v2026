#!/usr/bin/env python3
"""
Test suite for The Unofficial Guide web service (serve.py).

Verifies the HTTP service layer:
  - GET  /health   (index status, metadata, diagnostic health)
  - GET  /log      (audit log retrieval)
  - POST /ask      (valid in-corpus questions, out-of-scope gate refusals)
  - POST /ask      (malformed input & 400 Bad Request error handling)

Usage:
    # Run against a running server:
    python eval_server.py --url http://127.0.0.1:5000

    # Run in-process using Flask's test client (no server needed):
    python eval_server.py
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class ClientAdapter:
    """Unified client that supports both live HTTP requests and Flask test_client."""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url.rstrip("/") if base_url else None
        self._test_client = None
        if not self.base_url:
            from serve import app

            app.testing = True
            self._test_client = app.test_client()

    def get(self, path: str, params: dict | None = None) -> tuple[int, dict[str, Any]]:
        if self.base_url:
            query = f"?{urllib.parse.urlencode(params)}" if params else ""
            req = urllib.request.Request(f"{self.base_url}{path}{query}", method="GET")
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.status, json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as err:
                try:
                    return err.code, json.loads(err.read().decode("utf-8"))
                except Exception:
                    return err.code, {}
        else:
            resp = self._test_client.get(path, query_string=params)
            return resp.status_code, resp.get_json(silent=True) or {}

    def post_json(self, path: str, data: Any) -> tuple[int, dict[str, Any]]:
        if self.base_url:
            payload = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}{path}",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return resp.status, json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as err:
                try:
                    return err.code, json.loads(err.read().decode("utf-8"))
                except Exception:
                    return err.code, {}
        else:
            resp = self._test_client.post(
                path,
                data=json.dumps(data),
                content_type="application/json",
            )
            return resp.status_code, resp.get_json(silent=True) or {}


def run_checks(client: ClientAdapter) -> bool:
    all_passed = True
    results = []

    def check(name: str, passed: bool, detail: str = ""):
        nonlocal all_passed
        if not passed:
            all_passed = False
        status = "PASS" if passed else "FAIL"
        results.append((status, name, detail))

    print("\n--- Running Service Verification Checks ---\n")

    # 1. Health check
    try:
        status, data = client.get("/health")
        passed = (
            status == 200
            and data.get("ok") is True
            and data.get("index_ready") is True
            and "corpus" in data
        )
        check(
            "GET /health responds healthy",
            passed,
            f"status={status}, corpus={data.get('corpus')}, chunks={data.get('indexed_chunks')}",
        )
    except Exception as exc:
        check("GET /health responds healthy", False, str(exc))

    # 2. Audit log endpoint
    try:
        status, data = client.get("/log", params={"limit": 5})
        passed = status == 200 and "count" in data and isinstance(data.get("entries"), list)
        check(
            "GET /log retrieves audit ledger",
            passed,
            f"status={status}, log_count={data.get('count')}",
        )
    except Exception as exc:
        check("GET /log retrieves audit ledger", False, str(exc))

    # 3. Valid question through /ask
    try:
        question = "How do grade appeals work?"
        status, data = client.post_json("/ask", {"question": question})
        passed = (
            status == 200
            and data.get("ok") is True
            and data.get("refused") is False
            and bool(data.get("answer"))
            and len(data.get("sources", [])) > 0
            and "duration_ms" in data
            and "tokens" in data
            and "cost_usd" in data
        )
        check(
            "POST /ask answers in-corpus question with metrics",
            passed,
            f"status={status}, duration_ms={data.get('duration_ms')}, tokens={data.get('tokens')}, cost=${data.get('cost_usd')}",
        )
    except Exception as exc:
        check("POST /ask answers in-corpus question with metrics", False, str(exc))

    # 4. Out-of-scope question gate refusal
    try:
        question = "What is the capital of Mongolia?"
        status, data = client.post_json("/ask", {"question": question})
        passed = status == 200 and data.get("refused") is True
        check(
            "POST /ask gate refuses out-of-corpus question",
            passed,
            f"status={status}, refused={data.get('refused')}, best_distance={data.get('best_distance')}",
        )
    except Exception as exc:
        check("POST /ask gate refuses out-of-corpus question", False, str(exc))

    # 5. Bad Request on empty question
    try:
        status, data = client.post_json("/ask", {"question": "   "})
        passed = status == 400 and data.get("error") == "bad_request"
        check(
            "POST /ask rejects empty question (400 Bad Request)",
            passed,
            f"status={status}, message={data.get('message')}",
        )
    except Exception as exc:
        check("POST /ask rejects empty question (400 Bad Request)", False, str(exc))

    # 6. Bad Request on non-dictionary payload
    try:
        status, data = client.post_json("/ask", ["not", "a", "dict"])
        passed = status == 400 and data.get("error") == "bad_request"
        check(
            "POST /ask rejects non-dict payload (400 Bad Request)",
            passed,
            f"status={status}, message={data.get('message')}",
        )
    except Exception as exc:
        check("POST /ask rejects non-dict payload (400 Bad Request)", False, str(exc))

    # Report results table
    print(f"{'Status':<8} {'Check':<45} {'Details'}")
    print("-" * 80)
    for res_status, name, detail in results:
        print(f"[{res_status}]   {name:<45} {detail}")

    print("\n" + ("=" * 80))
    if all_passed:
        print("ALL SERVICE CHECKS PASSED.")
    else:
        print("SOME SERVICE CHECKS FAILED.")
    print("=" * 80 + "\n")

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Verify The Unofficial Guide web service.")
    parser.add_argument(
        "--url",
        help="Base URL of running server, e.g. http://127.0.0.1:5000. If omitted, uses Flask test_client.",
    )
    args = parser.parse_args()

    client = ClientAdapter(base_url=args.url)
    success = run_checks(client)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
