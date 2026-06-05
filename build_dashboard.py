"""
build_dashboard.py
------------------
Run this after each scrape to regenerate deals_dashboard.html
with fresh data from your CSV.

Usage:
    python build_dashboard.py
    python build_dashboard.py --csv deals_history.csv --out index.html
"""

import csv
import json
import sys
import os
import argparse
from pathlib import Path

COL_MAP = {
    "deal_id":          "id",
    "announced_date":   "date",
    "type":             "type",
    "companies":        "companies",
    "headline":         "headline",
    "value":            "value",
    "therapeutic_area": "ta",
    "modality":         "modality",
    "summary":          "summary",
    "url":              "url",
    "indication_1":     "indication_1",
    "indication_2":     "indication_2",
    "indication_3":     "indication_3",
    "target_1":         "target_1",
    "target_2":         "target_2",
    "target_3":         "target_3",
    "delivery_vehicle": "delivery_vehicle",
    "source":           "source",
}


def parse_value(raw):
    if not raw or raw.strip() in ("", "N/A", "n/a", "null", "None", "-"):
        return None
    raw = raw.strip().lstrip("$").replace(",", "")
    if raw.upper().endswith("B"):
        try:
            return round(float(raw[:-1]), 4)
        except ValueError:
            pass
    if raw.upper().endswith("M"):
        try:
            return round(float(raw[:-1]) / 1000, 4)
        except ValueError:
            pass
    try:
        return round(float(raw), 4)
    except ValueError:
        return None


def js_str(s):
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\\"'  )
    s = s.replace("\n", " ").replace("\r", "")
    return s


def row_to_js(row):
    fields = []
    for csv_col, js_key in COL_MAP.items():
        raw = row.get(csv_col, "").strip()
        if js_key == "value":
            v = parse_value(raw)
            fields.append(f'{js_key}:{json.dumps(v)}')
        else:
            fields.append(f'{js_key}:"{js_str(raw)}"')
    return "{" + ",".join(fields) + "}"


def load_csv(csv_path):
    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            if not row.get("headline", "").strip():
                print(f"  Skipping row {i}: no headline")
                continue
            if not row.get("announced_date", "").strip():
                print(f"  Skipping row {i}: no announced_date")
                continue
            rows.append(row)
    return rows


def build_raw_js(rows):
    entries = [row_to_js(r) for r in rows]
    return "const RAW=[\n" + ",\n".join(entries) + "\n];"


def regenerate(csv_path, html_path):
    print(f"Reading CSV:       {csv_path}")
    rows = load_csv(csv_path)
    print(f"  Loaded {len(rows)} deals")

    print(f"Reading dashboard: {html_path}")
    html = html_path.read_text(encoding="utf-8")

    marker = "const RAW=["
    start_idx = html.find(marker)
    if start_idx == -1:
        print("ERROR: Could not find 'const RAW=[' in the dashboard HTML.")
        sys.exit(1)

    end_idx = html.find("\n];", start_idx)
    if end_idx == -1:
        end_idx = html.find("];", start_idx) + 2
    else:
        end_idx += 3

    new_raw = build_raw_js(rows)
    new_html = html[:start_idx] + new_raw + html[end_idx:]

    html_path.write_text(new_html, encoding="utf-8")
    print(f"Dashboard updated: {html_path}")
    print(f"  {len(rows)} deals embedded ({len(new_html):,} bytes)")


def main():
    parser = argparse.ArgumentParser(description="Rebuild biopharma dashboard from CSV")
    parser.add_argument("--csv", default="deals_history.csv",
                        help="Path to deals CSV (default: deals_history.csv)")
    parser.add_argument("--out", default="index.html",
                        help="Path to dashboard HTML to update (default: index.html)")
    args = parser.parse_args()

    here = Path(__file__).parent
    csv_path = Path(args.csv) if Path(args.csv).is_absolute() else here / args.csv
    html_path = Path(args.out) if Path(args.out).is_absolute() else here / args.out

    if not csv_path.exists():
        print(f"ERROR: CSV not found at {csv_path}")
        sys.exit(1)
    if not html_path.exists():
        print(f"ERROR: Dashboard HTML not found at {html_path}")
        sys.exit(1)

    regenerate(csv_path, html_path)


if __name__ == "__main__":
    main()
