#!/usr/bin/env python3
"""Match open deals to the closed deals they look like, and flag how they die.

For every open deal, finds the most similar closed deals in the same
pipeline (stage position, value, age, time in stage, idle time, activity
pace, next step, unanswered email) and reports the share that were lost,
the lost reasons among them, and rule-based death signals. Closed deals are
described as they were when they closed, so "looks like a lost deal" means
"looks like a deal shortly before it was marked lost". Standard library
only, no network, no LLM.

Usage:
  python3 deal_match.py --open open*.json --closed closed*.json
      [--activities acts*.json] [--context account_context.json]
      [--k 7] [--stale-days 14] [--top 25] [--today YYYY-MM-DD]
      [--out premortem.json]

Record files: JSON list, an object with a "data" list (raw MCP result), or
a saved tool result wrapper. Several files and globs are allowed; records
are deduplicated by id. Deals should be fetched with include_fields
next_activity_id, last_activity_id, last_incoming_mail_time,
last_outgoing_mail_time. Activities: done activities with deal_id
(optional, improves the pace signal).
"""

import argparse
import glob
import json
import math
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


def load_stages(path):
    """{stage_id: (order_nr, name)} from getAccountContext or .pipedrive/context.json."""
    if not path:
        return {}
    try:
        ctx = read_json(path)
    except (OSError, ValueError):
        return {}
    out = {}
    raw = ctx.get("stages") or []
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, dict):
                out[str(k)] = (v.get("order_nr") or 0, v.get("name") or str(k))
            else:
                out[str(k)] = (0, v)
    for st in raw if isinstance(raw, list) else []:
        out[str(st.get("id"))] = (st.get("order_nr") or 0, st.get("name") or str(st.get("id")))
    for pipe in ctx.get("pipelines") or []:
        if isinstance(pipe, dict):
            for i, st in enumerate(pipe.get("stages") or []):  # listed in pipeline order
                out[str(st.get("id"))] = (st.get("order_nr") or i + 1, st.get("name") or str(st.get("id")))
    return out


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


def pct(values, q):
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    return vals[min(len(vals) - 1, int(round(q * (len(vals) - 1))))]


def features(deal, today, acts_by_deal, stages):
    status = deal.get("status") or "open"
    end = today
    if status == "won":
        end = parse_day(deal.get("won_time") or deal.get("close_time")) or today
    elif status == "lost":
        end = parse_day(deal.get("lost_time") or deal.get("close_time")) or today
    added = parse_day(deal.get("add_time")) or end
    in_stage = parse_day(deal.get("stage_change_time")) or added
    last_touch = max(filter(None, [parse_day(deal.get("last_activity_date")),
                                   parse_day(deal.get("update_time")) if status == "open" else None,
                                   in_stage]), default=added)
    acts = acts_by_deal.get(str(deal.get("id")), [])
    recent = sum(1 for d in acts if d and 0 <= (end - d).days <= 30)
    out_mail = parse_day(deal.get("last_outgoing_mail_time"))
    in_mail = parse_day(deal.get("last_incoming_mail_time"))
    unanswered = bool(out_mail and (not in_mail or (out_mail - in_mail).days > 7))
    stage = str(ref_id(deal.get("stage_id")))
    try:
        value = float(deal.get("value") or 0)
    except (TypeError, ValueError):
        value = 0.0
    return {
        "id": deal.get("id"),
        "title": deal.get("title") or "",
        "status": status,
        "pipeline": str(ref_id(deal.get("pipeline_id"))),
        "stage": stage,
        "stage_order": stages.get(stage, (0, stage))[0],
        "stage_name": stages.get(stage, (0, stage))[1],
        "owner": str(ref_id(deal.get("owner_id") or deal.get("user_id"))),
        "value": value,
        "currency": deal.get("currency") or "",
        "age": max(0, (end - added).days),
        "in_stage": max(0, (end - in_stage).days),
        "idle": max(0, (end - last_touch).days),
        "acts_30": recent if acts_by_deal else None,
        "next_step": bool(deal.get("next_activity_id") or deal.get("next_activity_date")),
        "unanswered": unanswered,
        "close_passed": status == "open" and bool(parse_day(deal.get("expected_close_date")))
        and parse_day(deal.get("expected_close_date")) < today,
        "lost_reason": (deal.get("lost_reason") or "").strip(),
    }


def distance(a, b, span):
    d = abs(a["stage_order"] - b["stage_order"]) / span["stage"]
    d += abs(math.log1p(a["value"]) - math.log1p(b["value"])) / span["value"]
    for key in ("age", "in_stage", "idle"):
        d += abs(math.log1p(a[key]) - math.log1p(b[key])) / span[key]
    if a["acts_30"] is not None and b["acts_30"] is not None:
        d += abs(math.log1p(a["acts_30"]) - math.log1p(b["acts_30"])) / span["acts_30"]
    d += 0.5 * (a["next_step"] != b["next_step"]) + 0.5 * (a["unanswered"] != b["unanswered"])
    d += 0.25 * (a["owner"] != b["owner"])
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--open", nargs="+", required=True)
    ap.add_argument("--closed", nargs="+", required=True)
    ap.add_argument("--activities", nargs="*")
    ap.add_argument("--context")
    ap.add_argument("--k", type=int, default=7)
    ap.add_argument("--stale-days", type=int, default=14)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--today")
    ap.add_argument("--out")
    args = ap.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()
    stages = load_stages(args.context)
    acts_by_deal = defaultdict(list)
    for act in load_records(args.activities):
        if act.get("deal_id") and act.get("done", True):
            acts_by_deal[str(ref_id(act["deal_id"]))].append(
                parse_day(act.get("marked_as_done_time") or act.get("due_date")))

    open_f = [features(d, today, acts_by_deal, stages) for d in load_records(args.open)
              if (d.get("status") or "open") == "open"]
    closed_f = [features(d, today, acts_by_deal, stages) for d in load_records(args.closed)
                if d.get("status") in ("won", "lost")]
    if not open_f or not closed_f:
        sys.exit("Need at least one open and one closed (won or lost) deal.")

    allf = open_f + closed_f
    span = {"stage": max(1, max(f["stage_order"] for f in allf) - min(f["stage_order"] for f in allf))}
    for key in ("value", "age", "in_stage", "idle", "acts_30"):
        vals = [math.log1p(f[key]) for f in allf if f[key] is not None]
        span[key] = max(0.5, (pct(vals, 0.9) or 1) - (pct(vals, 0.1) or 0))

    won = [f for f in closed_f if f["status"] == "won"]
    lost = [f for f in closed_f if f["status"] == "lost"]
    won_cycle_p75 = pct([f["age"] for f in won], 0.75)
    lost_stage_days = defaultdict(list)
    for f in lost:
        lost_stage_days[f["stage"]].append(f["in_stage"])
    won_pace = pct([f["acts_30"] for f in won if f["acts_30"] is not None], 0.5)
    base_lost = len(lost) / len(closed_f)

    by_pipe = defaultdict(list)
    for f in closed_f:
        by_pipe[f["pipeline"]].append(f)

    rows = []
    for f in open_f:
        pool = by_pipe.get(f["pipeline"]) or closed_f
        near = sorted(pool, key=lambda c: distance(f, c, span))[:args.k]
        weights = [1 / (0.1 + distance(f, c, span)) for c in near]
        lost_w = sum(w for c, w in zip(near, weights) if c["status"] == "lost")
        risk = round(100 * lost_w / sum(weights)) if weights else 0
        reasons = Counter(c["lost_reason"] or "(no reason)" for c in near if c["status"] == "lost")
        flags = []
        p50 = pct(lost_stage_days.get(f["stage"], []), 0.5)
        if p50 is not None and f["in_stage"] >= p50 and len(lost_stage_days[f["stage"]]) >= 3:
            flags.append(f"{f['in_stage']}d in stage, lost deals died here at {p50}d")
        if won_cycle_p75 and f["age"] > won_cycle_p75:
            flags.append(f"age {f['age']}d, 75% of wins closed by {won_cycle_p75}d")
        if f["idle"] >= args.stale_days:
            flags.append(f"idle {f['idle']}d")
        if not f["next_step"]:
            flags.append("no next step")
        if f["unanswered"]:
            flags.append("our last email unanswered 7d+")
        if f["close_passed"]:
            flags.append("expected close date passed")
        if won_pace and f["acts_30"] is not None and f["acts_30"] < won_pace / 2:
            flags.append(f"{f['acts_30']} activities in 30d, wins had {won_pace}")
        rows.append({
            "id": f["id"], "title": f["title"], "stage": f["stage_name"], "owner": f["owner"],
            "value": f["value"], "currency": f["currency"], "risk": risk, "flags": flags,
            "likely_reason": reasons.most_common(1)[0][0] if reasons else None,
            "neighbors": [{"id": c["id"], "title": c["title"], "status": c["status"],
                           "lost_reason": c["lost_reason"], "died_in": c["stage_name"]}
                          for c in near],
        })

    rows.sort(key=lambda r: (r["risk"] + 5 * len(r["flags"])) * math.log1p(r["value"] + 1),
              reverse=True)
    result = {
        "today": today.isoformat(),
        "method": f"k={args.k} nearest closed deals in the same pipeline, weighted by similarity",
        "baseline": {"closed": len(closed_f), "won": len(won), "lost": len(lost),
                     "lost_share": round(100 * base_lost), "won_cycle_p75": won_cycle_p75,
                     "won_activities_30d_p50": won_pace,
                     "lost_days_in_stage_p50": {stages.get(s, (0, s))[1]: pct(v, 0.5)
                                                for s, v in lost_stage_days.items()}},
        "deals": rows,
    }
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, ensure_ascii=False)

    print(f"Open {len(open_f)} vs closed {len(closed_f)} (won {len(won)}, lost {len(lost)}, "
          f"baseline lost {result['baseline']['lost_share']}%)")
    for r in rows[:args.top]:
        print(f"{r['id']} | {r['title'][:40]} | {r['stage']} | {r['value']:.0f} {r['currency']} | "
              f"risk {r['risk']}% | {r['likely_reason'] or '-'} | {'; '.join(r['flags']) or '-'}")


if __name__ == "__main__":
    main()
