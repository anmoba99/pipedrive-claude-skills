#!/usr/bin/env python3
"""Field completeness and record issues for the data health tracker.

Reads saved getDeals / getPersons / getOrganizations results and works out
the fill rate of every standard and custom field, records with gaps, open
deals with no next step, stale deals and owner-only visibility. Writes one
JSON for the tracker, and optionally the tracker HTML itself. Standard
library only, no network.

Usage:
  python3 field_health.py [--deals deals.json] [--persons persons.json]
      [--orgs orgs.json] [--context account_context.json]
      [--dupes-person dupes_p.csv] [--dupes-org dupes_o.csv]
      [--prev last-summary.json] [--domain acme] [--threshold 0.5]
      [--stale-days 90] [--today YYYY-MM-DD]
      [--out data.json] [--summary-out summary.json]
      [--html tracker.html --html-out out.html]

Input: JSON list, or an object with a "data" list (raw MCP result).
Context: raw getAccountContext result (custom_fields per entity with
field_name, field_code, is_writable) or .pipedrive/context.json with
"users": {"<id>": "<name>"}. Both are optional.
Duplicates: CSV from find_dupes.py (id_a,id_b,...).
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime

ENTITIES = {"deal": "deals", "person": "persons", "org": "orgs"}
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
    "no_contact": ("No email or phone", "Add email or phone"),
    "no_org": ("No organization", "Link an organization"),
    "no_value": ("No deal value", "Add value or products"),
    "no_close_date": ("No expected close date", "Set expected close date"),
    "no_next_step": ("No next activity", "Schedule next activity"),
    "stale": ("Idle {days} days", "Revive or close as lost"),
    "duplicate": ("Possible duplicate of #{related}", "Merge in Pipedrive"),
    "owner_only": ("Visible to owner only", "Check visibility if team needs it"),
}
ISSUE_CAP = 500


def load_list(path):
    if not path:
        return []
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "text" in raw[0]:
        raw = json.loads(raw[0]["text"])  # saved tool result wrapper
    if isinstance(raw, dict):
        raw = raw.get("data") or raw.get("items") or []
    return [r.get("item", r) for r in raw if isinstance(r, dict)]


def load_context(path):
    """Return ({entity: {code: (name, writable, custom)}}, {user_id: name})."""
    fields, users = defaultdict(dict), {}
    if not path:
        return fields, users
    try:
        with open(path, encoding="utf-8") as f:
            ctx = json.load(f)
    except (OSError, ValueError):
        return fields, users
    if isinstance(ctx, list) and ctx and isinstance(ctx[0], dict) and "text" in ctx[0]:
        ctx = json.loads(ctx[0]["text"])
    for ent, key in CONTEXT_KEYS.items():
        for fd in (ctx.get("custom_fields") or {}).get(key) or []:
            fields[ent][fd.get("field_code")] = (
                fd.get("field_name"), fd.get("is_writable", True),
                fd.get("is_custom_field", False))
    raw_users = ctx.get("users") or ctx.get("companyUsers") or {}
    if isinstance(raw_users, list):
        raw_users = {u.get("id"): u.get("name") for u in raw_users if isinstance(u, dict)}
    users = {str(k): v for k, v in raw_users.items()}
    return fields, users


def load_dupes(path):
    pairs = []
    if not path:
        return pairs
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pairs.append((str(row.get("id_a")), str(row.get("id_b"))))
    return pairs


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


def field_rows(ent, records, ctx_fields, threshold):
    """Fill rate per standard and custom field present in the data."""
    total = len(records)
    if not total:
        return []
    names = ctx_fields.get(ent, {})
    codes = dict(STANDARD[ent])
    for rec in records:
        for code in (rec.get("custom_fields") or {}):
            codes.setdefault(code, None)
    rows = []
    for code, label in codes.items():
        name, writable, _ = names.get(code, (label, True, False))
        custom = label is None
        present = 0
        filled = 0
        for rec in records:
            src = (rec.get("custom_fields") or {}) if custom else rec
            if code in src:
                present += 1
                if not is_empty(src[code]) and not (code == "value" and not src[code]):
                    filled += 1
        if not present:
            status = "not_returned"
        elif writable is False:
            status = "read_only"
        elif filled == 0:
            status = "empty"
        elif filled / total < threshold:
            status = "attention"
        else:
            status = "ok"
        rows.append({
            "entity": ent, "key": code, "custom": custom,
            "field": (name or code[:8]).strip(),
            "filled": filled, "total": total,
            "fill": round(filled / total, 3), "status": status,
        })
    order = {"empty": 0, "attention": 1, "ok": 2, "read_only": 3, "not_returned": 4}
    rows.sort(key=lambda r: (order[r["status"]], r["fill"], r["entity"], r["field"]))
    return rows


def record_issues(ent, rec, today, stale_days):
    out = []
    if ent == "person":
        if is_empty(rec.get("emails")) and is_empty(rec.get("phones")):
            out.append(("no_contact", {}))
        if "org_id" in rec and not ref_id(rec.get("org_id")):
            out.append(("no_org", {}))
    if ent == "deal" and rec.get("status", "open") == "open":
        if not rec.get("value"):
            out.append(("no_value", {}))
        if "expected_close_date" in rec and not rec.get("expected_close_date"):
            out.append(("no_close_date", {}))
        if "next_activity_id" in rec and not rec.get("next_activity_id"):
            out.append(("no_next_step", {}))
        last = parse_day(rec.get("update_time"))
        if last and (today - last).days > stale_days:
            out.append(("stale", {"days": (today - last).days}))
    if rec.get("visible_to") in (1, "1"):
        out.append(("owner_only", {}))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for ent in ENTITIES.values():
        ap.add_argument("--" + ent)
    ap.add_argument("--context")
    ap.add_argument("--dupes-person")
    ap.add_argument("--dupes-org")
    ap.add_argument("--prev")
    ap.add_argument("--domain", help="Pipedrive company subdomain, for record links")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--stale-days", type=int, default=90)
    ap.add_argument("--today")
    ap.add_argument("--out")
    ap.add_argument("--summary-out")
    ap.add_argument("--html", help="tracker.html template")
    ap.add_argument("--html-out")
    args = ap.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()
    ctx_fields, users = load_context(args.context)
    data = {ent: load_list(getattr(args, key)) for ent, key in ENTITIES.items()}
    dupes = {"person": load_dupes(args.dupes_person), "org": load_dupes(args.dupes_org)}

    fields, issues, owners = [], [], defaultdict(lambda: {"records": 0, "issues": 0})
    flagged = set()
    counts = defaultdict(int)
    for ent, records in data.items():
        fields += field_rows(ent, records, ctx_fields, args.threshold)
        by_id = {str(r.get("id")): r for r in records}
        dup_of = defaultdict(list)
        for a, b in dupes.get(ent, []):
            dup_of[a].append(b)
            dup_of[b].append(a)
        for rec in records:
            rid = str(rec.get("id"))
            owner = str(ref_id(rec.get("owner_id")) or "")
            owners[owner]["records"] += 1
            found = record_issues(ent, rec, today, args.stale_days)
            found += [("duplicate", {"related": o}) for o in dup_of.get(rid, [])[:1]]
            for code, extra in found:
                counts[code] += 1
                text, fix = ISSUE_TEXT[code]
                issues.append({
                    "entity": ent, "id": rec.get("id"),
                    "name": rec.get("title") or rec.get("name") or "",
                    "owner": owner, "code": code,
                    "issue": text.format(**extra), "fix": fix,
                    "related": extra.get("related"),
                })
            if found:
                flagged.add((ent, rid))
                owners[owner]["issues"] += 1
        counts["records"] += len(by_id)

    scored = [f for f in fields if f["status"] in ("ok", "attention", "empty")]
    completeness = round(sum(f["fill"] for f in scored) / len(scored), 3) if scored else None
    kpis = {
        "completeness": completeness,
        "records": counts["records"],
        "records_with_issues": len(flagged),
        "duplicates": len(dupes["person"]) + len(dupes["org"]),
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

    issues.sort(key=lambda i: (list(ISSUE_TEXT).index(i["code"]), i["entity"], str(i["id"])))
    out = {
        "date": today.isoformat(),
        "domain": args.domain,
        "scope": {ent: len(recs) for ent, recs in data.items()},
        "kpis": kpis,
        "trend": trend,
        "fields": fields,
        "owners": [{"id": k, "name": users.get(k) or ("User " + k if k else "No owner"), **v}
                   for k, v in sorted(owners.items(), key=lambda kv: -kv[1]["issues"])],
        "issues": issues[:ISSUE_CAP],
        "issues_truncated": max(0, len(issues) - ISSUE_CAP),
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
    if args.html:
        with open(args.html, encoding="utf-8") as f:
            page = f.read()
        if "/*DATA*/" not in page:
            sys.exit("template has no /*DATA*/ placeholder")
        page = page.replace("/*DATA*/", text.replace("</", "<\\/"), 1)
        with open(args.html_out or "tracker.html", "w", encoding="utf-8") as f:
            f.write(page)
    if not (args.out or args.html):
        print(text)

    print(f"records {kpis['records']} | with issues {kpis['records_with_issues']} | "
          f"fields needing attention {kpis['fields_attention']} | "
          f"completeness {completeness if completeness is not None else 'n/a'}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
