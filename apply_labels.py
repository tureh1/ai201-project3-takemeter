#!/usr/bin/env python3
"""
apply_labels.py — Apply Claude's draft labels (pre-labeling) to takemeter_raw.csv,
then build a class-balanced takemeter_data.csv for the notebook.

TAXONOMY (discourse effort/substance — a deliberately SUBJECTIVE task):
  s = substantive    — develops a point with specific detail, context, reasoning,
                       or useful info; the reader gains something.
  l = low_effort     — on-topic but minimal: a bare/vague question or generic
                       statement with little context.
  n = non_discourse  — not really discussion: memes, jokes, pure reactions,
                       karma/image posts.

These are DRAFT labels for human review. The CODES string is index-aligned to the
rows of takemeter_raw.csv (0..299).
"""
import csv
import random

CODES = (
    "slssnsslsl"  # 0-9
    "llssllssnl"  # 10-19
    "llllslslss"  # 20-29
    "lslllsllll"  # 30-39
    "ssllllslll"  # 40-49
    "llssllsnls"  # 50-59
    "llllllsssl"  # 60-69
    "llllslllss"  # 70-79
    "lllsslllsl"  # 80-89
    "ssslsllssl"  # 90-99
    "lsllsllnll"  # 100-109
    "lslsslllll"  # 110-119
    "llslsllsll"  # 120-129
    "snllslllss"  # 130-139
    "lsslsllssl"  # 140-149
    "lllllsnlsl"  # 150-159
    "llsslnlnsl"  # 160-169
    "lllslnnsls"  # 170-179
    "slssllnnnl"  # 180-189
    "lsnllllsns"  # 190-199
    "slslnllnll"  # 200-209
    "lsnnllsnnn"  # 210-219
    "nllnsnlnsn"  # 220-229
    "sllllsnlnl"  # 230-239
    "lnnlnlnlnl"  # 240-249
    "nllnlllsln"  # 250-259
    "lllsllnlnn"  # 260-269
    "nnnnnnnnnn"  # 270-279
    "nnnnnnnlnl"  # 280-289
    "nnnnnnnnnn"  # 290-299
)

LABEL = {"s": "substantive", "l": "low_effort", "n": "non_discourse"}

# Notes on genuinely borderline calls (index -> note). These are the hard cases.
NOTES = {
    5:   "edge: one-liner but cites specific spending (CyTown/coaching/Workday vs emails) -> substantive",
    11:  "edge: short, but gives a concrete reason/context -> substantive",
    98:  "edge: rumor-question, but carries a real claim + context (assault cases) -> substantive",
    156: "edge: jokey advocacy ('Bring Back the Dinky') with no real content -> non_discourse",
    178: "edge: brief rebuttal in a thread, little standalone content -> low_effort",
    217: "edge: pure one-line opinion ('Hickory Park Sucks. That's all') -> non_discourse",
    238: "edge: quirky humorous nostalgia, not real discussion -> non_discourse",
    257: "edge: complaint but with reasoning about room capacity -> substantive",
}

# ---- 1. Read raw, reset notes, apply labels ------------------------------
rows = list(csv.DictReader(open("takemeter_raw.csv", encoding="utf-8")))
assert len(rows) == len(CODES), f"row/label mismatch: {len(rows)} vs {len(CODES)}"

for i, r in enumerate(rows):
    r["label"] = LABEL[CODES[i]]
    r["notes"] = NOTES.get(i, "")

with open("takemeter_raw.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["source_type", "permalink", "text", "label", "notes"])
    w.writeheader()
    w.writerows(rows)

# ---- 2. Report distribution ----------------------------------------------
from collections import Counter
dist = Counter(r["label"] for r in rows)
total = len(rows)
print("FULL annotated set (takemeter_raw.csv):", total, "rows")
for k, v in sorted(dist.items()):
    print(f"  {k:<16} {v:>4}  ({100*v/total:.1f}%)")

# ---- 3. Build a class-balanced training CSV ------------------------------
# Keep ALL substantive + non_discourse (minorities); downsample low_effort.
random.seed(42)
by_label = {}
for r in rows:
    by_label.setdefault(r["label"], []).append(r)

TARGET = {"substantive": len(by_label["substantive"]),
          "non_discourse": len(by_label["non_discourse"]),
          "low_effort": 80}

balanced = []
for lab, items in by_label.items():
    n = min(TARGET[lab], len(items))
    balanced.extend(random.sample(items, n))
random.shuffle(balanced)

with open("takemeter_data.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["text", "label", "notes"])
    w.writeheader()
    for r in balanced:
        w.writerow({"text": r["text"], "label": r["label"], "notes": r["notes"]})

bdist = Counter(r["label"] for r in balanced)
bt = len(balanced)
print(f"\nBALANCED training set (takemeter_data.csv): {bt} rows  <-- upload THIS to the notebook")
for k, v in sorted(bdist.items()):
    print(f"  {k:<16} {v:>4}  ({100*v/bt:.1f}%)")
