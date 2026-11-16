#!/usr/bin/env python3
"""
The Unofficial Guide — the same pipeline, over HTTP.

    python serve.py                          run it locally on port 5000
    gunicorn serve:app                       run it the way a host runs it

Nothing new happens in this file. It is a wrapper: a request comes in, it
hands the question to `app.py::ask_pipeline` — the exact function the command
line uses — and hands the answer back as JSON. Retrieval, the relevance gate
and the grounded prompt all still live where they lived. If you change how
your system answers, you change it in those files and this one follows.

Two routes:

    POST /ask       {"question": "..."} in, the answer and its sources out
    GET  /health    is the service up, and is there an index to search

Why this exists: `app.py` runs once and exits, which is fine on your laptop
and impossible to deploy. A hosted service has to stay up and wait for
requests. This is the smallest thing that does that.

⚠️ There is deliberately no logging, no timing and no metrics in this file.
Unit 9 has you build the structured log yourself — the request line, the
timing field everyone skips, the whole instrument-before-you-deploy exercise.
Shipping a logger here would hand you the answer to that. Add yours in unit 9;
this file stays the bare shell until then.
"""

import os

from flask import Flask, jsonify, request

import config

app = Flask(__name__)


@app.get("/health")
def health():
    """Is the service up, and is there an index to search?

    Modeled after production health checks:
    - Verifies vector index presence without loading heavy embedding weights.
    - Exposes operational configuration (corpus, chunk count, model, gate threshold).
    - Returns HTTP 200 when ready, HTTP 503 when the index is missing.
    """
    from store import index_exists, _client

    ready = index_exists(config.CORPUS)
    chunk_count = 0
    if ready:
        try:
            coll = _client().get_collection(config.collection_name(config.CORPUS))
            chunk_count = coll.count()
        except Exception:
            chunk_count = 0

    body = {
        "ok": ready,
        "status": "healthy" if ready else "degraded",
        "service": "unofficial-guide",
        "corpus": config.CORPUS,
        "index_ready": ready,
        "indexed_chunks": chunk_count,
        "model": config.MODEL,
        "embedding_model": config.EMBEDDING_MODEL,
        "threshold": config.THRESHOLD,
        "top_k": config.TOP_K,
        "detail": (
            "ready"
            if ready
            else "no index for this corpus — run `python app.py index`"
        ),
    }
    status_code = 200 if ready else 503
    return jsonify(body), status_code


@app.post("/ask")
def ask():
    """One question in, one grounded answer out.

    A refused question is a 200, not an error. The gate refusing is your
    system working — it is an answer, and the JSON says so with
    `"refused": true` so whatever calls this can tell the two apart.
    """
    from app import ask_pipeline

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return (
            jsonify(
                {
                    "error": "bad_request",
                    "message": "Expected a JSON object.",
                }
            ),
            400,
        )

    question = payload.get("question")
    if not isinstance(question, str) or not question.strip():
        return (
            jsonify(
                {
                    "error": "bad_request",
                    "message": "Field 'question' must be a non-empty string, e.g. "
                    '{"question": "is the housing lottery random?"}',
                }
            ),
            400,
        )

    question = question.strip()

    # Guard against oversized questions
    if len(question.split()) >= 1000:
        return (
            jsonify(
                {
                    "error": "bad_request",
                    "message": "Question exceeds maximum allowed length (1,000 words).",
                }
            ),
            400,
        )

    try:
        outcome = ask_pipeline(question, corpus=config.CORPUS)
    except Exception as exc:  # noqa: BLE001 — a reader gets this, not a traceback
        return (
            jsonify(
                {
                    "error": "internal_server_error",
                    "message": f"{type(exc).__name__}: {exc}",
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "ok": True,
                "question": question,
                "answer": outcome["answer"],
                "refused": outcome["refused"],
                "sources": outcome["sources"],
                "best_distance": round(outcome["best_distance"], 4),
                "threshold": outcome["threshold"],
                "corpus": config.CORPUS,
            }
        ),
        200,
    )


def main():
    # Hosts tell you which port to listen on through PORT, and they expect you
    # on 0.0.0.0. Binding 127.0.0.1 instead works perfectly on your laptop and
    # then answers nothing at all once deployed, because the host's router
    # can't reach a socket that only accepts connections from inside the
    # container. It is the single most common way a first deploy "succeeds"
    # and is unreachable.
    port = int(os.getenv("PORT", "5000"))

    # Debug mode reloads on save, which is handy, and prints a console that
    # runs arbitrary code, which is not something to leave switched on where
    # strangers can reach it. Off unless you ask for it.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    print(f"Serving The Unofficial Guide on http://localhost:{port}")
    print(f"Corpus: {config.CORPUS}    (Ctrl-C to stop)\n")
    print("Try it from another terminal:\n")
    print(f"  curl http://localhost:{port}/health")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"question\": \"is the housing lottery random?\"}}'\n"
    )

    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
