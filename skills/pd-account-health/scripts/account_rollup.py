#!/usr/bin/env python3
"""Account portfolio roll-up: health score, renewals, coverage, whitespace.

Scores every customer organization 0-100 from data the connector returns,
with the same rules every run (no guessing, no LLM). Built for thousands of
accounts: the HTML gets a capped, prioritized list, the CSV gets every row.
Optionally writes writeback.json: score changes to push to an opt-in
organization field after the user confirms. Standard library only, no network.

Usage:
  python3 account_rollup.py --orgs orgs*.json --deals deals*.json
      [--activities acts*.json] [--persons persons*.json]
      [--products deal_products*.json] [--config .pipedrive/config.json]
      [--context account_context.json] [--prev last-portfolio.json]
      [--domain acme] [--today YYYY-MM-DD] [--scope-note "..."]
      [--out portfolio.json] [--csv-out portfolio.csv]
      [--writeback-out writeback.json] [--writeback-max 200]
      [--html portfolio.html --html-out out.html]

Record files: JSON list, an object with a "data" list (raw MCP result), or a
saved tool result wrapper. Several files and globs are allowed; records are
deduplicated by id. Orgs should be fetched with include_fields
people_count, open_deals_count, won_deals_count, next_activity_id.
Deals: won and open deals (any pipeline). Activities: done activities of the
last 180 days. Config "accounts" keys are documented in references/setup.md.
"""

import argparse
import csv
import glob
import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

WEIGHTS = {"touch": 30, "trend": 20, "next_step": 20, "coverage": 20, "breadth": 10}
DRIVER_TEXT = {
    "touch": "Last touch",
    "trend": "Activity trend",
    "next_step": "Next step planned",
    "coverage": "People covered",
    "breadth": "Product breadth",
}
GREEN, AMBER = 70, 40
ACCOUNTS_CAP = 3000
WHITESPACE_MIN_PEERS = 5
WHITESPACE_MIN_RATE = 0.5
RENEWAL_DAYS = 90
NONE = "_none"


def read_json(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "text" in raw[0]:
        raw = json.loads(raw[0]["text"])  # saved tool result wrapper
    return raw


def expand(patterns):
    paths = []
    for pat in patterns or []:
        hits = sorted(glob.glob(pat))
        paths += hits or [pat]
    return paths


def load_records(patterns):
    by_id = {}
    for path in expand(patterns):
        raw = read_json(path)
        if isinstance(raw, dict):
            raw = [raw] if "id" in raw else (raw.get("data") or raw.get("items") or [])
        if isinstance(raw, dict):
            raw = [raw]
        for rec in raw:
            if not isinstance(rec, dict):
                continue
            rec = rec.get("item", rec)
            rid = str(rec.get("id"))
            old = by_id.get(rid)
            if old is None or str(rec.get("update_time") or "") >= str(old.get("update_time") or ""):
                by_id[rid] = rec
    return list(by_id.values())


def load_context(path):
    """Return (org fields {code: field}, person fields, users, pipelines)."""
    fields = {"org": {}, "person": {}, "deal": {}}
    users, pipelines = {}, {}
    if not path:
        return fields, users, pipelines
    try:
        ctx = read_json(path)
    except (OSError, ValueError):
        return fields, users, pipelines
    for ent, key in (("org", "organization"), ("person", "person"), ("deal", "deal")):
        for fd in (ctx.get("custom_fields") or {}).get(key) or []:
            fields[ent][fd.get("field_code")] = fd
    raw_users = ctx.get("users") or ctx.get("companyUsers") or {}
    if isinstance(raw_users, list):
        raw_users = {u.get("id"): u.get("name") for u in raw_users if isinstance(u, dict)}
    users = {str(k): v for k, v in raw_users.items()}
    raw_pipes = ctx.get("pipelines") or {}
    if isinstance(raw_pipes, list):
        raw_pipes = {p.get("id"): p.get("name") for p in raw_pipes if isinstance(p, dict)}
    pipelines = {str(k): (v.get("name") if isinstance(v, dict) else v) for k, v in raw_pipes.items()}
    return fields, users, pipelines


def load_field_map(path, fields):
    """Merge pd-setup field-map.json ({entity: {name: {key, type, options}}}) into fields."""
    if not path:
        return
    try:
        fmap = read_json(path)
    except (OSError, ValueError):
        return
    for ent in ("org", "person", "deal"):
        for name, fd in (fmap.get(ent) or {}).items():
            if not isinstance(fd, dict) or not fd.get("key") or fd["key"] in fields[ent]:
                continue
            opts = [{"id": v, "label": k} for k, v in (fd.get("options") or {}).items()]
            fields[ent][fd["key"]] = {"field_code": fd["key"], "field_name": name.strip(),
                                      "field_type": fd.get("type"), "options": opts}


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


def custom(rec, key):
    if not key:
        return None
    cf = rec.get("custom_fields")
    if isinstance(cf, dict) and key in cf:
        return cf[key]
    return rec.get(key)


def money(value, default_cur=""):
    """(amount, currency) from a money field, a number, or None."""
    if isinstance(value, dict):
        try:
            return float(value.get("value") or 0), value.get("currency") or default_cur
        except (TypeError, ValueError):
            return 0.0, default_cur
    try:
        return (float(value), default_cur) if value not in (None, "") else (0.0, default_cur)
    except (TypeError, ValueError):
        return 0.0, default_cur


def label(value, field):
    """Option label for an option field value, else the value as text."""
    if value in (None, "", []):
        return ""
    if isinstance(value, dict):
        return str(value.get("label") or value.get("value") or "")
    if isinstance(value, list):
        return ", ".join(label(v, field) for v in value if v not in (None, ""))
    for opt in (field or {}).get("options") or []:
        if str(opt.get("id")) == str(value):
            return str(opt.get("label"))
    return str(value)


def clamp(x):
    return max(0.0, min(1.0, x))


def touch_score(days):
    if days is None:
        return 0.0
    if days <= 14:
        return 1.0
    return clamp(1 - (days - 14) / 106.0)  # 0 at 120 days


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--orgs", nargs="*", default=[])
    ap.add_argument("--deals", nargs="*", default=[])
    ap.add_argument("--activities", nargs="*", default=[])
    ap.add_argument("--persons", nargs="*", default=[])
    ap.add_argument("--products", nargs="*", default=[], help="getDealsProducts results")
    ap.add_argument("--config")
    ap.add_argument("--context")
    ap.add_argument("--field-map", help=".pipedrive/field-map.json from pd-setup")
    ap.add_argument("--prev", help="previous portfolio JSON, for score changes")
    ap.add_argument("--domain")
    ap.add_argument("--today")
    ap.add_argument("--scope-note")
    ap.add_argument("--out")
    ap.add_argument("--csv-out")
    ap.add_argument("--writeback-out")
    ap.add_argument("--writeback-max", type=int, default=200)
    ap.add_argument("--html")
    ap.add_argument("--html-out")
    args = ap.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()
    cfg = {}
    if args.config:
        try:
            cfg = read_json(args.config) or {}
        except (OSError, ValueError):
            print("config not readable, using defaults", file=sys.stderr)
    acc = cfg.get("accounts") or {}
    renewal_key = acc.get("renewal_field") or cfg.get("renewal_field")
    weights = dict(WEIGHTS)
    weights.update({k: v for k, v in (acc.get("weights") or {}).items() if k in WEIGHTS})
    fields, users, pipelines = load_context(args.context)
    load_field_map(args.field_map, fields)
    ofields = fields["org"]
    renewal_pipe = str(acc.get("renewal_pipeline_id") or "")
    expansion_pipe = str(acc.get("expansion_pipeline_id") or "")

    orgs = load_records(args.orgs)
    deals = load_records(args.deals)
    acts = load_records(args.activities)
    persons = load_records(args.persons)
    products = load_records(args.products) if args.products else []
    prev = {}
    if args.prev:
        try:
            prev = {str(a["id"]): a for a in (read_json(args.prev).get("all_scores") or [])}
        except (OSError, ValueError, AttributeError):
            prev = {}

    # Deals per org
    won, open_ = defaultdict(list), defaultdict(list)
    deal_org = {}
    for d in deals:
        oid = ref_id(d.get("org_id"))
        if oid is None:
            continue
        oid = str(oid)
        deal_org[str(d.get("id"))] = oid
        st = d.get("status")
        if st == "won":
            won[oid].append(d)
        elif st == "open":
            open_[oid].append(d)

    # People per org
    people = defaultdict(list)
    person_org = {}
    role_key = acc.get("role_field")
    role_field = fields["person"].get(role_key) if role_key else None
    for p in persons:
        oid = ref_id(p.get("org_id"))
        if oid is None:
            continue
        person_org[str(p.get("id"))] = str(oid)
        people[str(oid)].append({"id": p.get("id"), "n": p.get("name") or "",
                                 "role": label(custom(p, role_key), role_field) if role_key else ""})

    # Done activities per org (direct, or through the person or deal)
    last_touch = {}
    cur90, prev90 = Counter(), Counter()
    touched_people = defaultdict(set)
    acts_seen = 0
    for a in acts:
        if a.get("done") is False:
            continue
        day = parse_day(a.get("marked_as_done_time")) or parse_day(a.get("due_date"))
        if not day or day > today:
            continue
        pid = ref_id(a.get("person_id"))
        oid = ref_id(a.get("org_id"))
        oid = str(oid) if oid is not None else person_org.get(str(pid)) or deal_org.get(str(ref_id(a.get("deal_id"))))
        if not oid:
            continue
        acts_seen += 1
        age = (today - day).days
        if oid not in last_touch or day > last_touch[oid]:
            last_touch[oid] = day
        if age <= 90:
            cur90[oid] += 1
            if pid is not None:
                touched_people[oid].add(str(pid))
        elif age <= 180:
            prev90[oid] += 1

    # Products per org from won deals
    org_products = defaultdict(set)
    product_name = {}
    won_ids = {str(d.get("id")) for ds in won.values() for d in ds}
    for li in products:
        did = str(ref_id(li.get("deal_id")))
        if did not in won_ids:
            continue
        pid = str(ref_id(li.get("product_id")) or li.get("name"))
        product_name[pid] = li.get("name") or product_name.get(pid) or "Product " + pid
        org_products[deal_org[did]].add(pid)
    have_products = bool(products)

    # Which orgs are accounts
    tier_key, arr_key, seg_key = acc.get("tier_field"), acc.get("arr_field"), acc.get("segment_field")
    csm_key = acc.get("csm_field")
    health_key, health_date_key = acc.get("health_field"), acc.get("health_date_field")
    rule = acc.get("customer_rule") or "won_or_field"

    def is_account(o):
        oid = str(o.get("id"))
        if won.get(oid) or (o.get("won_deals_count") or 0) > 0:
            return True
        if rule == "won":
            return False
        return any(custom(o, k) not in (None, "", 0, []) for k in (tier_key, arr_key) if k)

    rows = []
    year_ago = today - timedelta(days=365)
    for o in orgs:
        if not is_account(o):
            continue
        oid = str(o.get("id"))
        csm = custom(o, csm_key) if csm_key else o.get("owner_id")
        csm = str(ref_id(csm)) if csm not in (None, "") else NONE
        tier = label(custom(o, tier_key), ofields.get(tier_key)) if tier_key else ""
        seg = label(custom(o, seg_key), ofields.get(seg_key)) if seg_key else ""

        # ARR: mapped field, else won value of the last 12 months
        arr, cur, arr_src = 0.0, "", ""
        if arr_key:
            arr, cur = money(custom(o, arr_key))
            arr_src = "field" if arr else ""
        if not arr:
            by_cur = Counter()
            for d in won[oid]:
                wt = parse_day(d.get("won_time") or d.get("close_time"))
                if wt and wt >= year_ago:
                    by_cur[d.get("currency") or ""] += float(d.get("value") or 0)
            if by_cur:
                cur, arr = by_cur.most_common(1)[0]
                arr_src = "won_12m"

        # Renewal date: field, else open deal in renewal pipeline, else won anniversary
        ren, ren_src = None, ""
        if renewal_key:
            ren = parse_day(ref_id(custom(o, renewal_key)))
            ren_src = "field" if ren else ""
        if not ren and renewal_pipe:
            cands = [parse_day(d.get("expected_close_date")) for d in open_[oid] if str(d.get("pipeline_id")) == renewal_pipe]
            cands = [c for c in cands if c]
            if cands:
                ren, ren_src = min(cands), "renewal_deal"
        if not ren and acc.get("anniversary_renewals", True):
            wins = [parse_day(d.get("won_time") or d.get("close_time")) for d in won[oid]]
            wins = [w for w in wins if w]
            if wins:
                first = min(wins)
                cand = first.replace(year=today.year) if not (first.month == 2 and first.day == 29) else date(today.year, 3, 1)
                if cand < today:
                    cand = cand.replace(year=today.year + 1) if not (cand.month == 2 and cand.day == 29) else date(today.year + 1, 3, 1)
                ren, ren_src = cand, "anniversary"
        ren_days = (ren - today).days if ren else None

        # Drivers
        lt = last_touch.get(oid)
        lt_days = (today - lt).days if lt else None
        drv = {}
        drv["touch"] = touch_score(lt_days)
        c, p = cur90[oid], prev90[oid]
        drv["trend"] = 0.0 if c == 0 else (1.0 if p == 0 else clamp(c / p))
        has_next = bool(o.get("next_activity_id")) or any(d.get("next_activity_id") for d in open_[oid])
        open_count = len(open_[oid]) or (o.get("open_deals_count") or 0)
        drv["next_step"] = 1.0 if has_next else (0.5 if open_count else 0.0)
        ppl = people.get(oid) or []
        pc = len(ppl) or (o.get("people_count") or 0)
        cov = {0: 0.0, 1: 0.4, 2: 0.7}.get(pc, 1.0)
        roles = sorted({x["role"] for x in ppl if x["role"]})
        if role_key and ppl and not roles:
            cov = min(cov, 0.5)
        drv["coverage"] = cov
        if have_products:
            drv["breadth"] = None  # filled after peers are known
        rows.append({
            "id": o.get("id"), "n": o.get("name") or "", "csm": csm, "tier": tier, "seg": seg,
            "arr": round(arr, 2), "cur": cur, "arr_src": arr_src,
            "ren": ren.isoformat() if ren else None, "ren_days": ren_days, "ren_src": ren_src,
            "lt": lt_days, "a90": c, "a_prev": p, "next": has_next, "open": open_count,
            "exp_open": sum(1 for d in open_[oid] if expansion_pipe and str(d.get("pipeline_id")) == expansion_pipe),
            "people": pc, "touched90": len(touched_people[oid]), "roles": roles,
            "products": sorted(org_products[oid]), "drv": drv,
            "old_health": custom(o, health_key) if health_key else None,
        })

    # Peer groups: tier, else segment, else all accounts
    group_by = "tier" if any(r["tier"] for r in rows) else ("seg" if any(r["seg"] for r in rows) else "")
    groups = defaultdict(list)
    for r in rows:
        groups[(r[group_by] if group_by else "") or "All accounts"].append(r)

    whitespace = []
    if have_products:
        for g, members in groups.items():
            sizes = sorted(len(r["products"]) for r in members)
            median = sizes[len(sizes) // 2] if sizes else 0
            for r in members:
                r["drv"]["breadth"] = clamp(len(r["products"]) / median) if median else (1.0 if r["products"] else 0.0)
            if len(members) < WHITESPACE_MIN_PEERS:
                continue
            adoption = Counter(p for r in members for p in r["products"])
            for pid, have in adoption.items():
                rate = have / len(members)
                if rate < WHITESPACE_MIN_RATE or have == len(members):
                    continue
                missing = [r for r in members if pid not in r["products"]]
                missing.sort(key=lambda r: -r["arr"])
                whitespace.append({"product": product_name.get(pid, pid), "group": g, "have": have,
                                   "total": len(members), "missing": [r["id"] for r in missing[:200]],
                                   "missing_count": len(missing)})
        whitespace.sort(key=lambda w: (-w["have"] / w["total"], -w["missing_count"]))

    # Scores
    for r in rows:
        used = {k: weights[k] for k, v in r["drv"].items() if v is not None and weights.get(k)}
        tot = sum(used.values()) or 1
        score = sum(r["drv"][k] * w for k, w in used.items()) / tot * 100
        r["score"] = int(round(score))
        r["bucket"] = "green" if r["score"] >= GREEN else ("amber" if r["score"] >= AMBER else "red")
        reasons = []
        if r["lt"] is None:
            reasons.append("no done activity in 180 days")
        elif r["lt"] > 60:
            reasons.append("last touch %d days ago" % r["lt"])
        if r["a_prev"] >= 3 and r["a90"] < r["a_prev"] * 0.5:
            reasons.append("activity down %d to %d" % (r["a_prev"], r["a90"]))
        if not r["next"]:
            reasons.append("no next step")
        if r["people"] <= 1:
            reasons.append("single-threaded" if r["people"] == 1 else "no people linked")
        if role_key and r["people"] and not r["roles"]:
            reasons.append("no roles set")
        if r["ren_days"] is not None and 0 <= r["ren_days"] <= RENEWAL_DAYS and not r["next"]:
            reasons.append("renewal in %d days, nothing planned" % r["ren_days"])
        r["why"] = reasons
        pv = prev.get(str(r["id"]))
        r["prev_score"] = pv.get("score") if pv else None
        r["drv"] = {k: (round(v, 2) if v is not None else None) for k, v in r["drv"].items()}

    def risk_key(r):
        return (r["bucket"] != "red", r["bucket"] != "amber", -r["arr"], r["score"])

    rows.sort(key=risk_key)

    # Aggregates
    def agg(key):
        out = defaultdict(lambda: {"accounts": 0, "red": 0, "amber": 0, "green": 0, "score_sum": 0,
                                   "arr": Counter(), "arr_risk": Counter(), "ren90": 0, "single": 0})
        for r in rows:
            a = out[r[key] or NONE]
            a["accounts"] += 1
            a[r["bucket"]] += 1
            a["score_sum"] += r["score"]
            a["arr"][r["cur"]] += r["arr"]
            if r["bucket"] != "green":
                a["arr_risk"][r["cur"]] += r["arr"]
            if r["ren_days"] is not None and 0 <= r["ren_days"] <= RENEWAL_DAYS:
                a["ren90"] += 1
            if r["people"] <= 1:
                a["single"] += 1
        res = []
        for k, a in out.items():
            res.append({"id": k, "name": users.get(k, "") if key == "csm" else ("" if k == NONE else k),
                        "accounts": a["accounts"], "red": a["red"], "amber": a["amber"], "green": a["green"],
                        "avg": round(a["score_sum"] / a["accounts"]) if a["accounts"] else None,
                        "arr": {c: round(v, 2) for c, v in a["arr"].items() if v},
                        "arr_risk": {c: round(v, 2) for c, v in a["arr_risk"].items() if v},
                        "ren90": a["ren90"], "single": a["single"]})
        res.sort(key=lambda x: (-(x["red"] + x["amber"]), -x["accounts"]))
        return res

    csms = agg("csm")
    for c in csms:
        if c["id"] == NONE:
            c["name"] = "No owner"
        elif not c["name"]:
            c["name"] = "User " + c["id"]
    tiers = agg("tier") if any(r["tier"] for r in rows) else []

    total_arr, risk_arr = Counter(), Counter()
    for r in rows:
        total_arr[r["cur"]] += r["arr"]
        if r["bucket"] != "green":
            risk_arr[r["cur"]] += r["arr"]
    renewals = [r for r in rows if r["ren_days"] is not None and 0 <= r["ren_days"] <= RENEWAL_DAYS]
    renewals.sort(key=lambda r: (r["ren_days"], r["score"]))
    single = [r for r in rows if r["people"] <= 1]

    kpis = {
        "accounts": len(rows),
        "red": sum(1 for r in rows if r["bucket"] == "red"),
        "amber": sum(1 for r in rows if r["bucket"] == "amber"),
        "green": sum(1 for r in rows if r["bucket"] == "green"),
        "avg": round(sum(r["score"] for r in rows) / len(rows)) if rows else None,
        "arr": {c: round(v, 2) for c, v in total_arr.items() if v},
        "arr_risk": {c: round(v, 2) for c, v in risk_arr.items() if v},
        "renewals_90": len(renewals),
        "renewals_90_risk": sum(1 for r in renewals if r["bucket"] != "green"),
        "single_threaded": len(single),
        "no_touch_90": sum(1 for r in rows if r["lt"] is None or r["lt"] > 90),
    }

    # Write-back proposal: changed accounts only
    writeback = []
    if health_key:
        hf = ofields.get(health_key) or {}
        opts = {str(o.get("label", "")).strip().lower(): o.get("id") for o in hf.get("options") or []}
        for r in rows:
            old = r["old_health"]
            if opts:
                new_val = opts.get(r["bucket"])
                if new_val is None:
                    continue
                old_val = ref_id(old)
                changed = str(old_val) != str(new_val)
            else:
                new_val = r["score"]
                try:
                    changed = old in (None, "") or abs(float(old) - r["score"]) >= 10 or \
                        (float(old) >= GREEN) != (r["score"] >= GREEN) or (float(old) >= AMBER) != (r["score"] >= AMBER)
                except (TypeError, ValueError):
                    changed = True
            if not changed:
                continue
            cf = {health_key: new_val}
            if health_date_key:
                cf[health_date_key] = today.isoformat()
            writeback.append({"id": r["id"], "name": r["n"], "old": old if not isinstance(old, dict) else ref_id(old),
                              "new": new_val, "score": r["score"], "bucket": r["bucket"], "custom_fields": cf,
                              "_arr": r["arr"]})
        writeback.sort(key=lambda w: (w["bucket"] == "green", -w["_arr"]))
        wb_total = len(writeback)
        writeback = writeback[: args.writeback_max]
        for w in writeback:
            w.pop("_arr", None)
    else:
        wb_total = 0

    def slim(r):
        keep = ("id", "n", "csm", "tier", "seg", "arr", "cur", "arr_src", "ren", "ren_days", "ren_src", "lt",
                "a90", "a_prev", "next", "open", "exp_open", "people", "touched90", "roles", "score",
                "prev_score", "bucket", "why", "drv")
        d = {k: r[k] for k in keep}
        d["np"] = len(r["products"])
        return d

    shown = rows[:ACCOUNTS_CAP]
    out = {
        "date": today.isoformat(),
        "domain": args.domain or None,
        "coverage": {"orgs_read": len(orgs), "accounts": len(rows), "deals": len(deals),
                     "activities": acts_seen, "persons": len(persons), "products": have_products,
                     "note": args.scope_note or None, "group_by": group_by or None,
                     "health_field": bool(health_key)},
        "weights": weights,
        "kpis": kpis,
        "csms": csms,
        "tiers": tiers,
        "accounts": [slim(r) for r in shown],
        "accounts_truncated": max(0, len(rows) - len(shown)),
        "renewals": [r["id"] for r in renewals],
        "whitespace": whitespace[:100],
        "writeback": {"count": wb_total, "proposed": len(writeback)},
        "all_scores": [{"id": r["id"], "score": r["score"], "bucket": r["bucket"]} for r in rows],
    }

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
    if args.csv_out:
        with open(args.csv_out, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["org_id", "name", "csm", "tier", "segment", "arr", "currency", "score", "bucket",
                        "last_touch_days", "activities_90d", "next_step", "people", "renewal", "renewal_source", "why"])
            for r in rows:
                w.writerow([r["id"], r["n"], users.get(r["csm"], r["csm"]), r["tier"], r["seg"], r["arr"], r["cur"],
                            r["score"], r["bucket"], "" if r["lt"] is None else r["lt"], r["a90"],
                            "yes" if r["next"] else "no", r["people"], r["ren"] or "", r["ren_src"], "; ".join(r["why"])])
    if args.writeback_out:
        with open(args.writeback_out, "w", encoding="utf-8") as f:
            json.dump({"date": today.isoformat(), "field": health_key, "date_field": health_date_key,
                       "total_changed": wb_total, "updates": writeback}, f, ensure_ascii=False, indent=1)
    if args.html and args.html_out:
        page = open(args.html, encoding="utf-8").read()
        payload = dict(out)
        payload.pop("all_scores", None)
        blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
        with open(args.html_out, "w", encoding="utf-8") as f:
            f.write(page.replace("/*DATA*/", blob, 1))

    print("accounts %d | red %d | amber %d | green %d | renewals 90d %d | single-threaded %d | write-back %d"
          % (len(rows), kpis["red"], kpis["amber"], kpis["green"], len(renewals), len(single), wb_total),
          file=sys.stderr)
    if not args.out and not args.html_out:
        json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
