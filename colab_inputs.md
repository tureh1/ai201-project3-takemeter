# Colab Notebook Inputs (Milestones 4 & 5)

Copy-paste these into the starter notebook. This file also serves as the record of the
exact baseline prompt for the README.

---

## Section 1 — Label map

Replace the `LABEL_MAP` block in the notebook's Section 1 cell (it ships with an example
`analysis/hot_take/reaction` map — delete that) with:

```python
LABEL_MAP = {
    "substantive":   0,
    "low_effort":    1,
    "non_discourse": 2,
}
```

Then **upload `takemeter_data.csv`** when the notebook prompts you (NOT `takemeter_raw.csv`).
It has columns `text`, `label`, `notes` — the notebook uses `text` and `label`.

---

## Section 5 — Groq zero-shot classification prompt

Paste this as the `SYSTEM_PROMPT` value in the Section 5 prompt cell. **No `{text}`
placeholder** — the notebook adds the post itself as a separate user message
(`"Classify this post:\n\n{text}"`). This prompt names the task, defines each label with
one example, and forces a clean single-label answer:

```
You are rating the discourse QUALITY of posts from r/iastate, the Iowa State University
subreddit. Assign each post to exactly ONE category based on how much it actually
contributes.

substantive: develops a point with specific detail, context, reasoning, or useful
information — a reader genuinely gains something (a well-contextualized question, an
informative answer, a reasoned opinion, a detailed account).
Example: "Chatted ALL of thermo I — took a 20-credit overload, got mostly A's but it wrecked me. Is thermo II just as brutal with Zoz?"

low_effort: on-topic and genuine but minimal — a bare or vague question, or a generic
statement, with little or no context.
Example: "Friley. Is Stange Friley a good floor?"

non_discourse: not really discussion — memes, jokes, pure emotional reactions, image or
karma posts. The point is to amuse or react, not to inform or genuinely ask.
Example: "What a game.. So happy today"

Decision rule: the hard line is substantive vs low_effort — if the post supplies concrete
specifics, backstory, reasoning, or facts a reader could act on, it is substantive; if it is
a bare ask or generic statement, it is low_effort. If the post's purpose is humor or pure
reaction, it is non_discourse.

Respond with ONLY the label name. Do not explain your reasoning.

Valid labels:
substantive
low_effort
non_discourse
```

---

## Run order for Milestone 4 (baseline only)

1. Runtime → Change runtime type → **T4 GPU** → Save.
2. **Section 1:** paste the label map, run it, upload `takemeter_data.csv`.
3. **Section 2:** run it — splits 70/15/15 and tokenizes. Check the printed split sizes and
   per-split label counts look reasonable (~158 train / ~34 val / ~35 test, from 227 rows).
4. **Section 5:** add your `GROQ_API_KEY` (via the 🔑 Colab Secrets panel — name it exactly
   `GROQ_API_KEY` and enable notebook access), paste the prompt above, run the baseline cells.
5. Read the printed **baseline accuracy + per-class metrics**. If >~10% of responses are
   unparseable, the prompt needs to be clearer — but the "output ONLY the category name"
   rule above should keep that near zero.

> Do NOT run Section 3/4 (fine-tuning) yet — that's Milestone 5. Running the baseline first,
> on the locked test split, is the whole point: it tells us how hard the task is before we train.

---

## Baseline results (zero-shot Groq) — RECORDED

**Model used:** `llama-3.1-8b-instant` (switched from `llama-3.3-70b-versatile` because the
70B model's free-tier daily token budget was exhausted; the 8B model has a separate budget).
Test set: 35 examples, all 35 parseable (0 unparseable — the prompt's "output ONLY the label
name" rule worked).

- **Overall accuracy: 0.829** · **macro-F1: 0.83**
- Per-class F1: `substantive` 0.83 · `low_effort` 0.78 · `non_discourse` 0.87
- Per-class precision/recall: substantive 0.83/0.83 · low_effort 0.82/**0.75** · non_discourse 0.83/0.91

**Where the baseline struggled (hypothesis to test after fine-tuning):**
- `low_effort` is the weakest class — recall only **0.75**, so the model *misses* a quarter
  of genuine low-effort posts. Since its precision is fine (0.82), it's under-predicting
  low_effort, most likely reading thin posts as `substantive` (the hard, subjective boundary
  we predicted in planning.md).
- `non_discourse` is easiest (recall 0.91) — memes/jokes/reactions have obvious surface cues.
- **Prediction:** the fine-tuned DistilBERT will also confuse `low_effort` ↔ `substantive`
  most, because that boundary is genuinely fuzzy, not because either model is "bad."
