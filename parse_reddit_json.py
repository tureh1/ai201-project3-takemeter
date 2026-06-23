#!/usr/bin/env python3
"""
parse_reddit_json.py — Turn Reddit JSON files (saved from your browser) into the
TakeMeter labeling CSV.

WHY: Reddit blocks automated/script requests (403), but your logged-in *browser*
can still load the .json endpoints. So you save those pages, and this script parses
them locally — no API, no PRAW, no secret needed.

HOW TO USE:
  1. Make a folder next to this script called  raw_json
  2. In your browser (logged into Reddit), open each of these URLs and save the page
     (Ctrl+S) into the raw_json folder. Keep the .json extension.

        https://www.reddit.com/r/iastate/hot.json?limit=100
        https://www.reddit.com/r/iastate/new.json?limit=100
        https://www.reddit.com/r/iastate/top.json?limit=100&t=year
        https://www.reddit.com/r/iastate/top.json?limit=100&t=month
        https://www.reddit.com/r/iastate/rising.json?limit=100

     (Optional, for comment examples: open any individual post, add `.json` to its
      URL, and save that too — this script reads comment pages as well.)

  3. Run:   python parse_reddit_json.py

Output: takemeter_raw.csv  (columns: source_type, permalink, text, label, notes)
  - `label` and `notes` are BLANK on purpose — you fill them in during annotation.
"""

import csv
import glob
import json
import os
import re
import sys

INPUT_DIR = "raw_json"
OUTPUT = "takemeter_raw.csv"
MIN_CHARS = 25
MAX_CHARS = 1500
TARGET_ROWS = 300
JUNK_AUTHORS = {"AutoModerator", "[deleted]", None}


def clean(text):
    if not text:
        return ""
    text = text.strip()
    if text in ("[deleted]", "[removed]", ""):
        return ""
    text = re.sub(r"\s+", " ", text)
    for a, b in (("&amp;", "&"), ("&gt;", ">"), ("&lt;", "<")):
        text = text.replace(a, b)
    return text.strip()


def add_post(d, rows, seen):
    title = clean(d.get("title", ""))
    body = clean(d.get("selftext", ""))
    text = (title + ". " + body).strip(". ").strip() if body else title
    if MIN_CHARS <= len(text) <= MAX_CHARS and text.lower() not in seen:
        seen.add(text.lower())
        rows.append({"source_type": "post",
                     "permalink": "https://reddit.com" + d.get("permalink", ""),
                     "text": text})


def add_comment(d, rows, seen):
    if d.get("author") in JUNK_AUTHORS:
        return
    body = clean(d.get("body", ""))
    if MIN_CHARS <= len(body) <= MAX_CHARS and body.lower() not in seen:
        seen.add(body.lower())
        rows.append({"source_type": "comment",
                     "permalink": "https://reddit.com" + d.get("permalink", ""),
                     "text": body})


def walk_children(children, rows, seen):
    """Recursively pull t3 (posts) and t1 (comments) out of a listing's children."""
    for c in children:
        kind = c.get("kind")
        d = c.get("data", {})
        if kind == "t3":
            add_post(d, rows, seen)
        elif kind == "t1":
            add_comment(d, rows, seen)
            # comment replies nest under data.replies (a listing or "")
            replies = d.get("replies")
            if isinstance(replies, dict):
                walk_children(replies.get("data", {}).get("children", []), rows, seen)


def parse_file(path, rows, seen):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ! could not read {os.path.basename(path)}: {e}", file=sys.stderr)
        return
    # A listing page is a dict; a comments page is a list of two listings.
    listings = data if isinstance(data, list) else [data]
    for listing in listings:
        if isinstance(listing, dict) and "data" in listing:
            walk_children(listing["data"].get("children", []), rows, seen)


def main():
    if not os.path.isdir(INPUT_DIR):
        sys.exit(f"Folder '{INPUT_DIR}' not found. Create it and save Reddit .json files into it.")
    files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.json"))) + \
            sorted(glob.glob(os.path.join(INPUT_DIR, "*.txt")))   # browsers sometimes save as .txt
    if not files:
        sys.exit(f"No .json files in '{INPUT_DIR}'. Save the Reddit pages there first.")

    rows, seen = [], set()
    for path in files:
        print(f"Parsing {os.path.basename(path)} ...")
        parse_file(path, rows, seen)

    rows = rows[:TARGET_ROWS]
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source_type", "permalink", "text", "label", "notes"])
        w.writeheader()
        for r in rows:
            r.setdefault("label", "")
            r.setdefault("notes", "")
            w.writerow(r)

    n_posts = sum(1 for r in rows if r["source_type"] == "post")
    n_comments = sum(1 for r in rows if r["source_type"] == "comment")
    print(f"\n[OK] Wrote {len(rows)} examples to {OUTPUT}  ({n_posts} posts, {n_comments} comments).")
    if len(rows) < 220:
        print("[WARN] Fewer than 220 rows -- save a few more .json pages (more listings or "
              "some individual post comment pages) into raw_json and re-run.")


if __name__ == "__main__":
    main()
