# TakeMeter — Planning

A fine-tuned text classifier for discourse on **r/iastate** (the Iowa State University subreddit).

> This document is my working spec and design notebook. It is written *before* data
> collection and updated as decisions evolve. The polished, reader-facing summary lives
> in `README.md`.

---

## 1. Community

**Community:** [r/iastate](https://www.reddit.com/r/iastate/) — the Iowa State University subreddit.

**Why this community:** The discourse on r/iastate is *functionally varied*. On any given
day the front page mixes students asking for course/dorm/logistics advice, students
recounting personal experiences with professors or campus life, and people broadcasting
events, deadlines, and news. Those three modes show up constantly and are distinguishable
from one another, which makes for a balanced, learnable classification task. It is also
fully public and large enough to collect 200+ posts and comments without touching anything
behind authentication.

---

## 2. Labels

Three labels, assigned by the **primary purpose** of the post — *what is the post for?*
The labels are mutually exclusive: a post gets exactly one, decided by its main intent.

### `seeking_help`
**Definition:** The post's main purpose is to get a question answered or to solicit
advice/recommendations from the community.

- *"Is Chem 167 with Prof. Smith doable if I'm not a science major? Trying to decide my schedule."*
- *"Anyone know the cheapest place near campus to get a bike fixed?"*

### `sharing_experience`
**Definition:** The post's main purpose is to recount a first-person account or state an
opinion grounded in the author's own experience, without asking the community for anything.

- *"Just finished my first semester in Friley — honestly the community was way better than I expected, met most of my friends there."*
- *"Took Stat 226 online last fall. It was a slog but the exams were fair if you keep up with the homework."*

### `announcement`
**Definition:** The post's main purpose is to broadcast news, an event, or information to
the community, with no question and no personal-experience framing.

- *"Free pizza at the Memorial Union from 5–7 tonight for the club fair."*
- *"Reminder: spring parking permits go on sale Monday at 8 AM."*

---

## 3. Hard Edge Cases

### Edge case A — "experience + question" (the primary anticipated ambiguity)
A post that recounts a personal experience **and** asks a question, e.g.:

> *"I took Chem 167 and it was brutal — does anyone know if 178 is any easier?"*

This sits between `sharing_experience` and `seeking_help`.

**Decision rule:** Classify by **primary purpose**. If removing the question leaves a
complete, self-standing post, the experience is the point → `sharing_experience`. If the
experience is just context the author provides so people can answer, the question is the
point → `seeking_help`. The example above exists to get an answer about 178, so the story
is only setup → **`seeking_help`**.

### Edge case B — announcement vs. sharing_experience
> *"Went to the free pizza event, it was packed and fun"* vs. *"Free pizza tonight 5–7."*

**Decision rule:** First-person and after-the-fact → `sharing_experience`. Informing people
so they can act (forward-looking, no personal account) → `announcement`.

### Hard examples actually encountered during annotation (Milestone 3)

These are real r/iastate posts that gave me genuine pause, with the call I made:

1. **"Update: Broke up with my engineering gf because she said my major is 'way easier
   than hers'. AITA?"** — Classic experience+question. "AITA?" looks like a request, but
   the post is a self-contained personal update; the question is rhetorical framing.
   **Decided `sharing_experience`** (per Edge Case A: removing the question leaves a
   complete post).

2. **"Iowa State Names Jimmy Rogers Head Football Coach. Thoughts?"** — Announcement vs.
   seeking_help. It tacks "Thoughts?" onto a news headline. The primary purpose is
   broadcasting the hire; the one-word question is an engagement prompt, not a genuine
   request for advice. **Decided `announcement`.**

3. **"What's with the politeness? I'm new to Iowa. Whenever I go out people greet me
   warmly..."** — Seeking_help vs. sharing_experience. Opens with a question but the body
   is a first-person observation/account of the poster's experience; "What's with" is
   rhetorical. **Decided `sharing_experience`.**

4. **"Pls stop farting in class, use deodorant and take a damn shower..."** — Announcement
   (PSA) vs. sharing_experience (venting). It reads like a public-service notice but is
   really a first-person rant aimed at specific classmates, with no information to convey.
   **Decided `sharing_experience`.**

> A recurring tension: r/iastate has many memes/jokes/sports reactions that aren't pure
> "experiences." I folded these into `sharing_experience` as the closest fit (the author is
> expressing something, not asking or broadcasting). This is a known soft spot in the
> taxonomy and is flagged for the evaluation reflection.

### Annotation process & disclosure
All 300 collected examples were **pre-labeled by Claude (Opus 4.8)** using the definitions
above, then reviewed. Draft labels and per-row edge-case notes live in `takemeter_raw.csv`
(full set) and the balanced, notebook-ready file is `takemeter_data.csv`. Class balance was
adjusted by keeping all `announcement` examples and downsampling the two larger classes so
no class is a runaway majority (final: ~40/40/20). This AI pre-labeling is disclosed again
in the README's AI Usage section.

---

## 4. Data Collection Plan

**Source:** Public posts and top-level comments from [r/iastate](https://www.reddit.com/r/iastate/).
I will pull from a mix of `Hot`, `New`, and `Top (this year)` so the sample isn't skewed
toward a single moment (e.g., one viral thread). Both submissions (title + body) and
substantive comments are fair game — comments are a good source of `seeking_help` and
`sharing_experience`, while submissions skew toward `announcement`.

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

