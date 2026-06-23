#!/usr/bin/env python3
"""
apply_labels.py — Apply Claude's draft labels (pre-labeling) to takemeter_raw.csv,
then build a class-balanced takemeter_data.csv for the notebook.

These are DRAFT labels for human review (the required annotation step). Codes:
  h = seeking_help, e = sharing_experience, a = announcement
The CODES string is index-aligned to the rows of takemeter_raw.csv (0..299).
"""
import csv
import random

CODES = (
    "haeheeaahh"  # 0-9
    "ahhhhahhhh"  # 10-19
    "ahhhhhhheh"  # 20-29
    "aahahhhhhh"  # 30-39
    "hhaaehhhha"  # 40-49
    "hhhhahheah"  # 50-59
    "hhhhheahah"  # 60-69
    "ahhhehhhhh"  # 70-79
    "hahhhheahe"  # 80-89
    "hhaahhhahh"  # 90-99
    "haahhhhehh"  # 100-109
    "hhhhhhhhhh"  # 110-119
    "hhhhhhhhhh"  # 120-129
    "hehhhhhhhh"  # 130-139
    "hhhhhhhhhh"  # 140-149
    "ahehhheahh"  # 150-159
    "hhhhhehehh"  # 160-169
    "hhahheeeee"  # 170-179
    "eeeeeeeeee"  # 180-189
    "eeeeeeehee"  # 190-199
    "eeeeeeheee"  # 200-209
    "eaeeeeaeee"  # 210-219
    "eaheeeeeae"  # 220-229
    "eeaheeeaea"  # 230-239
    "aeeaeaeheh"  # 240-249
    "ehaeeeheae"  # 250-259
    "hehhaaehee"  # 260-269
    "eheeeeeeee"  # 270-279
    "eeeeeeehee"  # 280-289
    "eeeeeeeeee"  # 290-299
)

LABEL = {"h": "seeking_help", "e": "sharing_experience", "a": "announcement"}

# Notes on genuinely borderline calls (index -> note).
NOTES = {
    2:   "edge: experience+question; AITA is rhetorical, the update is the point -> sharing_experience",
    3:   "edge: shares an idea but 'pointers welcome' -> seeking_help",
    44:  "edge: rhetorical complaint ('just why'), not a real question -> sharing_experience",
    57:  "edge: in-the-moment reaction report, not a broadcast -> sharing_experience",
    65:  "edge: shares a milestone with faint 'any folks here?' -> sharing_experience (sharing is primary)",
    81:  "edge: reports an event with no first-person framing -> announcement",
    89:  "edge: sports take/opinion, not a question -> sharing_experience",
    150: "edge: news link + opinion; the news is the point -> announcement",
    188: "low-content (gif only) -> consider dropping in review",
    198: "edge: PSA-style rant aimed at a person -> sharing_experience (venting)",
    202: "edge: observation w/ rhetorical 'what's with'; not asking -> sharing_experience",
    222: "edge: 'what are the odds' reads as discussion/asking -> seeking_help",
    237: "edge: found-pet resolution informing followers -> announcement",
    243: "edge: news headline + 'Thoughts?' tacked on; news is primary -> announcement",
    247: "edge: asks if swans return amid musing -> seeking_help",
    263: "edge: shares concern + 'anyone else experiencing?' -> seeking_help",
    265: "edge: shares a letter + 'I encourage everyone to read' -> announcement",
}

# ---- 1. Read raw, apply labels -------------------------------------------
rows = list(csv.DictReader(open("takemeter_raw.csv", encoding="utf-8")))
assert len(rows) == len(CODES), f"row/label mismatch: {len(rows)} vs {len(CODES)}"

for i, r in enumerate(rows):
    r["label"] = LABEL[CODES[i]]
    if i in NOTES:
        r["notes"] = NOTES[i]

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
    print(f"  {k:<20} {v:>4}  ({100*v/total:.1f}%)")

# ---- 3. Build a class-balanced training CSV ------------------------------
# Keep ALL announcements (minority); downsample the two larger classes so each
# class is well represented (announcement ~20%). Reproducible via fixed seed.
random.seed(42)
by_label = {}
for i, r in enumerate(rows):
    by_label.setdefault(r["label"], []).append(r)

TARGET = {"announcement": len(by_label["announcement"]),  # keep all
          "seeking_help": 84,
          "sharing_experience": 84}

balanced = []
for lab, items in by_label.items():
    n = min(TARGET[lab], len(items))
    balanced.extend(random.sample(items, n))
random.shuffle(balanced)

# The notebook only needs text,label — keep notes too for traceability.
with open("takemeter_data.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["text", "label", "notes"])
    w.writeheader()
    for r in balanced:
        w.writerow({"text": r["text"], "label": r["label"], "notes": r["notes"]})

bdist = Counter(r["label"] for r in balanced)
bt = len(balanced)
print(f"\nBALANCED training set (takemeter_data.csv): {bt} rows  <-- upload THIS to the notebook")
for k, v in sorted(bdist.items()):
    print(f"  {k:<20} {v:>4}  ({100*v/bt:.1f}%)")
