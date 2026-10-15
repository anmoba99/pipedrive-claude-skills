#!/usr/bin/env python3
"""Field completeness and record issues for the data health tracker.

Built for accounts of any size. Field fill rates come from a sample (for
example the 1,000 most recently updated records per item). Record issues
come from the scope (for example every open deal). A snapshot keeps a
compact copy of every record seen, so later runs only fetch what changed
(updated_since) and merge. Writes one JSON for the tracker, a summary for
the next run's trend, a full fix list CSV, and optionally the tracker HTML.
Standard library only, no network.

Usage:
  python3 field_health.py
      [--deals f1.json f2.json ...] [--persons ...] [--orgs ...]
      [--sample-deals ...] [--sample-persons ...] [--sample-orgs ...]
      [--context account_context.json]
      [--dupes-person dupes_p.csv] [--dupes-org dupes_o.csv]
      [--snapshot snapshot.json] [--snapshot-out snapshot.json]
      [--prev last-summary.json] [--scope-note "open deals, ..."]
      [--domain acme] [--threshold 0.5] [--stale-days 90] [--today YYYY-MM-DD]
      [--out data.json] [--summary-out summary.json] [--fixlist-out fixlist.csv]
      [--html tracker.html --html-out out.html]

Record files: JSON list, an object with a "data" list (raw MCP result), or
a saved tool result wrapper. Several files and globs are allowed; records
are deduplicated by id, keeping the latest update_time. Without --sample-*
files, field fill rates use the scope records.
Context: raw getAccountContext result or .pipedrive/context.json. Optional.
Duplicates: CSV from find_dupes.py (id_a,id_b,name_a,name_b,reason,score).
"""

import argparse
import csv
import glob
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime

ENTITIES = ("deal", "person", "org")
ARG = {"deal": "deals", "person": "persons", "org": "orgs"}
CONTEXT_KEYS = {"deal": "deal", "person": "person", "org": "organization"}
STANDARD = {
    "deal": {"value": "Value", "expected_close_date": "Expected close date",
             "person_id": "Contact person", "org_id": "Organization",
             "label_ids": "Labels"},
    "person": {"emails": "Email", "phones": "Phone", "org_id": "Organization",
               "label_ids": "Labels"},
    "org": {"address": "Address", "website": "Website", "industry": "Industry",
            "employee_count": "Employees", "label_ids": "Labels"},
}
ISSUE_TEXT = {
    "no_next_step": ("No next activity", "Schedule next activity"),
    "no_close_date": ("No expected close date", "Set expected close date"),
    "no_value": ("No deal value", "Add value or products"),
    "stale": ("Idle {days} days", "Revive or close as lost"),
    "no_contact": ("No email or phone", "Add email or phone"),
    "no_org": ("No organization", "Link an organization"),
    "owner_only": ("Visible to owner only", "Check visibility if the team needs it"),
}
# How to fix each issue in bulk with native Pipedrive tools.
RECIPES = {
    "no_next_step": {
        "where": "Deals list view",
        "filter": "Status is open AND Next activity date is empty",
        "action": "Save the filter, share it, and have each owner schedule a next activity from the list. A Pipedrive automation can also create an activity when a deal enters a stage."},
    "no_close_date": {
        "where": "Deals list view",
        "filter": "Status is open AND Expected close date is empty",
        "action": "Select the deals per owner or stage and use bulk edit to set Expected close date."},
    "no_value": {
        "where": "Deals list view",
        "filter": "Status is open AND Value is empty",
        "action": "Add products or values, starting with the latest stages. Consider making Value required in those stages."},
    "stale": {
        "where": "Deals list view",
        "filter": "Status is open AND Update time is more than {stale} days ago",
        "action": "Review per owner: revive with an activity, or select and bulk edit Status to lost with a lost reason."},
    "no_contact": {
        "where": "People list view",
        "filter": "Email is empty AND Phone is empty",
        "action": "Enrich the ones linked to open deals first. Remove the rest after review."},
    "no_org": {
        "where": "People list view",
        "filter": "Organization is empty",
        "action": "Select people from the same company and use bulk edit to set Organization."},
    "owner_only": {
        "where": "Deals, People or Organizations list view",
        "filter": "Visible to is Owner only",
        "action": "Select the records the team needs and use bulk edit to change Visible to. Check the default visibility in your visibility group settings."},
    "duplicate": {
        "where": "Pipedrive's merge duplicates tool",
        "filter": "Pipedrive suggests duplicate people and organizations",
        "action": "Review and merge there. Use this list to start with the records that matter most."},
}
ISSUE_ROWS_CAP = 1500
DUPES_CAP = 1000


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
    """Records from many files, deduplicated by id (latest update_time wins)."""
    by_id = {}
    for path in expand(patterns):
        raw = read_json(path)
        if isinstance(raw, dict):
            raw = raw.get("data") or raw.get("items") or []
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
    """Return (fields {entity: {code: (name, writable)}}, users, pipelines)."""
    fields, users, pipelines = defaultdict(dict), {}, {}
    if not path:
        return fields, users, pipelines
    try:
        ctx = read_json(path)
    except (OSError, ValueError):
        return fields, users, pipelines
    for ent, key in CONTEXT_KEYS.items():
        for fd in (ctx.get("custom_fields") or {}).get(key) or []:
            fields[ent][fd.get("field_code")] = (fd.get("field_name"), fd.get("is_writable", True))
    raw_users = ctx.get("users") or ctx.get("companyUsers") or {}
    if isinstance(raw_users, list):
        raw_users = {u.get("id"): u.get("name") for u in raw_users if isinstance(u, dict)}
    users = {str(k): v for k, v in raw_users.items()}
    raw_pipes = ctx.get("pipelines") or {}
    if isinstance(raw_pipes, list):
        raw_pipes = {p.get("id"): p.get("name") for p in raw_pipes if isinstance(p, dict)}
    pipelines = {str(k): (v.get("name") if isinstance(v, dict) else v) for k, v in raw_pipes.items()}
    return fields, users, pipelines


def load_dupes(path, ent):
    rows = []
    if not path:
        return rows
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({"e": ent, "a": row.get("id_a"), "b": row.get("id_b"),
                         "na": row.get("name_a") or "", "nb": row.get("name_b") or "",
                         "why": row.get("reason") or "", "score": row.get("score") or ""})
    return rows


def ref_id(value):
    if isinstance(value, dict):
        return value.get("id") or value.get("value")
    return value


def is_empty(value):
    if value is None or value == "" or value == [] or value == {}:
        return True
    if isinstance(value, list):
        return all(is_empty(v.get("value") if isinstance(v, dict) else v) for v in value)
    if isinstance(value, dict) and "value" in value and len(value) <= 3:
        return is_empty(value["value"])
    return False


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


def has(rec, key):
    """True/False if the key was returned, None if the connector left it out."""
    if key not in rec:
        return None
    return not is_empty(ref_id(rec[key]) if key.endswith("_id") else rec[key])


def compact(ent, rec):
    """Small, stable copy of a record: enough to recompute its issues later."""
    c = {"n": rec.get("title") or rec.get("name") or "",
         "o": str(ref_id(rec.get("owner_id")) or ""),
         "u": str(rec.get("update_time") or "")[:10],
         "vis": rec.get("visible_to")}
    if ent == "deal":
        c.update({"s": rec.get("status", "open"), "v": rec.get("value") or 0,
                  "cur": rec.get("currency") or "", "p": str(rec.get("pipeline_id") or ""),
                  "cd": has(rec, "expected_close_date"), "na": has(rec, "next_activity_id")})
    elif ent == "person":
        c.update({"ct": bool(has(rec, "emails") or has(rec, "phones")), "og": has(rec, "org_id")})
    return c


def issues_of(ent, c, today, stale_days):
    out = []
    if ent == "deal" and c.get("s", "open") == "open":
        if c.get("na") is False:
            out.append(("no_next_step", {}))
        if c.get("cd") is False:
            out.append(("no_close_date", {}))
        if not c.get("v"):
            out.append(("no_value", {}))
        last = parse_day(c.get("u"))
        if last and (today - last).days > stale_days:
            out.append(("stale", {"days": (today - last).days}))
    if ent == "person":
        if not c.get("ct"):
            out.append(("no_contact", {}))
        if c.get("og") is False:
            out.append(("no_org", {}))
    if c.get("vis") in (1, "1"):
        out.append(("owner_only", {}))
    return out


def field_rows(ent, records, ctx_fields, threshold):
    """Fill rate per standard and custom field present in the sample."""
    total = len(records)
    if not total:
        return []
    names = ctx_fields.get(ent, {})
    codes = dict(STANDARD[ent])
    for rec in records:
        for code in (rec.get("custom_fields") or {}):
            codes.setdefault(code, None)
    present, filled = defaultdict(int), defaultdict(int)
    for rec in records:
        cf = rec.get("custom_fields") or {}
        for code, label in codes.items():
            src = cf if label is None else rec
            if code in src:
                present[code] += 1
                val = src[code]
                if not is_empty(val) and not (code == "value" and not val):
                    filled[code] += 1
    rows = []
    for code, label in codes.items():
        name, writable = names.get(code, (label, True))
        f = filled[code]
        if not present[code]:
            status = "not_returned"
        elif writable is False:
            status = "read_only"
        elif f == 0:
            status = "empty"
        elif f / total < threshold:
            status = "attention"
        else:
            status = "ok"
        rows.append({"entity": ent, "key": code, "custom": label is None,
                     "field": (name or code[:8]).strip(), "filled": f, "total": total,
                     "fill": round(f / total, 3), "status": status})
    order = {"empty": 0, "attention": 1, "ok": 2, "read_only": 3, "not_returned": 4}
    rows.sort(key=lambda r: (order[r["status"]], r["fill"], r["entity"], r["field"]))
    return rows



def cap_rows(rs, cap):
    """Keep at most cap rows, shared fairly between issue codes so no issue type
    disappears. Within a code: open deals first, then biggest value, then most
    recently updated."""
    by = defaultdict(list)
    for r in rs:
        by[r["c"]].append(r)
    for lst in by.values():
        lst.sort(key=lambda r: r["u"], reverse=True)
        lst.sort(key=lambda r: (not r.get("open"), -float(r["v"] or 0)))
    keep, left = [], cap
    codes = sorted(by, key=lambda c: len(by[c]))
    for i, code in enumerate(codes):
        share = left // (len(codes) - i)
        take = by[code][:share]
        keep += take
        left -= len(take)
    return keep


def load_snapshot(path):
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for ent in ENTITIES:
        ap.add_argument("--" + ARG[ent], nargs="*", default=[])
        ap.add_argument("--sample-" + ARG[ent], nargs="*", default=[])
    ap.add_argument("--context")
    ap.add_argument("--dupes-person")
    ap.add_argument("--dupes-org")
    ap.add_argument("--snapshot", help="previous snapshot to merge into")
    ap.add_argument("--snapshot-out")
    ap.add_argument("--prev", help="previous summary JSON, for the trend")
    ap.add_argument("--scope-note", default="")
    ap.add_argument("--domain", help="Pipedrive company subdomain, for record links")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--stale-days", type=int, default=90)
    ap.add_argument("--today")
    ap.add_argument("--out")
    ap.add_argument("--summary-out")
    ap.add_argument("--fixlist-out")
    ap.add_argument("--html", help="tracker.html template")
    ap.add_argument("--html-out")
    args = ap.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()
    ctx_fields, users, pipelines = load_context(args.context)

    # Scope: snapshot first, then fresh records on top.
    snap = load_snapshot(args.snapshot)
    store = {ent: {} for ent in ENTITIES}
    snap_age = None
    if snap:
        for key, c in (snap.get("records") or {}).items():
            ent, _, rid = key.partition(":")
            if ent in store:
                store[ent][rid] = c
        sd = parse_day(snap.get("date"))
        snap_age = (today - sd).days if sd else None
    fresh, samples = {}, {}
    for ent in ENTITIES:
        recs = load_records(getattr(args, ARG[ent]))
        fresh[ent] = len(recs)
        for rec in recs:
            store[ent][str(rec.get("id"))] = compact(ent, rec)
        sample_paths = getattr(args, "sample_" + ARG[ent])
        samples[ent] = load_records(sample_paths) if sample_paths else recs

    # Entities with no new records keep the field rates and duplicates of the snapshot.
    old_fields = (snap or {}).get("fields") or {}
    old_dupes = (snap or {}).get("dupes") or {}
    fields, reused = [], []
    for ent in ENTITIES:
        if samples[ent] or not old_fields.get(ent):
            fields += field_rows(ent, samples[ent], ctx_fields, args.threshold)
        else:
            fields += old_fields[ent]
            reused.append(ent)
    dupes = []
    for ent, path in (("person", args.dupes_person), ("org", args.dupes_org)):
        dupes += load_dupes(path, ent) if path else old_dupes.get(ent, [])

    counts = defaultdict(int)
    flagged = 0
    flagged_by = defaultdict(int)
    owners = defaultdict(lambda: {"records": 0, "with_issues": 0, "codes": defaultdict(int)})
    pipes = defaultdict(lambda: {"open": 0, "no_next_step": 0, "no_close_date": 0,
                                 "no_value": 0, "stale": 0, "value": defaultdict(float)})
    at_risk = defaultdict(lambda: defaultdict(float))
    rows = {ent: [] for ent in ENTITIES}
    for ent in ENTITIES:
        for rid, c in store[ent].items():
            found = issues_of(ent, c, today, args.stale_days)
            own = owners[c.get("o", "")]
            own["records"] += 1
            open_deal = ent == "deal" and c.get("s", "open") == "open"
            pipe = pipes[c.get("p", "")] if open_deal else None
            if open_deal:
                pipe["open"] += 1
                pipe["value"][c.get("cur", "")] += float(c.get("v") or 0)
            if not found:
                continue
            flagged += 1
            flagged_by[ent] += 1
            own["with_issues"] += 1
            for code, extra in found:
                counts[code] += 1
                own["codes"][code] += 1
                if open_deal:
                    if code in pipe:
                        pipe[code] += 1
                    at_risk[code][c.get("cur", "")] += float(c.get("v") or 0)
                rows[ent].append({"e": ent, "id": rid, "n": c.get("n", ""), "o": c.get("o", ""),
                                  "c": code, "d": extra.get("days"), "v": c.get("v") or 0,
                                  "cur": c.get("cur", ""), "p": c.get("p", ""), "u": c.get("u", ""),
                                  "open": open_deal})

    scope = {ent: len(store[ent]) for ent in ENTITIES}
    shown, truncated = {}, {}
    for ent in ENTITIES:
        shown[ent] = cap_rows(rows[ent], ISSUE_ROWS_CAP)
        truncated[ent] = len(rows[ent]) - len(shown[ent])

    scored = [f for f in fields if f["status"] in ("ok", "attention", "empty")]
    completeness = round(sum(f["fill"] for f in scored) / len(scored), 3) if scored else None
    kpis = {
        "completeness": completeness,
        "records": sum(scope.values()),
        "records_with_issues": flagged,
        "duplicates": len(dupes),
        "no_next_step": counts["no_next_step"],
        "stale": counts["stale"],
        "owner_only": counts["owner_only"],
        "fields_attention": sum(f["status"] in ("attention", "empty") for f in fields),
    }

    trend = None
    if args.prev:
        try:
            with open(args.prev, encoding="utf-8") as f:
                prev = json.load(f)
            pk = prev.get("kpis", {})
            trend = {"date": prev.get("date"),
                     "kpis": {k: round(v - pk[k], 3) if isinstance(v, (int, float)) and isinstance(pk.get(k), (int, float)) else None
                              for k, v in kpis.items()}}
            prev_fill = {(r["entity"], r["key"]): r["fill"] for r in prev.get("fields", [])}
            for row in fields:
                old = prev_fill.get((row["entity"], row["key"]))
                if old is not None:
                    row["delta"] = round(row["fill"] - old, 3)
        except (OSError, ValueError, KeyError):
            trend = None

    def owner_name(k):
        return users.get(k) or ("User " + k if k else "No owner")

    recipes = {k: dict(v, filter=v["filter"].format(stale=args.stale_days)) for k, v in RECIPES.items()}
    out = {
        "date": today.isoformat(),
        "domain": args.domain,
        "coverage": {"scope": scope, "sample": {ent: next((r["total"] for r in old_fields[ent]), 0) if ent in reused
                                else len(samples[ent]) for ent in ENTITIES},
                     "fields_from_snapshot": reused,
                     "fresh": fresh, "note": args.scope_note,
                     "snapshot_age_days": snap_age, "merged": bool(snap)},
        "kpis": kpis,
        "counts": dict(counts),
        "with_issues": {ent: flagged_by[ent] for ent in ENTITIES},
        "trend": trend,
        "fields": fields,
        "owners": [{"id": k, "name": owner_name(k), "records": v["records"],
                    "with_issues": v["with_issues"], "codes": dict(v["codes"])}
                   for k, v in sorted(owners.items(), key=lambda kv: -kv[1]["with_issues"])],
        "pipelines": [{"id": k, "name": pipelines.get(k) or ("Pipeline " + k if k else "No pipeline"),
                       **{x: v[x] for x in ("open", "no_next_step", "no_close_date", "no_value", "stale")},
                       "value": {cur: round(val, 2) for cur, val in v["value"].items()}}
                      for k, v in sorted(pipes.items(), key=lambda kv: -kv[1]["open"])],
        "at_risk": {code: {cur: round(val, 2) for cur, val in by.items()} for code, by in at_risk.items()},
        "recipes": recipes,
        "issues": shown,
        "truncated": truncated,
        "dupes": dupes[:DUPES_CAP],
        "dupes_truncated": max(0, len(dupes) - DUPES_CAP),
    }

    text = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    if args.summary_out:
        slim = {"date": out["date"], "kpis": kpis,
                "fields": [{k: r[k] for k in ("entity", "key", "fill")} for r in fields]}
        with open(args.summary_out, "w", encoding="utf-8") as f:
            json.dump(slim, f, separators=(",", ":"))
    if args.snapshot_out:
        with open(args.snapshot_out, "w", encoding="utf-8") as f:
            json.dump({"date": out["date"],
                       "fields": {ent: [r for r in fields if r["entity"] == ent] for ent in ENTITIES},
                       "dupes": {ent: [d for d in dupes if d["e"] == ent] for ent in ("person", "org")},
                       "records": {f"{ent}:{rid}": c for ent in ENTITIES for rid, c in store[ent].items()}},
                      f, ensure_ascii=False, separators=(",", ":"))
    if args.fixlist_out:
        with open(args.fixlist_out, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["type", "id", "name", "owner", "issue", "suggested_fix",
                        "value", "currency", "pipeline", "related_id"])
            for ent in ENTITIES:
                for r in rows[ent]:
                    issue, fix = ISSUE_TEXT[r["c"]]
                    w.writerow([ent, r["id"], r["n"], owner_name(r["o"]), issue.format(days=r["d"]), fix,
                                r["v"] if ent == "deal" else "", r["cur"], pipelines.get(r["p"], r["p"]), ""])
            for d in dupes:
                w.writerow([d["e"], d["a"], d["na"], "", "Possible duplicate (" + d["why"] + ")",
                            "Merge in Pipedrive", "", "", "", d["b"]])
    if args.html:
        with open(args.html, encoding="utf-8") as f:
            page = f.read()
        if "/*DATA*/" not in page:
            sys.exit("template has no /*DATA*/ placeholder")
        page = page.replace("/*DATA*/", text.replace("</", "<\\/"), 1)
        html_out = args.html_out or os.path.join("pipedrive-out", "pd-data-hygiene", "tracker.html")
        os.makedirs(os.path.dirname(html_out) or ".", exist_ok=True)
        with open(html_out, "w", encoding="utf-8") as f:
            f.write(page)
    if not (args.out or args.html):
        print(text)

    print(f"records {kpis['records']} | with issues {flagged} | "
          f"fields needing attention {kpis['fields_attention']} | "
          f"completeness {completeness if completeness is not None else 'n/a'} | "
          f"page data {len(text) // 1024} KB", file=sys.stderr)


if __name__ == "__main__":
    main()
