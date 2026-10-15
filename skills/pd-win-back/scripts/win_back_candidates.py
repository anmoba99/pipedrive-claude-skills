#!/usr/bin/env python3
"""Rank lost deals that are worth a new deal now, and say why now.

The lost deal itself is never changed: the output is a list of chances to
create a new deal for the same organization and person.

Each lost deal gets a reason class from a map Claude builds from the
account's own lost reasons (timing, budget, competitor, no_decision,
went_silent, price, product_gap, bad_fit, other). Triggers are then checked
from data: the timing window has come around, a competitor contract is near
its likely anniversary, the contact is now linked to another organization,
the organization shows new activity since the loss. Bad fit and do not
contact are never suggested. Standard library only, no network, no LLM.

Usage:
  python3 win_back_candidates.py --lost lost*.json [--reason-map reasons.json]
      [--persons persons*.json] [--open open*.json] [--orgs orgs*.json]
      [--min-days 60] [--top 25] [--today YYYY-MM-DD] [--out candidates.json]
      [--scope-note "..."]

Reason map: {"<lost reason text, lowercase>": "<class>"}. Missing reasons
fall back to a small multilingual keyword match, then "other".
Record files: JSON list, an object with a "data" list (raw MCP result), or a
saved tool result wrapper. Several files and globs are allowed.
"""

import argparse
import glob
import json
import math
from datetime import date, datetime

KEYWORDS = {
    "timing": ["timing", "later", "next year", "next quarter", "not now", "postpone", "freeze",
               "momento", "mais tarde", "próximo ano", "später", "plus tard", "más adelante"],
    "budget": ["budget", "orçamento", "presupuesto", "no money", "funding", "cost cut"],
    "competitor": ["competitor", "concorrente", "competencia", "chose", "went with", "lost to"],
    "price": ["price", "expensive", "preço", "caro", "precio", "zu teuer", "cher"],
    "no_decision": ["no decision", "status quo", "internal", "reorg", "sem decisão"],
    "went_silent": ["silent", "no response", "ghost", "unresponsive", "sem resposta", "no answer"],
    "product_gap": ["feature", "missing", "integration", "functionality", "funcionalidade"],
    "bad_fit": ["fit", "spam", "duplicate", "do not contact", "not interested", "wrong", "test"],
}
# Days after loss when each class is usually worth a new conversation: (start, end).
WINDOWS = {
    "timing": (90, 270), "budget": (300, 420), "competitor": (300, 400),
    "no_decision": (120, 365), "went_silent": (90, 365), "price": (180, 400),
    "product_gap": (120, 540), "other": (180, 365),
}


def read_json(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "text" in raw[0]:
        raw = json.loads(raw[0]["text"])  # saved tool result wrapper
    return raw


def load_records(patterns):
    by_id = {}
    for pat in patterns or []:
        for path in sorted(glob.glob(pat)) or [pat]:
            raw = read_json(path)
            if isinstance(raw, dict):
                raw = [raw] if "id" in raw else (raw.get("data") or raw.get("items") or [])
            for rec in raw if isinstance(raw, list) else []:
                if isinstance(rec, dict):
                    rec = rec.get("item", rec)
                    by_id[str(rec.get("id"))] = rec
    return list(by_id.values())


def ref_id(value):
    if isinstance(value, dict):
        return value.get("id") or value.get("value")
    return value


def parse_day(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")[:19]).date()
    except ValueError:
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None


def classify(reason, rmap):
    text = (reason or "").strip().lower()
    if text in rmap:
        return rmap[text]
    if not text:
        return "other"
    for cls, words in KEYWORDS.items():
        if any(w in text for w in words):
            return cls
    return "other"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lost", nargs="+", required=True)
    ap.add_argument("--reason-map")
    ap.add_argument("--persons", nargs="*")
    ap.add_argument("--open", nargs="*")
    ap.add_argument("--orgs", nargs="*")
    ap.add_argument("--min-days", type=int, default=60)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--today")
    ap.add_argument("--out")
    ap.add_argument("--scope-note", default="")
    args = ap.parse_args()
    today = date.fromisoformat(args.today) if args.today else date.today()

    rmap = {}
    if args.reason_map:
        rmap = {k.strip().lower(): v for k, v in read_json(args.reason_map).items()}
    persons = {str(p.get("id")): p for p in load_records(args.persons)}
    open_orgs = {}
    for d in load_records(args.open):
        if (d.get("status") or "open") == "open" and d.get("org_id"):
            open_orgs.setdefault(str(ref_id(d["org_id"])), []).append(d.get("id"))
    orgs = {str(o.get("id")): o for o in load_records(args.orgs)}

    rows, skipped = [], {"bad_fit": 0, "too_recent": 0, "has_open_deal": 0}
    for d in load_records(args.lost):
        if d.get("status") != "lost":
            continue
        lost_on = parse_day(d.get("lost_time") or d.get("close_time"))
        if not lost_on:
            continue
        days = (today - lost_on).days
        cls = classify(d.get("lost_reason"), rmap)
        org = str(ref_id(d.get("org_id")) or "")
        if cls in ("bad_fit", "do_not_contact"):
            skipped["bad_fit"] += 1
            continue
        if org and org in open_orgs:
            skipped["has_open_deal"] += 1
            continue
        if days < args.min_days:
            skipped["too_recent"] += 1
            continue

        triggers, score = [], 0
        start, end = WINDOWS.get(cls, WINDOWS["other"])
        if start <= days <= end:
            triggers.append(f"{cls} window: lost {days}d ago")
            score += 3
        if cls == "competitor" and (330 <= days <= 400 or 695 <= days <= 765):
            triggers.append("competitor contract near its likely anniversary")
            score += 2
        pid = str(ref_id(d.get("person_id")) or "")
        p = persons.get(pid)
        if p and org and str(ref_id(p.get("org_id")) or "") not in ("", org):
            triggers.append("contact now linked to another organization")
            score += 3
        o = orgs.get(org)
        if o:
            touched = parse_day(o.get("update_time"))
            if touched and touched > lost_on and (today - touched).days <= 60:
                triggers.append(f"organization updated {(today - touched).days}d ago")
                score += 1
            if (o.get("people_count") or 0) > 1:
                score += 0.5
        if not triggers:
            continue
        try:
            value = float(d.get("value") or 0)
        except (TypeError, ValueError):
            value = 0.0
        rows.append({"id": d.get("id"), "title": d.get("title") or "", "org_id": org,
                     "person_id": pid, "value": value, "currency": d.get("currency") or "",
                     "lost_reason": d.get("lost_reason") or "", "class": cls, "lost_days": days,
                     "triggers": triggers, "score": round(score * math.log10(value + 10), 2)})
    rows.sort(key=lambda r: r["score"], reverse=True)

    result = {"today": today.isoformat(), "candidates": rows, "skipped": skipped,
              "windows": WINDOWS}
    result["note"] = args.scope_note
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, ensure_ascii=False)
    if args.scope_note:
        print(f"Scope: {args.scope_note}")
    print(f"Candidates {len(rows)} | skipped: bad fit {skipped['bad_fit']}, too recent "
          f"{skipped['too_recent']}, org has open deal {skipped['has_open_deal']}")
    for r in rows[:args.top]:
        print(f"{r['id']} | {r['title'][:40]} | {r['value']:.0f} {r['currency']} | {r['class']} | "
              f"{'; '.join(r['triggers'])}")


if __name__ == "__main__":
    main()
