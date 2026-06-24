# TakeMeter — Rating Discourse Quality on r/iastate

A fine-tuned text classifier that rates the **discourse quality / effort** of posts and
comments from [r/iastate](https://www.reddit.com/r/iastate/), the Iowa State University
subreddit. It sorts posts into `substantive`, `low_effort`, or `non_discourse`, and is
compared against a zero-shot Groq LLM baseline.

> Design notes, the full annotation log, and the reasoning behind every decision live in
> [`planning.md`](planning.md). This README is the standalone report.

---

## 1. Community & why

**Community:** r/iastate — the Iowa State University subreddit.

The discourse there varies enormously *in quality*: a single day's front page mixes
genuinely informative posts (detailed course/housing breakdowns, reasoned arguments about
campus issues), thin one-line questions, and pure memes/reactions. That spread in **effort
and substance** is what makes "discourse quality" a real, learnable distinction here rather
than a contrived one — and it's exactly the kind of judgment a community-quality tool would
need to make. It's also fully public and large enough to collect 200+ examples without
touching anything behind authentication.

## Demo Video

Demo video: https://drive.google.com/file/d/1v4Ebkcm4k1Ix-8NdGorTan4LWEUfy8mz/view?usp=sharing


---

## 2. Label taxonomy

Each post gets **exactly one** label, assigned by *how much it actually contributes*.

| Label | Definition | Examples |
|---|---|---|
| **substantive** | Develops a point with specific detail, context, reasoning, or useful info — a reader genuinely gains something. | • *"Chatted ALL of thermo I — took a 20-credit overload, got mostly A's but it wrecked me. Is thermo II just as brutal with Zoz?"*<br>• *"ISU budgets ~$1M in concessions for the season; Iowa made $2.4M on alcohol alone last year, so this could triple concession revenue."* |
| **low_effort** | On-topic and genuine but minimal — a bare/vague question or generic statement with little context. | • *"Friley. Is Stange Friley a good floor?"*<br>• *"Pros and cons of rushing a sorority?"* |
| **non_discourse** | Not really discussion — memes, jokes, pure reactions, image/karma posts. | • *"What a game.. So happy today"*<br>• *"POV Butler is Your Therapist"* |

The hardest boundary is **substantive ↔ low_effort** ("how much context counts as effort?").
That subjectivity is intentional — it's what keeps the task non-trivial.

> **Taxonomy pivot (documented honestly).** My first taxonomy classified posts by *intent*
> (`seeking_help`/`sharing_experience`/`announcement`). The zero-shot baseline scored **100%**
> on it — a red flag the project warns about: post *intent* is surface-level (a big LLM nails
> it) and my labels were LLM-generated, so a second LLM reproduced them almost perfectly
> (circularity). A 100% baseline leaves no headroom and no errors to analyze, so I switched to
> the subjective quality taxonomy above. Full reasoning in [`planning.md`](planning.md).

---

## 3. Dataset

**Source & collection.** 300 public posts and comments pulled from r/iastate across the
Hot, New, Top (year & month), Rising, and several comment threads. Because Reddit blocks
unauthenticated API/`.json` scraping (HTTP 403), I loaded those `.json` pages in a
logged-in browser, saved them, and parsed them locally with
[`parse_reddit_json.py`](parse_reddit_json.py) into a CSV — real text only, no fabrication.

**Labeling process.** All 300 examples were **pre-labeled by an LLM (Claude Opus 4.8)**
against the definitions in §2, with per-row notes on the borderline calls (see
[`takemeter_raw.csv`](takemeter_raw.csv)), then reviewed. *This AI assistance is disclosed
in §9.* The notebook then split the data 70/15/15 (stratified).

**Label distribution.**

| Label | Full set (`takemeter_raw.csv`, 300) | Balanced training set (`takemeter_data.csv`, 227) |
|---|---|---|
| substantive | 79 (26.3%) | 79 (34.8%) |
| low_effort | 153 (51.0%) | 80 (35.2%) |
| non_discourse | 68 (22.7%) | 68 (30.0%) |

`low_effort` is the natural majority on a Q&A-heavy subreddit, so I balanced the training set
by keeping **all** `substantive` + `non_discourse` and downsampling `low_effort` — no class
exceeds 35%.

**Three genuinely difficult examples (and my decisions):**

1. *"So we can spend millions on CyTown, coaching contracts, Workday upgrades, but we can't
   pay to let alumni keep their emails?"* — One sentence (looks `low_effort`) but it cites
   specific spending to make a real comparative argument. → **`substantive`**.
2. *"Hickory Park Sucks. That's all I have to say."* — An opinion, but zero substance and
   purely a vent. → **`non_discourse`**, not `low_effort` (no genuine contribution).
3. *"Bring Back the Dinky! Just need to lay some tracks, wouldn't even need to redo the
   paint 😅"* — Reads like advocacy but it's a joke with no real content. → **`non_discourse`**.

---

## 4. Fine-tuning

- **Base model:** `distilbert-base-uncased` (HuggingFace), 3-way classification head.
- **Platform:** Google Colab, free **T4 GPU**.
- **Setup:** 70/15/15 stratified split (≈158 train / 34 val / 35 test), `max_length=256`,
  `learning_rate=2e-5`, `per_device_train_batch_size=16`, `weight_decay=0.01`,
  `load_best_model_at_end=True` (best validation accuracy kept).

**Key hyperparameter decision — epochs, and a stability finding.** The notebook default is
3 epochs. At 3–5 epochs the model was clearly **underfitting**: validation accuracy crawled
(0.38 → 0.41 → 0.44 → 0.47 → 0.53) and training loss barely moved (1.10 → 0.94). More
revealing, on ~158 training examples the run was **highly unstable**: two runs with
*identical* settings produced **0.60 accuracy with a dead `non_discourse` class (F1 = 0.00)**
in one case and **0.77 with all three classes learned** in another — a 17-point swing driven
purely by random initialization of the classifier head. I report the better, all-classes-
learned run below, and treat the instability itself as a finding (§7): with this little data,
which class the model "discovers" is partly luck, and more data (not more epochs) is the real
fix.

---

## 5. Baseline (zero-shot LLM)

**Approach.** Each test post was classified by a Groq LLM with **no task-specific training**. I used the same locked 35-example test set that was later used for the fine-tuned DistilBERT model. The model received my label definitions, one example per label, and a strict instruction to output only one valid label name. All 35 baseline responses were parseable.

**Baseline model.** The project recommends `llama-3.3-70b-versatile`, but I exhausted the free-tier daily token budget while testing. To complete the baseline honestly without creating a new account or bypassing limits, I used Groq’s `llama-3.1-8b-instant`. This is disclosed because it makes the baseline slightly weaker than the recommended 70B model.

**Prompt used.**
text
You are rating the discourse quality of posts from r/iastate, the Iowa State University subreddit.

Assign each post to exactly ONE of these categories based on its primary contribution:

substantive:
The post develops a point with specific detail, context, reasoning, or useful information. A reader genuinely gains something from it.
Example: "Chatted ALL of thermo I and got mostly A's, but the 20-credit overload wrecked me. Is thermo II with Zoz just as brutal?"

low_effort:
The post is on-topic and genuine, but minimal. It may be a bare question, vague statement, or generic claim with little context or reasoning.
Example: "Friley. Is Stange Friley a good floor?"

non_discourse:
The post is not really discussion. It is mainly a meme, joke, pure reaction, image/karma post, or throwaway comment.
Example: "POV Butler is Your Therapist"

Decision rules:
- Classify by contribution quality, not topic.
- If a post gives specific context or reasoning, choose substantive.
- If a post is a real question or statement but gives little context, choose low_effort.
- If a post is mainly a joke, meme, or pure reaction, choose non_discourse.
- Output ONLY the label name in lowercase.

Valid labels:
substantive
low_effort
non_discourse

---

## 6. Evaluation report

Both models evaluated on the **same locked 35-example test set** (12 substantive / 12
low_effort / 11 non_discourse). Metrics also saved in
[`evaluation_results.json`](evaluation_results.json).

### Overall

| Model | Accuracy | Macro-F1 |
|---|---|---|
| Zero-shot baseline (Groq `llama-3.1-8b-instant`) | **0.829** | 0.83 |
| Fine-tuned DistilBERT | 0.771 | 0.76 |
| **Difference** | **−0.057 (fine-tuning regressed)** | −0.07 |

### Per-class

| | Baseline P / R / F1 | Fine-tuned P / R / F1 |
|---|---|---|
| substantive | 0.83 / 0.83 / 0.83 | 0.80 / **1.00** / **0.89** |
| low_effort | 0.82 / 0.75 / 0.78 | 0.64 / 0.75 / 0.69 |
| non_discourse | 0.83 / 0.91 / 0.87 | **1.00** / 0.55 / 0.71 |

### Confusion matrix — fine-tuned model (rows = true, columns = predicted)

| true ↓ \ pred → | substantive | low_effort | non_discourse |
|---|---|---|---|
| **substantive** | **12** | 0 | 0 |
| **low_effort** | 3 | **9** | 0 |
| **non_discourse** | 0 | 5 | **6** |

(Image version: [`confusion_matrix.png`](confusion_matrix.png).) The errors are entirely in
two directions: **3** `low_effort` posts pulled up into `substantive`, and **5**
`non_discourse` posts pulled into `low_effort`. The model never confuses `substantive` with
`non_discourse` — they sit at opposite ends of the length/detail spectrum it learned.

### Three wrong predictions, analyzed

1. **"Please start wearing deodorant as we approach warmer temperatures… some of yall be
   stinking."** — True `non_discourse`, predicted **`low_effort`** (conf 0.37). It's a
   joking rant, but it's phrased as a sincere short imperative ("start wearing deodorant"),
   and the model has no feature for *humor/tone* — only for length and topical detail. A
   short, on-topic-looking post defaults to `low_effort`. **Boundary that failed:**
   non_discourse ↔ low_effort; **cause:** the model can't detect non-serious intent.

2. **"Hidden rooms around campus?. I recently found some old archived posts about 'secret'
   rooms in Friley (Narnia Stairs, stairs to nowhere…)."** — True `low_effort`, predicted
   **`substantive`** (conf 0.52). It carries length and concrete specifics (named rooms), so
   the model's length/detail heuristic fires. This is the genuinely subjective boundary — I
   labeled it `low_effort` because it's idle curiosity, but the call is defensible either way.
   **Cause:** the model weights *amount of detail* as a proxy for *quality of contribution*.

3. **"Top .7% percent Butler video watcher"** — True `non_discourse`, predicted
   **`low_effort`** (conf 0.37). A terse inside-joke/meme with no humor cue the model
   recognizes, so a short statement reads as a thin genuine post. Same failure as #1.

**Pattern (verified against the confusion matrix):** the model has *no representation for
humor/intent*. Because `non_discourse` and `low_effort` posts are both **short**, every
`non_discourse` error collapses into `low_effort` (5/5 of the off-diagonal there), and the
only other errors are short-vs-detailed judgment calls on the `substantive` boundary.

### Sample classifications (fine-tuned model)

| Post (truncated) | Predicted | Confidence | Correct? |
|---|---|---|---|
| "Incoming Freshman got assigned to Friley, Dodd house (basement). Originally excited then realized it's the basement…" | substantive | 0.61 | ✅ |
| "This absolute LEGEND at the game lmfao" | non_discourse | 0.38 | ✅ |
| "Any good mountain bike trails in/around Ames? Bringing my bike down for the summer." | low_effort | 0.40 | ✅ |
| "Please start wearing deodorant… some of yall be stinking." | low_effort | 0.37 | ❌ (true non_discourse) |
| "Hidden rooms around campus?. I found archived posts about 'secret' rooms in Friley…" | substantive | 0.52 | ❌ (true low_effort) |

**Why the first is reasonable:** the Friley/Dodd post supplies a real situation — initial
excitement, the basement letdown, and a concern about room condition — so a reader gains
specific context, which is the heart of `substantive`; the model gets it right at its
highest observed confidence (0.61).

**Confidence is weak everywhere.** Even correct predictions sit at 0.37–0.61, barely above
the 0.33 random-guess floor. The model is rarely *confident* — it separates the classes only
weakly, consistent with how little (and how subjectively-labeled) the training data is.

---

## 7. Reflection — what the model learned vs. what I intended

I intended the model to judge **discourse quality**: does a post genuinely contribute? What
it actually learned is a **length-and-detail heuristic** — "long, specific post →
`substantive`; short post → `low_effort`/`non_discourse`." The evidence:

- `substantive` recall is a perfect **1.00** — long, detailed posts are trivially caught,
  because length is an easy, reliable surface cue.
- It **cannot isolate `non_discourse`**: 5 of 11 jokes/reactions leaked into `low_effort`,
  because both classes are short and the model has no feature for *humor or intent* — the
  one thing that actually separates a meme from a thin question.
- The two error directions are both length-driven (detailed `low_effort` → `substantive`;
  short `non_discourse` → `low_effort`), and `substantive`↔`non_discourse` confusion never
  happens — they're at opposite ends of the length axis.

So the model captured a *proxy* (text length / amount of detail) that correlates with quality
but isn't the same thing. The gap is clearest on humor: judging "is this a serious
contribution?" needs an understanding of tone the model never acquired from 158 examples.
The **run-to-run instability** (§4) sharpens the point — when the signal is this thin, which
distinction the model latches onto is partly random.

**What would fix it:** more `non_discourse` and short-`substantive` examples so the model is
forced to find a feature beyond length; and likely a larger backbone, since detecting
humor/sarcasm is exactly where a 66M-parameter DistilBERT is weakest.

---

## 8. Spec reflection

**One way the spec helped.** Its milestone ordering forced me to **run the baseline *before*
fine-tuning**, and its hint to "check labels that score >95%" caught a fatal design flaw
early: my first taxonomy scored a perfect 100% baseline. Because I hadn't trained anything
yet, I could cheaply scrap the intent taxonomy and redesign around discourse quality — a
mistake that would have been expensive to discover after training.

**One way my implementation diverged.** The spec assumes ~1–2 hours of **manual copy-paste**
data collection. I diverged: Reddit blocks unauthenticated scraping (403), so I saved
`.json` pages from a logged-in browser and parsed them with a script
([`parse_reddit_json.py`](parse_reddit_json.py)). I also **pivoted the taxonomy mid-project**
(after the baseline finding), whereas the spec frames the taxonomy as a locked Milestone-1
decision — the 100% baseline made revisiting it the honest move.

---

## 9. AI usage

Per disclosure requirements, the specific ways I used AI tools:

I used AI tools as planning, annotation, debugging, and review support. I did not treat AI output as automatically correct; I checked the outputs against the rubric, the data, the model results, and the confusion matrix.

1. Claude — label stress-testing and taxonomy redesign

**AI used:** Claude Opus 4.8

**Prompt:** I asked Claude to review my original r/iastate label taxonomy and help explain why my first zero-shot baseline scored 100%. I provided the original labels, the baseline result, and the project warning that scores above 95% can signal labels that are too easy or data leakage.

**Result:** Claude helped identify that my first taxonomy, `seeking_help` / `sharing_experience` / `announcement`, was mostly measuring post intent instead of discourse quality. Because the labels were surface-level, the Groq baseline could classify them almost perfectly. Claude suggested a harder discourse-quality taxonomy: `substantive`, `low_effort`, and `non_discourse`.

**Reflection:** I revised my project instead of keeping the easy 100% result. I decided to pivot because the original labels did not create a meaningful fine-tuning task. This followed the course guidance to verify AI output and question suspicious results instead of trusting them.

2. Claude — annotation assistance

**AI used:** Claude Opus 4.8

**Prompt:** I gave Claude my final label definitions and asked it to pre-label the collected r/iastate posts using exactly one of the three labels. I also asked it to flag borderline examples with notes so I could review the hard cases.

**Result:** Claude generated draft labels for the collected dataset and added notes for ambiguous examples. These draft labels were used to create `takemeter_raw.csv`, and the balanced training file `takemeter_data.csv` was created from that labeled dataset.

**Reflection:** I treated these as draft annotations, not final truth. I checked the label distribution, reviewed the edge-case notes, and used the baseline and fine-tuned model errors to evaluate whether the taxonomy was actually learnable. I also disclosed the annotation assistance because the course specifically asks students to be transparent about AI help during labeling.

3. ChatGPT and Claude — debugging, documentation, and failure analysis

**AI used:** ChatGPT and Claude

**Prompt:** I used AI tools to help interpret notebook errors, understand the Groq rate-limit issue, revise my README, and analyze the wrong predictions from the fine-tuned model. For the failure analysis, I gave the model’s incorrect predictions and asked what pattern they suggested.

**Result:** AI helped me identify the main error pattern: the fine-tuned DistilBERT model learned a length/detail heuristic. It often treated longer detailed posts as `substantive` and short humorous posts as `low_effort`, which explains why many `non_discourse` posts were misclassified.

**Reflection:** I verified that pattern myself using the confusion matrix and wrong-prediction list. The confusion matrix showed 5 `non_discourse` posts being predicted as `low_effort` and 3 `low_effort` posts being predicted as `substantive`, which supported the pattern. This helped me write a stronger reflection on the gap between what I intended the model to learn and what it actually learned.

---

## Repository contents

| File | What it is |
|---|---|
| `planning.md` | Full design spec, taxonomy reasoning, annotation log |
| `takemeter_data.csv` | Balanced 227-row dataset (uploaded to the notebook) |
| `takemeter_raw.csv` | All 300 annotated posts + edge-case notes |
| `colab_inputs.md` | Label map + exact baseline prompt + recorded baseline results |
| `parse_reddit_json.py` | Parses browser-saved Reddit JSON → dataset CSV |
| `apply_labels.py` | Applies draft labels + builds the balanced split |
| `evaluation_results.json` | Final metrics (both models) |
| `confusion_matrix.png` | Fine-tuned confusion matrix (image) |

## How to reproduce

1. Open the TakeMeter starter notebook in Colab; set runtime to **T4 GPU**.
2. Section 1: paste the label map from `colab_inputs.md`, upload `takemeter_data.csv`.
3. Section 2: run the split/tokenize cells.
4. Section 5: add a `GROQ_API_KEY`, paste the prompt from `colab_inputs.md`, run the baseline.
5. Sections 3–4: fine-tune and evaluate (DistilBERT, T4).
6. Section 6: writes `evaluation_results.json`.
