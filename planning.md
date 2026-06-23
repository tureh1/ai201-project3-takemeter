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

<!-- Additional hard examples found during annotation will be appended here in Milestone 3. -->

---

<!-- Milestone 2 will add: Data Collection Plan, Evaluation Metrics, Definition of Success, AI Tool Plan. -->
