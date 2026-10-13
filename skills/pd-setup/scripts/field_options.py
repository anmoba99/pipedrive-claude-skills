#!/usr/bin/env python3
"""Turn Pipedrive's "Selectable options in fields" export into field-map.json.

Export it in Pipedrive: Settings > Data fields > Export > "Selectable options
in fields". The CSV covers single and multiple option fields only (option
name and ID, field name and API key). Other field types are not in it.

Standard library only, no network.

Usage:
  python3 field_options.py data_fields_options_<date>.csv
      [--merge .pipedrive/field-map.json] [--out .pipedrive/field-map.json]

Input columns: Option ID, Option name, Item type, Field name, Field type,
Field API key.
Output: {"deal": {"<Field name>": {"key": "", "type": "", "options":
{"<label>": <id>}}}, "person": {}, "org": {}, ...} (stdout or --out).
With --merge, fields already in that file are updated by API key, others kept.
Summary goes to stderr: fields per item type, duplicate field names.
"""

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict

ITEM_TYPES = {
    "deal": "deal", "person": "person", "organisation": "org",
    "organization": "org", "lead": "lead", "activity": "activity",
    "product": "product", "project": "project",
}


def field_type(raw):
    raw = raw.lower()
    if "multiple" in raw:
        return "set"
    return "enum"


def load_export(path):
    fields = defaultdict(dict)  # item -> key -> field
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            item = ITEM_TYPES.get(row["Item type"].strip().lower(),
                                  row["Item type"].strip().lower())
            key = row["Field API key"].strip()
            field = fields[item].setdefault(key, {
                "name": row["Field name"].strip(),
                "key": key,
                "type": field_type(row["Field type"]),
                "options": {},
            })
            label = row["Option name"].strip()
            if label in field["options"]:
                label = f"{label} [{row['Option ID'].strip()}]"
            field["options"][label] = int(row["Option ID"])
    return fields


def by_name(fields):
    """Key fields by name; same name on different keys gets a key suffix."""
    out, dupes = {}, {}
    for item, items in fields.items():
        counts = Counter(f["name"] for f in items.values())
        out[item] = {}
        for f in items.values():
            name = f["name"]
            if counts[name] > 1:
                dupes.setdefault(item, set()).add(name)
                name = f"{name} [{f['key'][:6]}]"
            out[item][name] = {k: f[k] for k in ("key", "type", "options")}
    return out, dupes


def merge(base, new):
    for item, items in new.items():
        target = base.setdefault(item, {})
        known = {v.get("key"): n for n, v in target.items()}
        for name, f in items.items():
            if f["key"] in known:
                target[known[f["key"]]].update(type=f["type"], options=f["options"])
            else:
                target[name] = f
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export")
    ap.add_argument("--merge", help="existing field-map.json to update")
    ap.add_argument("--out")
    a = ap.parse_args()

    result, dupes = by_name(load_export(a.export))
    if a.merge:
        try:
            with open(a.merge, encoding="utf-8") as f:
                result = merge(json.load(f), result)
        except FileNotFoundError:
            pass
    for item in ("deal", "person", "org"):
        result.setdefault(item, {})

    text = json.dumps(result, ensure_ascii=False, indent=1)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)

    summary = ", ".join(f"{k} {len(v)}" for k, v in sorted(result.items()) if v)
    print(f"Option fields: {summary}", file=sys.stderr)
    for item, names in sorted(dupes.items()):
        print(f"Duplicate names ({item}): {', '.join(sorted(names))}. "
              "Rename in Pipedrive to avoid mix-ups.", file=sys.stderr)


if __name__ == "__main__":
    main()
