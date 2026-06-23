# TakeMeter — Planning

A fine-tuned text classifier for discourse on **r/iastate** (the Iowa State University subreddit).

> This document is my working spec and design notebook. It is written *before* data
> collection and updated as decisions evolve. The polished, reader-facing summary lives
> in `README.md`.

---

## 1. Community

**Community:** [r/iastate](https://www.reddit.com/r/iastate/) — the Iowa State University subreddit.

**Why this community:** The discourse on r/iastate varies enormously *in quality*. On any
given day the front page mixes genuinely informative posts (detailed course/housing
breakdowns, reasoned arguments about campus issues), thin one-line questions, and pure
memes/reactions. That spread in effort and substance is exactly what makes "discourse
quality" a real, learnable distinction here rather than a contrived one. It is also fully
public and large enough to collect 200+ posts and comments without touching anything behind
authentication.

---

## 2. Labels

> **Taxonomy pivot (documented honestly).** My first taxonomy classified posts by *intent*
> (`seeking_help` / `sharing_experience` / `announcement`). It was clean and mutually
> exclusive, but the zero-shot Groq baseline scored **100%** on it — a red flag the project
> page explicitly warns about. Two reasons: (1) post *intent* is surface-level and a 70B LLM
> nails it, and (2) my labels were LLM-generated, so a second LLM reproduced them almost
> perfectly (circularity). A 100% baseline leaves no room to measure whether fine-tuning
> helps and produces no errors to analyze. So I switched to a genuinely **subjective**
> taxonomy about *discourse quality*, below. This is the project's actual theme and yields a
> non-trivial baseline plus analyzable mistakes.

Three labels, assigned by the **effort/substance** of the post — *how much does this post
actually contribute?* Mutually exclusive: each post gets exactly one.

### `substantive`
**Definition:** The post develops a point with specific detail, context, reasoning, or
useful information — a reader genuinely gains something (a well-contextualized question, an
informative answer, a reasoned opinion, a detailed account).

- *"Chatted ALL of thermo I — took a 20-credit overload, got mostly A's but it wrecked me. Is thermo II just as brutal with Zoz?"*
- *"ISU budgets ~$1M in concessions for the whole season; Iowa made $2.4M on alcohol alone last year, so this could realistically triple concession revenue."*

### `low_effort`
**Definition:** On-topic and genuine, but minimal — a bare or vague question, or a generic
statement, with little or no context. You couldn't learn much or answer well from it alone.

- *"Friley. Is Stange Friley a good floor?"*
- *"Pros and cons of rushing a sorority?"*

### `non_discourse`
**Definition:** Not really discussion — memes, jokes, pure emotional reactions, image/photo
or karma posts. The point is to amuse or react, not to inform or genuinely ask.

- *"What a f***ing game.. So happy today"*
- *"POV Butler is Your Therapist"*

---

## 3. Hard Edge Cases

The hardest boundary is **`substantive` ↔ `low_effort`** — *how much context counts as
"effort"?* That subjectivity is intentional: it's what makes the task non-trivial. A second
boundary, **`low_effort` ↔ `non_discourse`**, turns on whether a short post is a genuine
(if thin) contribution or just a reaction/joke.

**Decision rules:**
- *substantive vs low_effort:* if the post supplies concrete specifics, backstory, reasoning,
  or facts that a reader could act on or learn from → `substantive`. If it's a bare ask or a
  generic statement with no elaboration → `low_effort`.
- *low_effort vs non_discourse:* if the post is on-topic and sincerely trying to ask/state
  something (even briefly) → `low_effort`. If its purpose is humor, a reaction, or karma →
  `non_discourse`.

### Hard examples actually encountered during annotation

1. **"So we can spend millions on CyTown, coaching contracts, Workday upgrades, but we can't
   pay to let alumni keep their emails?"** — One sentence (looks `low_effort`) but it cites
   specific spending to make a real comparative point. **Decided `substantive`** — the
   specifics carry an argument.

2. **"Delts. Heard delts has to be dry first semester?? Doubt they will be, ifc hasn't done
   anything despite the assault cases this year."** — A short rumor-question, but it carries
   a concrete claim and context. **Decided `substantive`** (borderline with `low_effort`).

3. **"Hickory Park Sucks. That's all I have to say."** — An opinion, but zero substance and
   purely a reaction. **Decided `non_discourse`**, not `low_effort` — there's no genuine
   contribution, just a vent.

4. **"Bring Back the Dinky! Just need to lay some tracks, wouldn't even need to redo the
   paint 😅"** — Reads like advocacy but it's a joke with no real content. **Decided
   `non_discourse`.**

> Honest soft spot: the `substantive`/`low_effort` line depends on a judgment about "how much
> context is enough," so reasonable annotators (and the model) will disagree on borderline
> posts. That disagreement is the phenomenon this project is meant to surface, and it's the
> focus of the evaluation reflection.

### Annotation process & disclosure
All 300 collected examples were **pre-labeled by Claude (Opus 4.8)** against the definitions
above, with per-row notes on the borderline calls. Draft labels live in `takemeter_raw.csv`
(full 300) and the balanced, notebook-ready file is `takemeter_data.csv`. Class balance was
set by keeping **all** `substantive` and `non_discourse` examples and downsampling the
`low_effort` majority, giving a final split of ~35% / 35% / 30% (no runaway class). This AI
pre-labeling is disclosed again in the README's AI Usage section.

---

## 4. Data Collection Plan

**Source:** Public posts and top-level comments from [r/iastate](https://www.reddit.com/r/iastate/).
I will pull from a mix of `Hot`, `New`, and `Top (this year)` so the sample isn't skewed
toward a single moment (e.g., one viral thread). Both submissions (title + body) and
comments are fair game — comments are a good source of `substantive` discussion (reasoned
back-and-forth) and `non_discourse` quips, while submissions span all three levels.

**How:** Manual collection (copy-paste into a spreadsheet) is the default — it keeps me
close to the text, which matters for annotation quality. If manual collection drags, I may
use Reddit's public JSON endpoints (e.g., appending `.json` to a listing URL) to pull text
in bulk, but I will not build a scraping project; data collection should stay under ~2 hours.

**Target counts:** At least **210 examples**, aiming for a roughly even split of **~70 per
label** so no class dominates. The spec's hard limit is no single label above 70% of the
dataset; my self-imposed target is much tighter (≈33% each) because balanced classes give
the model a fair shot at every distinction.

**If a label is underrepresented after the first pass:** I'll do targeted collection for the
thin label rather than collecting randomly. For example, if `announcement` lags, I'll filter
r/iastate for event/PSA/deadline posts specifically (club fairs, registration dates, weather
closings) until I reach ~70. I will *not* relabel borderline posts just to fill a quota —
that would corrupt the boundary. I'd rather collect more raw posts than force-fit labels.

**Storage:** One CSV, `takemeter_data.csv`, with columns `text`, `label`, and `notes`
(notes capture why a hard case was decided the way it was). The CSV is committed unsplit —
the Colab notebook does the 70/15/15 train/val/test split automatically.

---

## 5. Evaluation Metrics

Accuracy alone is insufficient here because (a) even with balanced classes, a model can be
strong on one label and near-useless on another, and accuracy hides that, and (b) the value
of this tool depends on it being trustworthy *per category*, not just on average. So I'll use:

- **Overall accuracy** — headline number, and the simplest way to compare against the
  zero-shot baseline on the same test set.
- **Per-class precision, recall, and F1** — the core diagnostic. Precision tells me when the
  model says "announcement," how often it's right; recall tells me how many real
  announcements it catches. F1 is the single per-class summary I'll lead with.
- **Macro-F1** (unweighted mean of per-class F1) — my primary single-number metric, because
  it weights all three classes equally and won't let a strong majority class mask a weak one.
- **Confusion matrix** — to see *which* boundary fails and in *which direction* (e.g., are
  `sharing_experience` posts being read as `seeking_help`?). This drives the error analysis.

I'll report all of these for **both** the fine-tuned model and the zero-shot Groq baseline
on the identical locked test set.

---

## 6. Definition of Success

Concrete thresholds, decided up front so I can judge the result honestly:

- **Minimum bar (fine-tuning "worked"):** fine-tuned **macro-F1 ≥ 0.75**, **every per-class
  F1 ≥ 0.65** (no dead class), and the fine-tuned model beats the zero-shot baseline accuracy
  by **≥ 10 percentage points**. If it doesn't clear the baseline, that's a finding to
  investigate (leakage, imbalance, or noisy labels), not a number to massage.
- **"Good enough to deploy" as a real community tool:** **macro-F1 ≥ 0.80** with no per-class
  F1 below 0.70. At that level it could auto-tag posts (e.g., flag `seeking_help` threads for
  faster answers) with few enough errors that a human reviewer isn't constantly overriding it.

Given a subjective task and only ~200 examples, I expect to land near the minimum bar rather
than the deployment bar, and I'll say so plainly in the README.

---

## 7. AI Tool Plan

There's no application code to generate in this project, so AI tools help at three specific
points:

**Label stress-testing (before annotating):** I'll give Claude my three label definitions
and the edge-case rules and ask it to generate 8–10 posts that deliberately sit on the
boundaries (especially the "experience + question" case). If I can't classify its outputs
cleanly with my current rules, the rules are too loose and I'll tighten them before
annotating 200 real posts.

**Annotation assistance (during collection):** I plan to use **Groq's
`llama-3.3-70b-versatile`** to pre-label a batch of collected posts using my planning.md
definitions, then **manually review and correct every single pre-assigned label** — skimming
defeats the purpose. I'll track which rows were pre-labeled via a value in the `notes` column
(e.g., `prelabeled:llama`) so I can disclose it honestly in the README's AI Usage section.
If pre-labeling turns out to add noise rather than speed, I'll drop it and label by hand.

**Failure analysis (after evaluation):** I'll paste the list of misclassified test examples
into Claude and ask it to surface systematic patterns (a recurring confused label pair, post
length, sarcasm, low-information posts). Then I'll re-read those examples myself to confirm or
discard each proposed pattern before writing it up — the AI proposes, I verify.

> Stretch features, if attempted, will be logged here before I start each one.

