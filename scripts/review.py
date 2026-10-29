"""Separate CSV review workspace. Import only explicit human decisions."""
import argparse
import csv
import json
from datetime import datetime

from event_nlp.config import DATA, FIELDS
from event_nlp.data import read_jsonl, write_jsonl, validate_human


def export_review(path):
    rows = read_jsonl(DATA / "real.jsonl")
    columns = ["id", "text", "source_url", "institution", "suggested_category", "suggested_fields", "reviewer", "reviewed_at", "decision", "category", "reference_date", "notes"]
    columns += [field + "_raw" for field in FIELDS] + ["date_normalized"]
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            human = row.get("human") or {}
            value = {key: row[key] for key in ("id", "text", "source_url", "institution")}
            value.update(suggested_category=row["proposed"]["category"], suggested_fields=json.dumps(row["proposed"]["fields"], ensure_ascii=False))
            value.update({key: human.get(key, "") for key in ("reviewer", "reviewed_at", "decision", "category", "notes")})
            value["reference_date"] = row.get("reference_date", "")
            for field in FIELDS:
                annotation = human.get("fields", {}).get(field)
                value[field + "_raw"] = annotation["raw"] if annotation else ""
            value["date_normalized"] = (human.get("fields", {}).get("date") or {}).get("normalized", "")
            writer.writerow(value)
    print(f"Exported {len(rows)} records to {path}; no human labels created.")


def import_review(path):
    rows = read_jsonl(DATA / "real.jsonl")
    index = {row["id"]: row for row in rows}
    corrections, seen = [], set()
    with path.open(newline="", encoding="utf-8-sig") as file:
        for line in csv.DictReader(file):
            if not line["decision"].strip():
                continue
            if line["id"] in seen:
                raise ValueError("Repeated review ID")
            seen.add(line["id"])
            row = index[line["id"]]
            if line["text"] != row["text"]:
                raise ValueError("Do not edit original announcement text")
            fields = {}
            for field in FIELDS:
                raw = line[field + "_raw"]
                if not raw:
                    fields[field] = None
                else:
                    if row["text"].count(raw) != 1:
                        raise ValueError(f"{row['id']}: {field} must uniquely identify exact source evidence; use JSON annotation for repeated substrings")
                    start = row["text"].index(raw)
                    fields[field] = {"raw": raw, "start": start, "end": start + len(raw), "normalized": line.get("date_normalized") or None if field == "date" else None}
            timestamp = line["reviewed_at"].strip()
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            human = {"reviewer": line["reviewer"], "reviewed_at": timestamp,
                     "decision": line["decision"], "category": line["category"] or None, "fields": fields, "notes": line["notes"]}
            validate_human(row, human)
            corrections.append({"id": row["id"], "previous": row.get("human"), "human": human})
            row["human"] = human
            row["reference_date"] = line.get("reference_date") or None
            row["review_status"] = "reviewed" if human["decision"] == "accepted" else human["decision"]
    # Validate all rows before any write; preserve an append-only correction history.
    with (DATA / "human_corrections.jsonl").open("a", encoding="utf-8") as file:
        for correction in corrections:
            file.write(json.dumps(correction, ensure_ascii=False) + "\n")
    write_jsonl(DATA / "real.jsonl", rows)
    summary_path = DATA / "collection_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["human_reviewed"] = sum(bool(row.get("human") and row["human"]["decision"] == "accepted") for row in rows)
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Imported {len(corrections)} explicit human decisions.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["export", "import"])
    parser.add_argument("--file", default=str(DATA / "review.csv"))
    args = parser.parse_args()
    from pathlib import Path
    path = Path(args.file)
    export_review(path) if args.action == "export" else import_review(path)


if __name__ == "__main__":
    main()
