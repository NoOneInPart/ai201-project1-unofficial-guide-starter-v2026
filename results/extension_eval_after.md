# Extension Evaluation Results — After

**Date:** 2026-11-16T03:36:03.086562+00:00
**Corpus:** `campus_life`
**Model:** `gemini-3.5-flash-lite`

## Run Log — After

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Structured Log Schema Completeness | 100% | 13 of 13 | 13 of 13 | 13 of 13 | MET |
| 2. Health & Readiness Probe Latency | 1 of 1 (<100ms) | 1 of 1 | 1 of 1 | 1 of 1 | MET |
| 3. Bad-Path Rejection & Audit Trace | 2 of 2 (<10ms) | 2 of 2 | 2 of 2 | 2 of 2 | MET |
| 4. Gate Refusal Short-Circuit & Zero Spend | 4 of 5 (0 cost) | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 5. Token & Latency Instrumentation | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |

## Real Output by Criterion (Run 1 Examples)

#### 1. Structured Log Schema Completeness
- **Produced by:** `audit.py::log_ask_request` via `serve.py::ask`
- **Real log entry example:**
```json
{"timestamp": "2026-11-16T03:35:45.449079+00:00", "endpoint": "/health", "status_code": 200, "duration_ms": 51.74, "input": {}, "output": {"ok": true, "status": "healthy", "service": "unofficial-guide", "corpus": "campus_life", "index_ready": true, "indexed_chunks": 183, "model": "gemini-3.5-flash-lite", "embedding_model": "all-MiniLM-L6-v2", "threshold": 0.6, "top_k": 5, "log_entries": 53, "detail": "ready"}, "tokens": {"prompt_tokens": 0, "output_tokens": 0, "total_tokens": 0}, "cost_usd": 0.0}
```

#### 2. Health & Readiness Probe Latency
- **Produced by:** `serve.py::health`
- **Run 1 Latency:** `51.74 ms` (Target: `< 100 ms`)
- **Real response:**
```json
{"corpus": "campus_life", "detail": "ready", "embedding_model": "all-MiniLM-L6-v2", "index_ready": true, "indexed_chunks": 183, "log_entries": 53, "model": "gemini-3.5-flash-lite", "ok": true, "service": "unofficial-guide", "status": "healthy", "threshold": 0.6, "top_k": 5}
```

#### 3. Bad-Path Rejection & Audit Trace
- **Produced by:** `serve.py::ask` validation & `audit.py::log_rejection`
- **Real rejection samples:**
- Payload: `{'question': '   '}` -> HTTP `400`, error: `bad_request`, latency: `0.06 ms`
- Payload: `['non', 'dict', 'payload']` -> HTTP `400`, error: `bad_request`, latency: `0.06 ms`

#### 4. Gate Refusal Short-Circuit & Zero Spend
- **Produced by:** `gate.py::check` via `serve.py::ask`
- **Real refusal samples table:**
| Question | Best Distance | Refused | Total Tokens | Cost (USD) |
|---|---|---|---|---|
| What is the capital of Mongolia? | 0.8246 | True | 0 | $0.000000 |
| How do I change the oil in a diesel engine? | 0.9340 | True | 0 | $0.000000 |
| Who won the 1994 World Cup? | 0.8859 | True | 0 | $0.000000 |
| What is the recommended dosage of ibuprofen for a headache? | 0.7985 | True | 0 | $0.000000 |
| How do I write a for loop in Rust? | 0.8907 | True | 0 | $0.000000 |

#### 5. Token & Latency Instrumentation for Answered Queries
- **Produced by:** `generate.py::generate` & `audit.py::log_ask_request`
- **Real answered query sample (Question 1):**
- **Question:** How do grade appeals work?
- **Latency:** `1921.92 ms`
- **Tokens:** `{'output_tokens': 49, 'prompt_tokens': 490, 'total_tokens': 539}`
- **Cost:** `$0.000051`
- **Answer Preview:** A grade appeal must start with the instructor and be raised within fifteen days ...