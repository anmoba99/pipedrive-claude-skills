#!/usr/bin/env python3
"""Mine the activity paths of won and lost deals into a playbook, then audit open deals.

Per closed deal: activity types in order, days from creation to first touch,
gaps between touches, distinct contacts touched, cycle length. Compares won
vs lost: which activity types appear far more often in wins (lift), the most
common opening sequences, first touch speed, longest gap. Optional audit:
for each open deal, which playbook steps are missing or overdue. Standard
library only, no network, no LLM.

Usage:
  python3 won_paths.py --closed closed*.json --activities acts*.json
      [--open open*.json] [--min-support 0.2] [--today YYYY-MM-DD]
      [--out playbook.json] [--audit-csv audit.csv]

Record files: JSON list, an object with a "data" list (raw MCP result), or a
saved tool result wrapper. Several files and globs are allowed; records are
deduplicated by id. Activities: done activities with deal_id, type,
marked_as_done_time or due_date, person_id or participants.
"""

import argparse
import csv
import glob
import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime


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


def median(values):
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else round((vals[mid - 1] + vals[mid]) / 2, 1)


def collapse(types):
    """Drop immediate repeats: call, call, email -> call, email."""
    out = []
    for t in types:
        if not out or out[-1] != t:
            out.append(t)
    return out


def path_of(deal, acts, today):
    status = deal.get("status") or "open"
    end = today
    if status in ("won", "lost"):
        end = parse_day(deal.get(f"{status}_time") or deal.get("close_time")) or today
    added = parse_day(deal.get("add_time")) or end
    dated = sorted(((d, a) for a in acts for d in [parse_day(a.get("marked_as_done_time") or a.get("due_date"))]
                    if d and d <= end), key=lambda x: x[0])
    days = [d for d, _ in dated]
    gaps = [(b - a).days for a, b in zip(days, days[1:])]
    people = set()
    for _, a in dated:
        if a.get("person_id"):
            people.add(str(ref_id(a["person_id"])))
        for p in a.get("participants") or []:
            if isinstance(p, dict) and p.get("person_id"):
                people.add(str(p["person_id"]))
    return {
        "id": deal.get("id"), "title": deal.get("title") or "", "status": status,
        "types": collapse([(a.get("type") or "other") for _, a in dated]),
        "type_set": {(a.get("type") or "other") for _, a in dated},
        "first_touch": (days[0] - added).days if days else None,
        "max_gap": max(gaps) if gaps else None,
        "since_last": (end - days[-1]).days if days else (end - added).days,
        "touches": len(days), "people": len(people),
        "cycle": (end - added).days,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--closed", nargs="+", required=True)
    ap.add_argument("--activities", nargs="+", required=True)
    ap.add_argument("--open", nargs="*")
    ap.add_argument("--min-support", type=float, default=0.2)
    ap.add_argument("--today")
    ap.add_argument("--out")
    ap.add_argument("--audit-csv")
    args = ap.parse_args()
    today = date.fromisoformat(args.today) if args.today else date.today()

    acts = defaultdict(list)
    for a in load_records(args.activities):
        if a.get("deal_id") and a.get("done", True):
            acts[str(ref_id(a["deal_id"]))].append(a)

    paths = [path_of(d, acts.get(str(d.get("id")), []), today) for d in load_records(args.closed)
             if d.get("status") in ("won", "lost")]
    won = [p for p in paths if p["status"] == "won" and p["touches"]]
    lost = [p for p in paths if p["status"] == "lost" and p["touches"]]
    if len(won) < 5:
        sys.exit(f"Only {len(won)} won deals with activities. Need 5+ for a playbook.")

    # Activity types that separate wins from losses.
    steps = []
    for t in sorted({t for p in won + lost for t in p["type_set"]}):
        w = sum(t in p["type_set"] for p in won) / len(won)
        l = sum(t in p["type_set"] for p in lost) / len(lost) if lost else 0
        if w >= args.min_support:
            steps.append({"type": t, "in_won": round(100 * w), "in_lost": round(100 * l),
                          "lift": round(w / l, 2) if l else None,
                          "median_count_won": median([sum(1 for x in p["types"] if x == t) for p in won
                                                      if t in p["type_set"]])})
    steps.sort(key=lambda s: (s["lift"] or 99, s["in_won"]), reverse=True)

    # Typical position of each step in won paths (median rank of first occurrence).
    order = {}
    for s in steps:
        ranks = [p["types"].index(s["type"]) / max(1, len(p["types"]) - 1)
                 for p in won if s["type"] in p["types"]]
        order[s["type"]] = median(ranks)
    sequence = sorted(order, key=lambda t: order[t] if order[t] is not None else 1)

    def openings(group):
        c = Counter(" > ".join(p["types"][:3]) for p in group if len(p["types"]) >= 2)
        return [{"path": k, "share": round(100 * v / len(group))} for k, v in c.most_common(5)]

    timing = {}
    for name, group in (("won", won), ("lost", lost)):
        timing[name] = {
            "deals": len(group),
            "first_touch_days_p50": median([p["first_touch"] for p in group]),
            "max_gap_days_p50": median([p["max_gap"] for p in group]),
            "touches_p50": median([p["touches"] for p in group]),
            "people_p50": median([p["people"] for p in group]),
            "cycle_days_p50": median([p["cycle"] for p in group]),
        }
    gap_limit = timing["won"]["max_gap_days_p50"]

    audit = []
    for d in load_records(args.open):
        if (d.get("status") or "open") != "open":
            continue
        p = path_of(d, acts.get(str(d.get("id")), []), today)
        missing = [t for t in sequence if t not in p["type_set"]
                   and (next(s for s in steps if s["type"] == t)["lift"] or 2) >= 1.5]
        gaps = []
        if gap_limit is not None and p["since_last"] > gap_limit:
            gaps.append(f"{p['since_last']}d since last touch, wins rarely went {gap_limit}d")
        wp = timing["won"]["people_p50"]
        if wp and p["people"] < wp:
            gaps.append(f"{p['people']} contacts touched, wins had {wp}")
        if missing or gaps:
            audit.append({"id": p["id"], "title": p["title"], "missing_steps": missing,
                          "gaps": gaps, "path": " > ".join(p["types"][-6:])})
    audit.sort(key=lambda r: len(r["missing_steps"]) + len(r["gaps"]), reverse=True)

    result = {"today": today.isoformat(), "timing": timing, "steps": steps,
              "sequence_won": sequence, "openings_won": openings(won),
              "openings_lost": openings(lost), "audit": audit}
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, ensure_ascii=False)
    if args.audit_csv:
        with open(args.audit_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["deal_id", "title", "missing_steps", "gaps", "recent_path"])
            for r in audit:
                w.writerow([r["id"], r["title"], "; ".join(r["missing_steps"]),
                            "; ".join(r["gaps"]), r["path"]])

    tw, tl = timing["won"], timing["lost"]
    print(f"Won {tw['deals']} vs lost {tl['deals']} deals with activities")
    print(f"First touch p50: won {tw['first_touch_days_p50']}d, lost {tl['first_touch_days_p50']}d | "
          f"longest gap p50: won {tw['max_gap_days_p50']}d, lost {tl['max_gap_days_p50']}d | "
          f"contacts p50: won {tw['people_p50']}, lost {tl['people_p50']}")
    print("Won sequence: " + " > ".join(sequence))
    for s in steps[:8]:
        lift = f"lift {s['lift']}" if s["lift"] is not None else "only in wins"
        print(f"- {s['type']}: in {s['in_won']}% of wins vs {s['in_lost']}% of losses ({lift})")
    if args.open is not None:
        print(f"Open deals off playbook: {len(audit)}")
        for r in audit[:10]:
            print(f"{r['id']} | {r['title'][:40]} | missing {', '.join(r['missing_steps']) or '-'} | "
                  f"{'; '.join(r['gaps']) or '-'}")


if __name__ == "__main__":
    main()
