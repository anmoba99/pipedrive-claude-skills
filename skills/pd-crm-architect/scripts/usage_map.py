#!/usr/bin/env python3
"""How the team really uses Pipedrive: stages, fields, lost reasons, activity types.

Evidence for a CRM redesign. Per pipeline and stage: open deals and value,
deals lost and won from it, median days open deals sit there. Flags dead
stages (nothing open, nothing lost or won from it), leaky stages (a big
share of all losses), bottlenecks. Custom deal fields: fill rate on the
sample, near-empty fields. Lost reasons: how many distinct values, share of
free text. Activity types: used vs defined. Standard library only, no
network, no LLM.

Usage:
  python3 usage_map.py --deals deals*.json [--activities acts*.json]
      [--context account_context.json] [--today YYYY-MM-DD] [--out usage.json]

Deals: a mix of open, won and lost deals (for example last 12 months).
Context: raw getAccountContext result or .pipedrive/context.json, for stage
order, custom field names and activity types. Record files: JSON list, an
object with a "data" list (raw MCP result), or a saved tool result wrapper.
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


def load_context(path):
    ctx = {}
    if path:
        try:
            ctx = read_json(path)
        except (OSError, ValueError):
            ctx = {}
    stages, pipes = {}, {}
    raw_pipes = ctx.get("pipelines") or []
    for p in raw_pipes if isinstance(raw_pipes, list) else []:
        pipes[str(p.get("id"))] = p.get("name")
        for i, st in enumerate(p.get("stages") or []):  # listed in pipeline order
            stages[str(st.get("id"))] = {"name": st.get("name"), "order": st.get("order_nr") or i + 1,
                                         "pipeline": str(p.get("id"))}
    if isinstance(raw_pipes, dict):
        pipes = {str(k): (v.get("name") if isinstance(v, dict) else v) for k, v in raw_pipes.items()}
    raw_stages = ctx.get("stages") or []
    if isinstance(raw_stages, dict):
        raw_stages = [dict(v, id=k) if isinstance(v, dict) else {"id": k, "name": v}
                      for k, v in raw_stages.items()]
    for st in raw_stages:
        stages.setdefault(str(st.get("id")), {"name": st.get("name"), "order": st.get("order_nr") or 0,
                                              "pipeline": str(st.get("pipeline_id") or "")})
    # The context lists standard fields too; only hash keys are custom fields.
    fields = {fd.get("field_code"): fd.get("field_name") or fd.get("name")
              for fd in (ctx.get("custom_fields") or {}).get("deal") or []
              if is_custom(fd.get("field_code"))}
    types = ctx.get("activity_types") or ctx.get("activityTypes") or []
    types = [t.get("key_string") or t.get("key") or t.get("name") if isinstance(t, dict) else t for t in types]
    return stages, pipes, fields, [t for t in types if t]


def is_custom(key):
    return isinstance(key, str) and len(key) == 40 and all(c in "0123456789abcdef" for c in key)


def filled(v):
    return v not in (None, "", [], {}) and not (isinstance(v, dict) and v.get("value") in (None, ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--deals", nargs="+", required=True)
    ap.add_argument("--activities", nargs="*")
    ap.add_argument("--context")
    ap.add_argument("--today")
    ap.add_argument("--out")
    args = ap.parse_args()
    today = date.fromisoformat(args.today) if args.today else date.today()
    stages, pipes, field_names, act_types = load_context(args.context)

    deals = load_records(args.deals)
    per_stage = defaultdict(lambda: {"open": 0, "open_value": 0.0, "won": 0, "lost": 0, "days": []})
    lost_total = 0
    reasons = Counter()
    no_person = no_org = no_value = 0
    cf_fill = Counter()
    cf_seen = set()
    for d in deals:
        st = str(ref_id(d.get("stage_id")))
        s = per_stage[st]
        status = d.get("status") or "open"
        try:
            val = float(d.get("value") or 0)
        except (TypeError, ValueError):
            val = 0.0
        if status == "open":
            s["open"] += 1
            s["open_value"] += val
            since = parse_day(d.get("stage_change_time") or d.get("add_time"))
            if since:
                s["days"].append((today - since).days)
        elif status == "won":
            s["won"] += 1
        elif status == "lost":
            s["lost"] += 1
            lost_total += 1
            reasons[(d.get("lost_reason") or "").strip() or "(empty)"] += 1
        no_person += not d.get("person_id")
        no_org += not d.get("org_id")
        no_value += not val
        cf = d.get("custom_fields") if isinstance(d.get("custom_fields"), dict) else {}
        keys = {k for k in set(cf) | set(d) if is_custom(k)}
        for k in keys:  # only fields present in the fetched data; absent ones were not requested
            cf_seen.add(k)
            if filled(cf.get(k, d.get(k))):
                cf_fill[k] += 1

    stage_rows = []
    for st, s in per_stage.items():
        meta = stages.get(st, {"name": st, "order": 0, "pipeline": ""})
        days = sorted(s["days"])
        stage_rows.append({"stage_id": st, "stage": meta["name"], "order": meta["order"],
                           "pipeline": pipes.get(meta["pipeline"], meta["pipeline"]),
                           "open": s["open"], "open_value": round(s["open_value"]),
                           "won_from": s["won"], "lost_from": s["lost"],
                           "lost_share": round(100 * s["lost"] / lost_total) if lost_total else 0,
                           "open_days_p50": days[len(days) // 2] if days else None})
    for st, meta in stages.items():
        if st not in per_stage:
            stage_rows.append({"stage_id": st, "stage": meta["name"], "order": meta["order"],
                               "pipeline": pipes.get(meta["pipeline"], meta["pipeline"]), "open": 0,
                               "open_value": 0, "won_from": 0, "lost_from": 0, "lost_share": 0,
                               "open_days_p50": None})
    stage_rows.sort(key=lambda r: (str(r["pipeline"]), r["order"]))
    all_days = sorted(r["open_days_p50"] for r in stage_rows if r["open_days_p50"] is not None)
    slow = all_days[int(0.75 * (len(all_days) - 1))] if all_days else None
    for r in stage_rows:
        r["flags"] = []
        if not r["open"] and not r["lost_from"] and not r["won_from"]:
            r["flags"].append("dead stage")
        if r["lost_share"] >= 35:
            r["flags"].append(f"leaky: {r['lost_share']}% of all losses")
        if slow and r["open_days_p50"] and r["open_days_p50"] >= slow and r["open"] >= 5:
            r["flags"].append(f"bottleneck: open deals sit {r['open_days_p50']}d")

    n = len(deals) or 1
    fields = sorted(({"key": k, "name": field_names.get(k, k), "fill": round(100 * cf_fill[k] / n)}
                     for k in cf_seen), key=lambda f: f["fill"])
    distinct = len(reasons)
    acts = Counter((a.get("type") or "other") for a in load_records(args.activities))
    result = {
        "today": today.isoformat(), "deals": len(deals), "stages": stage_rows,
        "lost_reasons": {"lost": lost_total, "distinct": distinct,
                         "free_text_like": distinct > 15 or (lost_total >= 20 and distinct / lost_total > 0.3),
                         "empty_share": round(100 * reasons.get("(empty)", 0) / lost_total) if lost_total else 0,
                         "top": reasons.most_common(15)},
        "fields": fields, "near_empty_fields": [f for f in fields if f["fill"] < 5],
        "not_fetched": sorted(field_names.get(k, k) for k in set(field_names) - cf_seen),
        "gaps": {"no_person": round(100 * no_person / n), "no_org": round(100 * no_org / n),
                 "no_value": round(100 * no_value / n)},
        "activity_types": {"used": acts.most_common(),
                           "unused": [t for t in act_types if t not in acts] if acts else []},
    }
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, ensure_ascii=False)

    print(f"Deals {len(deals)} | stages {len(stage_rows)} | custom fields {len(fields)} "
          f"({len(result['near_empty_fields'])} under 5% filled"
          f"{', ' + str(len(result['not_fetched'])) + ' not fetched, pass custom_fields' if result['not_fetched'] else ''})")
    for r in stage_rows:
        print(f"{r['pipeline']} | {r['stage']} | open {r['open']} ({r['open_value']}) | won {r['won_from']} "
              f"lost {r['lost_from']} | p50 {str(r['open_days_p50']) + 'd' if r['open_days_p50'] is not None else '-'} | {', '.join(r['flags']) or '-'}")
    lr = result["lost_reasons"]
    print(f"Lost reasons: {lr['distinct']} distinct for {lr['lost']} losses, empty {lr['empty_share']}%"
          f"{' (free text, needs a picklist)' if lr['free_text_like'] else ''}")
    print(f"Gaps: no person {result['gaps']['no_person']}%, no org {result['gaps']['no_org']}%, "
          f"no value {result['gaps']['no_value']}%")
    if acts:
        print("Activity types used: " + ", ".join(f"{t} {c}" for t, c in acts.most_common(8))
              + (f" | unused: {', '.join(result['activity_types']['unused'])}"
                 if result['activity_types']['unused'] else ""))


if __name__ == "__main__":
    main()
