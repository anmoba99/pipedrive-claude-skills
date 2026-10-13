#!/usr/bin/env python3
"""Find likely duplicate persons or organizations.

Matches on exact email, exact phone (digits only), and fuzzy normalized
name. Standard library only, no network.

Usage:
  python3 find_dupes.py records.json|records.csv [--kind person|org]
      [--threshold 0.88] [--out dupes.csv]

Input: JSON list (or {"data": [...]}, raw MCP result) or CSV with a header.
Fields used: id, name, email/emails, phone/phones, org_id/org_name.
Output: CSV rows id_a,id_b,name_a,name_b,reason,score (stdout or --out).
"""

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher

ORG_SUFFIXES = {
    "inc", "llc", "ltd", "limited", "gmbh", "ag", "sa", "sas", "sarl", "bv",
    "nv", "srl", "spa", "lda", "plc", "oy", "ab", "as", "co", "corp",
    "corporation", "company", "group", "holding", "unipessoal",
}


def strip_accents(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text)
                   if not unicodedata.combining(c))


def norm_name(name, kind):
    text = strip_accents(str(name or "")).lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    if kind == "org":
        tokens = [t for t in tokens if t not in ORG_SUFFIXES]
    return " ".join(tokens)


def values(field):
    """Pipedrive emails/phones: string, list of strings, or list of {value}."""
    if not field:
        return []
    if isinstance(field, str):
        return [v.strip() for v in re.split(r"[;,]", field) if v.strip()]
    out = []
    for item in field:
        v = item.get("value") if isinstance(item, dict) else item
        if v:
            out.append(str(v).strip())
    return out


def load(path):
    if path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        raw = raw.get("data") or raw.get("items") or []
    return [r.get("item", r) for r in raw if isinstance(r, dict)]


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("records")
    p.add_argument("--kind", choices=["person", "org"], default="person")
    p.add_argument("--threshold", type=float, default=0.88)
    p.add_argument("--out")
    args = p.parse_args()

    rows = load(args.records)
    recs = []
    for i, r in enumerate(rows):
        recs.append({
            "id": r.get("id") or f"row{i + 2}",
            "name": r.get("name") or " ".join(
                x for x in (r.get("first_name"), r.get("last_name")) if x),
            "emails": {e.lower() for e in values(r.get("emails") or r.get("email"))},
            "phones": {re.sub(r"\D", "", ph)[-9:] for ph in
                       values(r.get("phones") or r.get("phone"))
                       if len(re.sub(r"\D", "", ph)) >= 7},
        })
        recs[-1]["norm"] = norm_name(recs[-1]["name"], args.kind)

    pairs = {}

    def add(a, b, reason, score):
        key = tuple(sorted((str(a["id"]), str(b["id"]))))
        if key[0] == key[1]:
            return
        if key not in pairs or pairs[key][3] < score:
            pairs[key] = (a, b, reason, score) if str(a["id"]) == key[0] else (b, a, reason, score)

    by_email, by_phone, blocks = defaultdict(list), defaultdict(list), defaultdict(list)
    for r in recs:
        for e in r["emails"]:
            by_email[e].append(r)
        for ph in r["phones"]:
            by_phone[ph].append(r)
        if r["norm"]:
            first = r["norm"].split()[0]
            blocks[first[:4]].append(r)
            last = r["norm"].split()[-1]
            if last != first:
                blocks["L" + last[:4]].append(r)

    for group, reason in ((by_email, "same_email"), (by_phone, "same_phone")):
        for members in group.values():
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    add(members[i], members[j], reason, 1.0)

    for members in blocks.values():
        if len(members) > 400:  # very common first token, skip to stay fast
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                score = SequenceMatcher(None, a["norm"], b["norm"]).ratio()
                if score >= args.threshold:
                    add(a, b, "similar_name", round(score, 2))

    out = open(args.out, "w", newline="", encoding="utf-8") if args.out else sys.stdout
    w = csv.writer(out)
    w.writerow(["id_a", "id_b", "name_a", "name_b", "reason", "score"])
    for a, b, reason, score in sorted(pairs.values(), key=lambda t: -t[3]):
        w.writerow([a["id"], b["id"], a["name"], b["name"], reason, score])
    if args.out:
        out.close()
        print(f"{len(pairs)} likely duplicate pairs -> {args.out}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as e:
        print(f"ERROR {e}", file=sys.stderr)
        sys.exit(1)
