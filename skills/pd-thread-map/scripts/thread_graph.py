#!/usr/bin/env python3
"""Who we really talk to on each open deal, and people who connect deals.

Per open deal: contacts linked, contacts touched in the last 30 and 90 days,
share of touches going to the main contact, contacts never touched, last
touch per person. Compared with won deals (median contacts touched).
Across deals: people linked to deals at more than one organization, people
whose organization differs from the deal's organization (possible job
change), and past contacts on won deals (alumni) now on open deals or
working at another organization. Standard library only, no network, no LLM.

Usage:
  python3 thread_graph.py --open open*.json --persons persons*.json
      --activities acts*.json [--won won*.json] [--today YYYY-MM-DD]
      [--top 25] [--out threads.json]

Record files: JSON list, an object with a "data" list (raw MCP result), or a
saved tool result wrapper. Several files and globs are allowed; records are
deduplicated by id. Persons: getPersons per deal or per org, with org_id.
A person file may also be a {"<deal_id>": [persons]} map, which links those
persons to that deal. Activities: done activities with deal_id and
person_id or participants.
"""

import argparse
import glob
import json
from collections import Counter, defaultdict
from datetime import date, datetime


def read_json(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "text" in raw[0]:
        raw = json.loads(raw[0]["text"])  # saved tool result wrapper
    return raw


def unwrap(raw):
    if isinstance(raw, dict):
        raw = [raw] if "id" in raw else (raw.get("data") or raw.get("items") or [])
    return [r.get("item", r) for r in raw if isinstance(r, dict)] if isinstance(raw, list) else []


def load_records(patterns):
    by_id = {}
    for pat in patterns or []:
        for path in sorted(glob.glob(pat)) or [pat]:
            for rec in unwrap(read_json(path)):
                by_id[str(rec.get("id"))] = rec
    return list(by_id.values())


def load_persons(patterns):
    """Return (persons by id, {deal_id: set(person_id)} from deal-keyed maps)."""
    persons, linked = {}, defaultdict(set)
    for pat in patterns or []:
        for path in sorted(glob.glob(pat)) or [pat]:
            raw = read_json(path)
            if isinstance(raw, dict) and raw and all(k.isdigit() for k in raw):
                for deal_id, recs in raw.items():
                    for p in unwrap(recs):
                        persons[str(p.get("id"))] = p
                        linked[deal_id].add(str(p.get("id")))
            else:
                for p in unwrap(raw):
                    persons[str(p.get("id"))] = p
    return persons, linked


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


def people_of(act):
    out = set()
    if act.get("person_id"):
        out.add(str(ref_id(act["person_id"])))
    for p in act.get("participants") or []:
        if isinstance(p, dict) and p.get("person_id"):
            out.add(str(p["person_id"]))
    return out


def median(values):
    vals = sorted(values)
    if not vals:
        return None
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--open", nargs="+", required=True)
    ap.add_argument("--persons", nargs="+", required=True)
    ap.add_argument("--activities", nargs="+", required=True)
    ap.add_argument("--won", nargs="*")
    ap.add_argument("--today")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--out")
    args = ap.parse_args()
    today = date.fromisoformat(args.today) if args.today else date.today()

    persons, linked = load_persons(args.persons)
    for p in persons.values():  # persons fetched with a deal filter may carry deal ids
        for key in ("deal_id", "deal_ids"):
            vals = p.get(key)
            for d in vals if isinstance(vals, list) else [vals] if vals else []:
                linked[str(ref_id(d))].add(str(p.get("id")))

    touches = defaultdict(lambda: defaultdict(list))  # deal -> person -> [dates]
    for a in load_records(args.activities):
        if not a.get("deal_id") or not a.get("done", True):
            continue
        day = parse_day(a.get("marked_as_done_time") or a.get("due_date"))
        for pid in people_of(a):
            touches[str(ref_id(a["deal_id"]))][pid].append(day)

    def contacts(deal):
        did = str(deal.get("id"))
        ids = set(linked.get(did, set())) | set(touches.get(did, {}))
        if deal.get("person_id"):
            ids.add(str(ref_id(deal["person_id"])))
        return ids

    won = [d for d in load_records(args.won) if d.get("status") == "won"]
    won_touched = [len(touches.get(str(d.get("id")), {})) for d in won if touches.get(str(d.get("id")))]
    won_p50 = median(won_touched)

    rows = []
    person_deals = defaultdict(set)
    for d in load_records(args.open):
        if (d.get("status") or "open") != "open":
            continue
        did = str(d.get("id"))
        org = str(ref_id(d.get("org_id")) or "")
        ids = contacts(d)
        tp = touches.get(did, {})
        counts = {pid: len(v) for pid, v in tp.items()}
        total = sum(counts.values())
        last = {pid: max(filter(None, v), default=None) for pid, v in tp.items()}
        t30 = [pid for pid, day in last.items() if day and (today - day).days <= 30]
        t90 = [pid for pid, day in last.items() if day and (today - day).days <= 90]
        main_share = round(100 * max(counts.values()) / total) if total else None
        never = [pid for pid in ids if pid not in tp]
        moved = [pid for pid in ids if persons.get(pid) and org
                 and str(ref_id(persons[pid].get("org_id")) or "") not in ("", org)]
        for pid in ids:
            person_deals[pid].add(did)
        flags = []
        if len(t90) <= 1:
            flags.append("single-threaded" if ids else "no contact")
        if main_share is not None and main_share >= 80 and len(ids) > 1:
            flags.append(f"{main_share}% of touches to one person")
        if won_p50 and len(t90) < won_p50:
            flags.append(f"{len(t90)} contacts active in 90d, wins had {won_p50:g}")
        if ids and not t30:
            flags.append("nobody touched in 30d")
        if moved:
            flags.append(f"{len(moved)} contact(s) now at another org")
        try:
            value = float(d.get("value") or 0)
        except (TypeError, ValueError):
            value = 0.0
        rows.append({
            "id": d.get("id"), "title": d.get("title") or "", "org_id": org, "value": value,
            "currency": d.get("currency") or "", "contacts": len(ids), "active_90d": len(t90),
            "active_30d": len(t30), "main_share": main_share, "flags": flags,
            "people": [{"id": pid, "name": (persons.get(pid) or {}).get("name") or pid,
                        "touches": counts.get(pid, 0),
                        "last_touch": last[pid].isoformat() if last.get(pid) else None,
                        "org_id": str(ref_id((persons.get(pid) or {}).get("org_id")) or ""),
                        "moved": pid in moved, "never_touched": pid in never}
                       for pid in sorted(ids, key=lambda x: -counts.get(x, 0))],
        })
    rows.sort(key=lambda r: (len(r["flags"]), r["value"]), reverse=True)

    # Alumni: people on won deals, and where they are now.
    alumni = []
    for d in won:
        org = str(ref_id(d.get("org_id")) or "")
        for pid in contacts(d):
            p = persons.get(pid)
            if not p:
                continue
            now_org = str(ref_id(p.get("org_id")) or "")
            on_open = sorted(person_deals.get(pid, set()))
            if (now_org and org and now_org != org) or on_open:
                alumni.append({"person_id": pid, "name": p.get("name"), "won_deal": d.get("id"),
                               "won_org": org, "now_org": now_org, "on_open_deals": on_open})
    bridges = [{"person_id": pid, "name": (persons.get(pid) or {}).get("name"), "open_deals": sorted(ds)}
               for pid, ds in person_deals.items() if len(ds) > 1]

    result = {"today": today.isoformat(), "won_contacts_p50": won_p50, "deals": rows,
              "alumni": alumni, "bridges": bridges}
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, ensure_ascii=False)

    flagged = [r for r in rows if r["flags"]]
    print(f"Open deals {len(rows)} | flagged {len(flagged)} | single-threaded "
          f"{sum('single-threaded' in r['flags'] for r in rows)} | won deals touched p50 contacts {won_p50}")
    for r in flagged[:args.top]:
        print(f"{r['id']} | {r['title'][:40]} | {r['value']:.0f} {r['currency']} | contacts {r['contacts']} "
              f"active90 {r['active_90d']} | {'; '.join(r['flags'])}")
    print(f"Alumni signals {len(alumni)} | people on 2+ open deals {len(bridges)}")


if __name__ == "__main__":
    main()
