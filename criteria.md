# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
<!-- e.g. "One of my questions is about a topic only two documents mention, so
     I expect that one to be hard." -->
The questions are pulled directly from the corpus and aren't too hard, so
getting 4 out of 5 right means the project is heading in the right direction
and may simply need more tuning.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
<!-- Why all five and not four? What about your setup makes that achievable —
     or what would have to go wrong for it not to be? -->
The system must not try and invent information, everything must be sourced.

**Revised in Unit 2:** 
Since source attribution is required by the system prompt, 5 out of 5 is an
achievable score and any less than 5 would mean that the model failed to follow
the prompt and hallucinated information.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:**
<!-- What did your distances look like when you set the cutoff in Milestone 4?
     Was there a clean gap, or did the two groups overlap? -->
This prevents the system from returning irrelevant information if the requested
question is not covered in the corpus. Allowing 1 miss for every 5 tries
provides some tuning leeway to either answer more questions at the expense of
possibly using the wrong sources, or only allowing it to answer questions it is
completely confident in, even if it might have been able to answer a question
based on info in the corpus that was not presented in a straightforward manner.

---

## 4. Something about your chunks

<!-- YOU WRITE THIS ONE.

     How would you know if your chunks were the right size? Name something
     countable or observable.

     Examples of the right shape — don't copy these, they should come from
     what you actually saw in Milestone 3:
       - "At least 4 of 5 sampled chunks read as a complete thought, with no
          sentence cut in half at either end."
       - "No chunk is shorter than 200 characters, since anything below that
          in my corpus turned out to be a heading with no content under it." -->
The chunker should return one line from the documentation, with one
sentence of overlap before and after each chunk.

**Revised in unit 2:** 
For at least 4 of 5 test questions, every retrieved chunk reads as a complete 
thought, with no sentences cut off mid-sentence at either chunk boundary.

**Why revised:** 
The original stated the implementation mechanism in chunker.py rather than a 
measurable acceptance threshold. The revised version tests the actual intended 
outcome of sentence overlap (sentence boundary integrity) as a measurable 
pass/fail rate across retrieved chunks.

**Why this target:**
Judging by how info is formatted in the corpus, one relevent line of text
should provide enough information to answer a question without getting
out of context, with the overlap allowing for possibly some more relevant
context and to prevent incomplete thoughts.


---

## 5. Your choice

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. It could be about
     speed, about refusals, about a particular kind of question your corpus
     handles badly, about source attribution being correct rather than merely
     present — anything, as long as it names a number or an observable
     outcome. -->
The system will only return information provided in the corpus and does not
attempt to provide its own interpretation of the information or add on to it
for at least 4 out of 5 tries.

**Revised in unit 2:** 
For all 5 of 5 test questions across all runs, the system produces a correct, 
substantive answer matching the expected information (verified by scorer.py::judge), 
without refusing due to missing information.

**Why revised:** 
"Does not attempt to provide its own interpretation" is too subjective to 
evaluate consistently across runs. However, measuring the correctness of the
answer using scorer.py allows it to be objectively measured with a judging
implementation that checks if the expected text is in the generated answer
on top of using rapidfuzz to do fuzzy matching if there are minor differences
in wording.

**Why this target:**
Allowing the system to add to the information runs the risk of it providing
incorrect, hallucinated information. Allowing it to get 1 question out of 5
wrong allows the system to be able to answer some slightly more abstract
questions while ensuring it won't make up an answer for a question that is
completely out of the context of the corpus.

**Revised in unit 2:** 
Since all test questions are pulled from information available directly in the
corpus, the model should be able to form a conclusion to all the questions
that are available in the corpus as well. 



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->


---

# Extension Acceptance Criteria (Shape A: Deploy & Instrument)

Written in the Extension Unit **before** evaluation trials were conducted.

At least three criteria directly evaluate the new operational service layer (HTTP API, structured JSON logging, latency measurement, and token/cost instrumentation), with explicit coverage of the failure/bad-request path.

---

## 1. Structured Log Schema Completeness (Extension)

Every incoming HTTP request handled by the service (across `/ask`, `/health`, and rejected calls) writes a single JSON record to `logs/audit.jsonl` containing all seven required top-level keys: `timestamp`, `endpoint`, `status_code`, `duration_ms`, `input`, `output`, and `tokens`.

- **Target:** 100% of requests (15 of 15 across 3 evaluation runs) write a valid JSON entry with all 7 keys present.
- **Why this target:** In an operational deployment, any request that fails to log creates an unmonitored blind spot where errors or runaway API spend go undetected. Because schema construction happens deterministically in the server's response wrapper before returning to the client, 100% compliance is achievable and necessary. A looser target (e.g. 90%) would mean tolerating silent data loss in production audit trails.

---

## 2. Health & Readiness Probe Latency (Extension)

`GET /health` returns HTTP status code 200 with `"ok": true`, `"index_ready": true`, and an `indexed_chunks` integer count greater than 0, completing in under 100 milliseconds without calling the LLM.

- **Target:** 3 of 3 evaluation trials return HTTP 200 with `duration_ms < 100` and `indexed_chunks > 0`.
- **Why this target:** Container platforms and cloud load balancers probe health endpoints every few seconds. If `/health` exceeds 100 ms or inadvertently triggers embedding model downloads or LLM synthesis, it burns system memory and API quota simply checking if the container is alive. 100 ms guarantees the health check only queries Chroma's SQLite metadata table for index presence rather than executing deep neural inference.

---

## 3. Bad-Path Rejection & Audit Trace (Extension — Failure Path)

When sent malformed or invalid inputs (specifically an empty query `{"question": "   "}` and a non-dictionary JSON payload `["invalid"]`), `POST /ask` immediately rejects the request with HTTP status code 400 Bad Request, refuses to execute retrieval or generation, and writes an audit log entry with `"error": "bad_request"` in under 10 milliseconds.

- **Target:** 6 of 6 invalid test queries (3 runs of 2 bad payloads) return HTTP 400 and log the rejection with `duration_ms < 10`.
- **Why this target:** This is the bad path. Clients frequently send empty strings, mistyped keys, or non-object JSON payloads. If the service attempts retrieval or LLM generation on malformed input, it wastes API quota, risks 500 runtime crashes, and corrupts metrics. Enforcing a < 10 ms rejection verifies that input validation happens immediately at the routing boundary before vector search or LLM invocation.

---

## 4. Gate Refusal Short-Circuit & Zero Spend (Core + Extension)

When an out-of-corpus question is submitted to `POST /ask` (using the 5 standard `OUT_OF_SCOPE` queries), the relevance gate refuses the question, returning HTTP 200 with `"refused": true`, logging `best_distance >= 0.6`, and consuming exactly 0 generation tokens and $0.00 USD API spend.

- **Target:** At least 4 of 5 out-of-scope questions refused with `cost_usd == 0.0` across all 3 trials.
- **Why this target:** Grounding integrity requires refusing questions unsupported by the corpus so the LLM does not hallucinate. The operational requirement is that a refusal must cleanly short-circuit the pipeline: it must record the query and its distance for observability, but consume zero model generation tokens. Allowing 1 miss out of 5 accounts for edge cases where an out-of-corpus query might accidentally align closely with corpus terminology, while still strictly enforcing zero financial cost on all refused queries.

---

## 5. Token & Latency Instrumentation for Answered Queries (Extension)

For every successfully answered question through `POST /ask`, the response payload and corresponding audit log entry include measured end-to-end latency (`duration_ms > 0`), measured API token counts (`prompt_tokens > 0` and `output_tokens > 0`), and calculated cost in USD.

- **Target:** 5 of 5 in-corpus test questions across all 3 trials report non-zero duration, positive prompt and output token counts, and cost.
- **Why this target:** Operational observability requires tracking how much each answered question costs and how long it takes. Since generation calls Gemini, a non-zero token count verifies that token usage was captured from real API metadata rather than defaulting to null or zero. Missing these fields means operators cannot budget or bill for API usage.
