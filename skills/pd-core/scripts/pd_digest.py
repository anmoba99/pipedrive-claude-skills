#!/usr/bin/env python3
"""Compact digest of Pipedrive deals.

Turns a saved getDeals result into a short summary: totals per currency,
counts per stage or owner, and a flagged list (stale, no next step,
close date passed, big deals). Standard library only, no network.

Usage:
  python3 pd_digest.py deals.json [--context .pipedrive/context.json]
      [--stale-days 14] [--group stage|owner] [--top 20] [--today YYYY-MM-DD]

Input: a JSON list of deals, or an object with a "data" list (raw MCP result).
Context (optional): {"stages": {"<id>": "<name>"}, "users": {"<id>": "<name>"}}
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import date, datetime


def load_deals(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        raw = raw.get("data") or raw.get("items") or []
    return [d.get("item", d) if isinstance(d, dict) else d for d in raw]


def load_context(path):
    if not path:
        return {}, {}
    try:
        with open(path, encoding="utf-8") as f:
            ctx = json.load(f)
    except (OSError, ValueError):
        return {}, {}
    stages = {str(k): v for k, v in (ctx.get("stages") or {}).items()}
    users = {str(k): v for k, v in (ctx.get("users") or {}).items()}
    return stages, users


def ref_id(value):
    """Pipedrive returns ids either as ints or as {"id": ..., "name": ...}."""
    if isinstance(value, dict):
        return value.get("id"), value.get("name")
    return value, None


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


def money(amount, currency):
    return f"{currency} {amount:,.0f}"


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("deals")
    p.add_argument("--context")
    p.add_argument("--stale-days", type=int, default=14)
    p.add_argument("--group", choices=["stage", "owner"], default="stage")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--today")
    args = p.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()
    deals = load_deals(args.deals)
    stages, users = load_context(args.context)
    if not deals:
        print("SUMMARY deals=0")
        return

    totals = defaultdict(float)
    groups = defaultdict(lambda: [0, defaultdict(float)])
    rows = []
    for d in deals:
        value = float(d.get("value") or 0)
        currency = d.get("currency") or "?"
        stage_id, _ = ref_id(d.get("stage_id"))
        owner_id, owner_name = ref_id(d.get("owner_id") or d.get("user_id"))
        stage = stages.get(str(stage_id), str(stage_id))
        owner = owner_name or users.get(str(owner_id), str(owner_id))

        updated = parse_day(d.get("update_time"))
        idle = (today - updated).days if updated else None
        close = parse_day(d.get("expected_close_date"))

        flags = []
        if idle is not None and idle >= args.stale_days:
            flags.append("STALE")
        has_next_key = "next_activity_id" in d or "undone_activities_count" in d
        if has_next_key and not d.get("next_activity_id") and not d.get("undone_activities_count"):
            flags.append("NO_NEXT")
        if close and close < today and d.get("status", "open") == "open":
            flags.append("CLOSE_PASSED")

        totals[currency] += value
        key = stage if args.group == "stage" else owner
        groups[key][0] += 1
        groups[key][1][currency] += value
        rows.append({
            "id": d.get("id"), "title": (d.get("title") or "")[:40],
            "stage": stage, "owner": owner, "value": value,
            "currency": currency, "idle": idle, "flags": flags,
        })

    values = sorted(r["value"] for r in rows)
    big_cut = values[int(len(values) * 0.8)] if len(values) >= 5 else None
    for r in rows:
        if big_cut and r["value"] >= big_cut and r["value"] > 0:
            r["flags"].append("BIG")

    def count(flag):
        return sum(flag in r["flags"] for r in rows)

    total_txt = ", ".join(money(v, c) for c, v in sorted(totals.items()))
    print(f"SUMMARY deals={len(rows)} value={total_txt} stale={count('STALE')} "
          f"no_next={count('NO_NEXT')} close_passed={count('CLOSE_PASSED')} "
          f"(today={today}, stale>={args.stale_days}d)")

    print(f"BY {args.group}:")
    for key, (n, vals) in sorted(groups.items(), key=lambda kv: -kv[1][0]):
        vtxt = ", ".join(money(v, c) for c, v in sorted(vals.items()))
        print(f"  {key}: {n} | {vtxt}")

    risky = [r for r in rows if set(r["flags"]) - {"BIG"}]
    risky.sort(key=lambda r: (-len(r["flags"]), -r["value"]))
    print(f"FLAGGED {len(risky)} (top {min(args.top, len(risky))}):")
    print("  id | title | stage | value | owner | idle_d | flags")
    for r in risky[: args.top]:
        idle = "-" if r["idle"] is None else r["idle"]
        print(f"  {r['id']} | {r['title']} | {r['stage']} | "
              f"{money(r['value'], r['currency'])} | {r['owner']} | {idle} | "
              f"{','.join(r['flags'])}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as e:
        print(f"ERROR {e}", file=sys.stderr)
        sys.exit(1)
