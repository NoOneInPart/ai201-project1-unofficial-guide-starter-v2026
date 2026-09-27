# The Unofficial Guide

<!-- Replace this line with your name and which corpus you picked. -->

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

<!-- Three or four sentences. Which corpus you picked, and the kinds of
     questions your system answers. Write it for someone who has never seen
     this repo.

     Milestone 5. -->
Given a corpus in `\corpora`, the below tests use the `campus_life` corpus, 
this system will split each document in the corpus into chunks by line, with
one sentence of overlap before and after, and index them. An embedding model
vectorizes each chunk, and for a given question, the system determines which
chunks are the most relevant by vector distance. The question, along with the
top-k (5) chunks from the corpus that pass below the distance threshold of 0.6,
are passed to an LLM to synthesize an answer from the provided information if
the question can reasonably be answered using the chunks from the corpus.

## Chunking Strategy

**Chunk size:** 1 line of text
**Overlap:** 1 sentence before and after each line

Judging based on how the corpus is formatted, one line should provide plenty
of context to answer a specific question, and adding a sentence of overlap
before and after prevents broken, incomplete thoughts while adding additional
provided information from the same source that may be prescient.

<!-- What about YOUR documents made you pick these numbers? Short posts and
     long sectioned guides don't want the same chunking, and "800 seemed
     reasonable" earns nothing. Point at something you noticed when you read
     the documents in Milestone 1.

     If you changed your mind partway through, say so and say why. That's worth
     more than pretending you got it right first time.

     Milestone 3. -->

## Sample Chunks

<!-- Five chunks, pasted as text. Label each one and name the file it came from
     AND the function that produced it — the grader checks your code against
     what you claim here.

     `python app.py chunks -n 5` prints all three for you. Copy them straight
     across.

     Milestone 3. -->

**Chunk 1** — source: `admin_add_drop_deadline.txt#0` — produced by: `chunker.py::split_documents`

```
On the add/drop deadline
You can add a course through the end of the second week.
```

**Chunk 2** — source: `course_cs_210_workload.txt#2` — produced by: `chunker.py::split_documents`

```
That's real time, not optimistic time.
It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.
```

**Chunk 3** — source: `course_phys_130.txt#3` — produced by: `chunker.py::split_documents`

```
Expect 7 hours a week, plus 3 on lab weeks.
The one piece of advice: the lab practical is worth 20% and almost nobody prepares for it.
```

**Chunk 4** — source: `dining_verrill_street_grill.txt#1` — produced by: `chunker.py::split_documents`

```
Verrill Street Grill
I'm a junior and I've done this twice now. Wait times: up to 30 minutes on Friday evenings, otherwise under 10. The thing worth going for is the burger, which is the only late-night hot food on campus. The thing to know is that one register, so the queue is a single line no matter how busy.
Hours are 11:00am to 1:00am daily during term.
```

**Chunk 5** — source: `housing_morrow_house.txt#2` — produced by: `chunker.py::split_documents`

```
Rooms are singles and doubles, hall bathrooms.
The good: cheapest housing tier by about $900 a year, and the singles are real singles.
The bad: known damp problem on the ground floor; two rooms were taken offline in 2024.
```

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:** "What is the dining atrium like?"

**Answer:**

```
  (best distance 0.453, cutoff 0.6)

Based on the provided documents, there is no queue if you go before 11:45 to eat between classes, but the food is picked clean by 1:15 and not restocked until the next morning (*dining_the_atrium_followup.txt*).

Sources retrieved: dining_pellew_dining_hall.txt, dining_the_atrium_followup.txt, housing_calder_annexe.txt, housing_fenwick_court.txt

1 model calls this session, 467 tokens (408 in, 59 out)
```

**My relevance cutoff:** 0.6
Based on my testing, my most abstract question from the corpus about the dining
atrium correctly retrieved student reviews about the Atrium at a distance of
0.5196, but also pulled less relevant sources about housing at a distance of
0.5129. The lowest distance of an out-of-corpus question was way
higher at 0.7903 when asking it about the capital of Mongolia. Thus, I decided
that the default cutoff of 0.6 worked for my setup as it ensures slightly more
difficult questions can be answered from the corpus while still easily 
filtering out sources for irrelevant questions.
Note: the best distance for the Atrium question returned 0.453, but checking
retrieve revealed that corresponding source to be about Pellew Dining Hall.
The most relevant source about the Atrium was the last one that appeared at a
distance of 0.5196 when analyzing the assembled prompt.

<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here — the table below wants all ten rows.

     Milestone 4. -->

| Question | In corpus? | Best distance |
|---|---|---|
| How do grade appeals work? | Yes | 0.2385 |
| What's the difference between withdrawal and dropping? | Yes | 0.3034 |
| What is the workload for CS 210? | Yes | 0.3092 |
| What is the dining atrium like? | Yes | 0.4531 |
| Where do I get textbooks? | Yes | 0.3262 |
| What is the capital of Mongolia? | No | 0.7903 |
| How do I change the oil in a diesel engine? | No | 0.8677 |
| Who won the 1994 World Cup? | No | 0.8270 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.7985 |
| How do I write a for loop in Rust? | No | 0.8312 |

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1.** I asked Gemini to write a new chunking function based on a simple
explanation of wanting it done by line with one sentence of overlap, but I had
the effort set to High and it went on a wild goose chase of trying to learn
everything about the repository. I stopped it in its tracks, turned the effort
down to Medium, and asked it again, but more explicitly about how I just want
a chunker that returns each line of the corpus, with an extra sentence from the
lines before and after when available to ensure there are no incomplete
thoughts in the chunk, and it finally got it done quickly.

**2.** In Unit 2, I asked Gemini to fill in the run logs in this README for me 
as I trusted it more to fill them in correctly without error based on the logs 
in /results compared to me doing it manually. I had discussions about the 
criteria in the chat context so I knew that it had an understanding of the 
criteria that aligned with how I viewed them. I checked the results and they 
matched up. I filled out the reasoning parts myself though.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 4 of 5 | 4 of 5 | 4 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 4. Retrieved chunks are complete thoughts | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 5. System answers in-corpus test questions correctly | 5 of 5 | 4 of 5 | 4 of 5 | 4 of 5 | MISSED |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

#### 1. Retrieved chunk contains the answer
- **Produced by:** `store.py::search` / `run_eval.py::main`
- **Result:** 4 of 5 questions retrieved a chunk containing the expected answer across all runs. Question 4 ("What's the dining atrium like?") failed because retrieval pulled `dining_the_atrium_followup.txt` instead of `dining_the_atrium.txt`, missing the expected answer ("no queue").
- **Real output example (Question 1, Run 1):**
  - Best distance: 0.2385 (passed gate)
  - Sources retrieved: `admin_grade_appeals.txt`, `admin_housing_lottery.txt`, `course_engl_205_exams.txt`, `course_stat_150_exams.txt`
  - Relevant retrieved chunk text from `admin_grade_appeals.txt`:
    ```
    A grade appeal must start with the instructor and be raised within fifteen days of the grade posting before it can go to the department. Skipping the instructor step will result in the appeal being returned.
    ```

#### 2. Every answer names a source
- **Produced by:** `generate.py::answer` via `run_eval.py::main`
- **Result:** 5 of 5 answers across all runs named at least one source file.
- **Real output example (Question 1, Run 1):**
  ```
  A grade appeal must start with the instructor and be raised within fifteen days of the grade posting before it can go to the department. Skipping the instructor step will result in the appeal being returned. 

  Source: admin_grade_appeals.txt
  ```
- **Real output example (Question 3, Run 1):**
  ```
  The workload for CS 210 Data Structures is 8 to 10 hours a week outside class, which is real time and front-loaded so the first month is heavier than the rest. (Source: `course_cs_210_workload.txt`)
  ```

#### 3. Gate stops out-of-corpus questions
- **Produced by:** `run_eval.py::check_out_of_scope` (cutoff: 0.6)
- **Result:** 5 of 5 out-of-scope questions were refused by the gate in one deterministic pass.
- **Real output table:**

| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.790 | refused |
| How do I change the oil in a diesel engine? | 0.868 | refused |
| Who won the 1994 World Cup? | 0.827 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.798 | refused |
| How do I write a for loop in Rust? | 0.831 | refused |

#### 4. Retrieved chunks are complete thoughts
- **Produced by:** `chunker.py::split_documents`
- **Result:** 5 of 5 questions had retrieved chunks that were complete thoughts, with clean sentence boundaries and no truncation due to sentence-aware chunking and overlap.
- **Real output chunk example (retrieved for Question 3, from `course_cs_210_workload.txt#2`):**
  ```
  That's real time, not optimistic time.
  It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.
  ```

#### 5. System answers in-corpus test questions correctly
- **Produced by:** `generate.py::answer` evaluated by `scorer.py::judge`
- **Result:** 4 of 5 across all three runs (**MISSED** against target of 5 of 5). Questions 1, 2, 3, and 5 passed the scorer in every run, but Question 4 ("What's the dining atrium like?") failed in all three runs because retrieval missed `dining_the_atrium.txt`, causing the model to return a refusal instead of the expected answer ("no queue").
- **Real output example (Question 4, Run 1 — Fail):**
  ```
  Based on the provided documents, there is not enough information to describe what The Atrium is like, other than someone adding to what others have said about it. 

  Source: dining_the_atrium_followup.txt
  ```

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer | MET | For 4 out of 5 questions on all 3 runs, the retrieved chunks contained the correct answer, which hits the target. |
| 2 | Every answer names a source | MET | For all 5 questions for all 3 runs, the generated answer correctly cited the source. |
| 3 | Gate stops out-of-corpus questions | MET | For all 5 out-of-corpus questions, the gate successfully discarded them for being out-of-corpus. |
| 4 | Retrieved chunks are complete thoughts | MET | For all 5 questions, all chunks returned are full sentences that are not cut off. |
| 5 | System answers in-corpus test questions correctly | MISSED | For 1 out of 5 questions, the system was unable to answer based on the returned information, which is below the target of 5 of 5. |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

Criterion 5 was missed because, despite working once in Unit 1, in subsequent
runs the model believed it did not have enough information to answer the 
question: "What's the dining atrium like?" Analyzing the retrieval stage,
one chunk from a document was retrieved: a follow-up reply to a student post 
about The Atrium, however that specific chunk contained nothing but the first
line of the document, the title, and one sentence from the next line over which 
provided no useful information:
```
Re: The Atrium
Adding to what people have said about The Atrium.
```
There are two problems here, the chunker returns useless chunks containing just
the title line and one sentence of overlap, and the top-k gate (5) prevents 
the return of the actual chunk that has relevant information.

## The Improvement

**What I changed:** I decided to patch the chunker to not return useless chunks 
for the title line (line 0).

**Why I picked it:** This fixes two problems in the criterion 5 diagnosis. The 
chunker no longer returns a chunk for line 0 if it doesn't contain a sentence 
punctuation (i.e. if it is only a title), which removes the number of useless 
chunks filling up the index. This also reduces the amount of useless chunks 
returned in the retrieval stage, minimizing the issue of the top-k gate not 
being high enough to allow all relevant chunks to pass through.

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 4. Retrieved chunks are complete thoughts | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 5. System answers in-corpus test questions correctly | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |

### Real Output by Criterion (After)

#### 1. Retrieved chunk contains the answer
- **Produced by:** `store.py::search` / `run_eval.py::main`
- **Result:** 5 of 5 questions had retrieved chunks containing the expected answer across all runs. With title-only stubs removed, `dining_the_atrium_followup.txt` entered the top-5 (rank 4, distance 0.4906) and provided the answer for Question 4 ("What's the dining atrium like?").
- **Real output example (Question 4, Run 1):**
  - Best distance: 0.4906 (passed gate)
  - Sources retrieved: `dining_the_atrium_followup.txt`, `housing_aldridge_hall.txt`, `housing_calder_annexe.txt`, `housing_fenwick_court.txt`, `housing_tamsin_court.txt`

#### 2. Every answer names a source
- **Produced by:** `generate.py::answer` via `run_eval.py::main`
- **Result:** 5 of 5 answers across all runs named at least one source document.
- **Real output example (Question 4, Run 2):**
  ```
  Based on the provided documents, the wait time at The Atrium has no queue if you go before 11:45 to eat between classes. However, the food is picked clean by 1:15 and is not restocked again until the next morning. 

  Source: dining_the_atrium_followup.txt
  ```

#### 3. Gate stops out-of-corpus questions
- **Produced by:** `run_eval.py::check_out_of_scope` (cutoff: 0.6)
- **Result:** 5 of 5 out-of-scope questions were refused by the gate in one deterministic pass.
- **Real output table:**

| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.825 | refused |
| How do I change the oil in a diesel engine? | 0.934 | refused |
| Who won the 1994 World Cup? | 0.886 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.798 | refused |
| How do I write a for loop in Rust? | 0.891 | refused |

#### 4. Retrieved chunks are complete thoughts
- **Produced by:** `chunker.py::split_documents`
- **Result:** 5 of 5 questions had retrieved chunks that read as complete thoughts. Skipping title lines without sentence-ending punctuation eliminated hollow chunks, increasing the minimum chunk size across the corpus from 31 to 91 characters.
- **Real output chunk example (`dining_the_atrium_followup.txt#0`):**
  ```
  Re: The Atrium
  Adding to what people have said about The Atrium. The wait figure of no queue matches what I've seen. If you're trying to eat between classes, go before 11:45 and it's a different building entirely.
  Also worth saying: picked clean by 1:15 and not restocked again until the next morning.
  ```

#### 5. System answers in-corpus test questions correctly
- **Produced by:** `generate.py::answer` evaluated by `scorer.py::judge`
- **Result:** 5 of 5 across all three runs (**MET** against target of 5 of 5). Question 4 now passes the scorer in every run because retrieval successfully supplies the substantive Atrium chunk.
- **Real output example (Question 4, Run 1 — Pass):**
  ```
  According to dining_the_atrium_followup.txt, there is usually no queue if you go before 11:45 to eat between classes. However, it gets picked clean by 1:15 and is not restocked again until the next morning.
  ```

**Did it help?**
This change allowed the relevant chunk to rank 4th, below the top-k gate of 5, 
and allowed the model to successfully answer the question about dining at The
Atrium. I have not noticed any regressions from this change while re-testing it 
with the same questions.

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->
As far as I am aware, criteria-wise the current system passes all 5 and manages 
to successfully answer all posed questions and reject all invalid out-of-corpus 
questions. However, I do find it strange that the first run with the original 
line-based chunker implementation managed to answer the question about dining 
at The Atrium back in Unit 1, but stopped working once I returned to work on 
Unit 2 without me seemingly changing any relevant code, only the scoring 
function used for run_eval.py. If I had the time, this is a curiousity that I 
think is worth investigation.

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
I would probably rewrite criteria 4 to be even more specific. Not only must the 
chunker return complete thoughts, it must not return irrelevant information, 
such as chunks for header and title lines. I would probably think of a better 
way to word it that is more measureable though.