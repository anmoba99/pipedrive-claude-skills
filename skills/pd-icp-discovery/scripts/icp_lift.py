#!/usr/bin/env python3
"""Find the customer profile that actually wins, then score open deals and leads by fit.

For each attribute (deal source, value band, owner, pipeline, organization
country, size, any deal or organization field you name) computes win rate,
lift vs the account's base win rate, average won value and cycle, with a
minimum sample. Then the strongest two-attribute combinations. Open deals
and leads get a fit score: summed smoothed log-odds of their attributes
(naive Bayes), shown as a 0-100 percentile. Standard library only, no
network, no LLM.

Usage:
  python3 icp_lift.py --closed closed*.json [--orgs orgs*.json]
      [--open open*.json] [--leads leads*.json] [--context account_context.json]
      [--dims origin channel value_band org_country org_size deal:<key> org:<key> ...]
      [--min-n 8] [--top 20]
      [--out icp.json] [--scores-csv fit.csv]

Built-in dims: value_band, owner, pipeline, origin, channel, source,
org_country, org_size, label. deal:<key> and org:<key> read standard or
custom fields by API key. Option IDs are shown as labels when the context
or include_option_labels gives them.
Record files: JSON list, an object with a "data" list (raw MCP result), or a
saved tool result wrapper. Several files and globs are allowed.
"""

import argparse
import csv
import glob
import json
import math
from collections import defaultdict
from datetime import datetime
from itertools import combinations

DEFAULT_DIMS = ["origin", "channel", "source", "value_band", "org_country", "org_size"]


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


def load_labels(path):
    """{field_key: {option_id: label}} plus users {id: name} from the account context."""
    labels, users = defaultdict(dict), {}
    if not path:
        return labels, users, {}
    try:
        ctx = read_json(path)
    except (OSError, ValueError):
        return labels, users, {}
    names = {}
    for ent, fields in (ctx.get("custom_fields") or {}).items():
        prefix = "org" if ent.startswith("org") else ent
        for fd in fields or []:
            names[f"{prefix}:{fd.get('field_code')}"] = fd.get("field_name") or fd.get("name")
            for opt in fd.get("options") or []:
                labels[fd.get("field_code")][str(opt.get("id"))] = opt.get("label")
    raw = ctx.get("users") or {}
    if isinstance(raw, list):
        raw = {u.get("id"): u.get("name") for u in raw if isinstance(u, dict)}
    users = {str(k): v for k, v in raw.items()}
    return labels, users, names


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
        return None


def field(rec, key, labels):
    cf = rec.get("custom_fields")
    val = cf.get(key) if isinstance(cf, dict) and key in cf else rec.get(key)
    if isinstance(val, list):
        val = ",".join(sorted(str(field({"v": v}, "v", labels)) for v in val)) or None
    if isinstance(val, dict):
        val = val.get("label") or val.get("name") or val.get("value") or val.get("id")
    if val in (None, ""):
        return None
    return labels.get(key, {}).get(str(val), val)


def band(x, edges):
    for e in edges:
        if x < e:
            return f"<{e:g}"
    return f"{edges[-1]:g}+"


def amount(rec):
    v = rec.get("value")
    if isinstance(v, dict):
        v = v.get("amount")
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def attrs(rec, orgs, dims, labels, users, value_edges, names=None):
    names = names or {}
    org = orgs.get(str(ref_id(rec.get("org_id") or rec.get("organization_id")) or ""), {})
    out = {}
    for dim in dims:
        if dim == "value_band":
            val = band(amount(rec), value_edges) if amount(rec) else "no value"
        elif dim == "owner":
            oid = str(ref_id(rec.get("owner_id") or rec.get("user_id")) or "")
            val = users.get(oid, oid or None)
        elif dim == "pipeline":
            val = ref_id(rec.get("pipeline_id"))
        elif dim in ("origin", "channel", "label"):
            val = field(rec, dim, labels)
        elif dim == "source":
            val = rec.get("source_name") or field(rec, "source", labels)
        elif dim == "org_country":
            addr = org.get("address")
            val = (addr.get("country") if isinstance(addr, dict) else None) or org.get("address_country")
        elif dim == "org_size":
            n = org.get("people_count")
            val = band(n, [2, 5, 15, 50]) + " contacts" if n else None
        elif dim.startswith("deal:"):
            val = field(rec, dim[5:], labels)
        elif dim.startswith("org:"):
            val = field(org, dim[4:], labels)
        else:
            val = field(rec, dim, labels)
        out[names.get(dim, dim)] = str(val) if val not in (None, "") else "(empty)"
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--closed", nargs="+", required=True)
    ap.add_argument("--orgs", nargs="*")
    ap.add_argument("--open", nargs="*")
    ap.add_argument("--leads", nargs="*")
    ap.add_argument("--context")
    ap.add_argument("--dims", nargs="*")
    ap.add_argument("--min-n", type=int, default=8)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out")
    ap.add_argument("--scores-csv")
    args = ap.parse_args()
    dims = args.dims or DEFAULT_DIMS

    labels, users, names = load_labels(args.context)
    orgs = {str(o.get("id")): o for o in load_records(args.orgs)}
    closed = [d for d in load_records(args.closed) if d.get("status") in ("won", "lost")]
    vals = sorted(amount(d) for d in closed if amount(d))
    edges = sorted({round(vals[int(q * (len(vals) - 1))], -1) or 1 for q in (0.25, 0.5, 0.75)}) if vals else [1]

    rows = [(d, attrs(d, orgs, dims, labels, users, edges, names)) for d in closed]
    won_n = sum(d["status"] == "won" for d, _ in rows)
    base = won_n / len(rows) if rows else 0
    prior = 2  # pseudo-deals pulled toward the base rate

    stats = defaultdict(lambda: {"n": 0, "won": 0, "won_value": 0.0, "cycles": []})
    for d, a in rows:
        won = d["status"] == "won"
        keys = [(k, v) for k, v in a.items()]
        for key in keys + list(combinations(sorted(keys), 2)):
            s = stats[key]
            s["n"] += 1
            if won:
                s["won"] += 1
                s["won_value"] += amount(d)
                start, end = parse_day(d.get("add_time")), parse_day(d.get("won_time") or d.get("close_time"))
                if start and end:
                    s["cycles"].append((end - start).days)

    def seg(key, s):
        rate = (s["won"] + prior * base) / (s["n"] + prior)
        cyc = sorted(s["cycles"])
        return {"segment": " + ".join(f"{k}={v}" for k, v in (key if isinstance(key[0], tuple) else [key])),
                "deals": s["n"], "won": s["won"], "win_rate": round(100 * s["won"] / s["n"]),
                "lift": round(rate / base, 2) if base else None,
                "avg_won_value": round(s["won_value"] / s["won"]) if s["won"] else 0,
                "won_cycle_p50": cyc[len(cyc) // 2] if cyc else None}

    singles = [seg(k, s) for k, s in stats.items() if not isinstance(k[0], tuple) and s["n"] >= args.min_n
               and k[1] != "(empty)"]
    pairs = [seg(k, s) for k, s in stats.items() if isinstance(k[0], tuple) and s["n"] >= args.min_n
             and "(empty)" not in str(k)]
    singles.sort(key=lambda r: r["lift"] or 0, reverse=True)
    pairs.sort(key=lambda r: ((r["lift"] or 0), r["won"]), reverse=True)

    def logodds(a):
        total = 0.0
        for k, v in a.items():
            s = stats.get((k, v))
            if not s or v == "(empty)" or s["n"] < args.min_n:  # same evidence bar as fits/misfits
                continue
            rate = (s["won"] + prior * base) / (s["n"] + prior)
            total += math.log(rate / (1 - rate)) - math.log(base / (1 - base)) if 0 < base < 1 else 0
        return total

    scored = []
    for kind, recs in (("deal", load_records(args.open)), ("lead", load_records(args.leads))):
        for r in recs:
            if kind == "deal" and (r.get("status") or "open") != "open":
                continue
            a = attrs(r, orgs, dims, labels, users, edges, names)
            good = [f"{k}={v}" for k, v in a.items() if stats.get((k, v)) and stats[(k, v)]["n"] >= args.min_n
                    and (stats[(k, v)]["won"] + prior * base) / (stats[(k, v)]["n"] + prior) > base * 1.2]
            bad = [f"{k}={v}" for k, v in a.items() if stats.get((k, v)) and stats[(k, v)]["n"] >= args.min_n
                   and (stats[(k, v)]["won"] + prior * base) / (stats[(k, v)]["n"] + prior) < base * 0.8]
            scored.append({"kind": kind, "id": r.get("id"), "title": r.get("title") or "",
                           "value": amount(r), "logodds": round(logodds(a), 3), "fits": good, "misfits": bad})
    ordered = sorted(s["logodds"] for s in scored)
    for s in scored:
        s["fit"] = round(100 * ordered.index(s["logodds"]) / max(1, len(ordered) - 1)) if ordered else 0
    scored.sort(key=lambda s: (s["fit"], s["value"]), reverse=True)

    result = {"base_win_rate": round(100 * base), "closed": len(rows), "won": won_n,
              "value_edges": edges, "dims": dims, "segments": singles, "pairs": pairs[:30],
              "scored": scored}
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, ensure_ascii=False)
    if args.scores_csv:
        with open(args.scores_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["kind", "id", "title", "value", "fit", "fits", "misfits"])
            for s in scored:
                w.writerow([s["kind"], s["id"], s["title"], s["value"], s["fit"],
                            "; ".join(s["fits"]), "; ".join(s["misfits"])])

    print(f"Closed {len(rows)} | won {won_n} | base win rate {result['base_win_rate']}% | min sample {args.min_n}")
    print("Best segments:")
    for r in [r for r in singles if (r["lift"] or 0) > 1][:8] or [{"segment": "none above base rate", "deals": "-",
                                                                  "win_rate": "-", "lift": "-", "avg_won_value": "-",
                                                                  "won_cycle_p50": "-"}]:
        print(f"- {r['segment']} | {r['deals']} deals | win {r['win_rate']}% | lift {r['lift']} | "
              f"avg won {r['avg_won_value']} | cycle {r['won_cycle_p50']}d")
    print("Best combinations:")
    for r in [r for r in pairs if (r["lift"] or 0) > 1][:5]:
        print(f"- {r['segment']} | {r['deals']} deals | win {r['win_rate']}% | lift {r['lift']}")
    print("Worst segments:")
    for r in sorted((r for r in singles if r["lift"] is not None and r["lift"] < 1), key=lambda r: r["lift"])[:4]:
        print(f"- {r['segment']} | {r['deals']} deals | win {r['win_rate']}% | lift {r['lift']}")
    if scored:
        print(f"Scored {len(scored)} open deals and leads. Top fit:")
        for s in scored[:args.top]:
            print(f"{s['kind']} {s['id']} | {s['title'][:40]} | fit {s['fit']} | {', '.join(s['fits']) or '-'}")


if __name__ == "__main__":
    main()
