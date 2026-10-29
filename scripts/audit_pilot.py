"""Automated quality screening is NOT human annotation. Preserve exclusions/corrections."""
import json
import hashlib
import re
from collections import Counter
from urllib.parse import urlparse

from event_nlp.config import DATA, REPORTS, FIELDS
from event_nlp.data import group_records, read_jsonl, write_jsonl
from event_nlp.extraction import extract


def main():
    rows = read_jsonl(DATA / "real.jsonl")
    accepted, excluded, corrections = [], read_jsonl(DATA / "excluded.jsonl"), read_jsonl(DATA / "collection_corrections.jsonl")
    pages = set()
    for row in rows:
        canonical = row["source_url"].split("?")[0].rstrip("/")
        reason = "duplicate source event page" if canonical in pages else "metadata or mail-header fragment rather than a natural announcement paragraph" if row["text"].startswith(("Nature of the meeting:", "To:")) else None
        if not reason and re.search(r"^Award Winning Projects|^Humanities innovation is|^Later in February|special group rate for attendees", row["text"], re.I):
            reason = "award/topic/registration/accommodation fragment rather than an announcement paragraph"
        if not reason and urlparse(row["source_url"]).netloc == "www.colorado.edu" and urlparse(row["source_url"]).path in ("", "/"):
            reason = "general institution homepage, not an event announcement source page"
        if reason:
            excluded.append({**row, "exclusion_reason": reason, "exclusion_origin": "automated quality screen"})
            continue
        pages.add(canonical)
        if "â\u0080" in row["text"] or "Ã" in row["text"]:
            try:
                decoded = row["text"].encode("latin1").decode("utf-8")
                corrections.append({"id": row["id"], "kind": "repair HTTP character decoding", "before": row["text"], "after": decoded, "origin": "automated; not human review"})
                row["text"] = decoded
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
        result = extract(row["text"], mode="hybrid")
        row["proposed"] = {"category": result["category"]["label"], "fields": result["fields"]}
        if re.search(r"\b(?:series|events yearly|Highlights|Meetings for)\b", row["text"], re.I):
            row["proposed"]["category"] = None
            result["warnings"].append({"code": "dataset_scope_review", "message": "Recurring series or mixed programme may not be a single event; annotation eligibility requires review.", "field": None})
        row["review_status"] = "needs_review" if not row.get("human") else row["review_status"]
        row["automatic_warnings"] = result["warnings"]
        accepted.append(row)
    accepted = group_records(accepted)
    schema_errors = []
    required = {"id", "text", "institution", "source_url", "collection_date", "publication_date", "proposed", "group_id", "provenance", "review_status", "human", "split"}
    for row in accepted:
        if required - row.keys() or row["provenance"] != "real" or not row["source_url"].startswith("https://"):
            schema_errors.append({"id": row.get("id"), "issue": "required metadata/provenance missing or invalid"})
        for field, value in row["proposed"]["fields"].items():
            if value is not None and row["text"][value["start"]:value["end"]] != value["raw"]:
                schema_errors.append({"id": row["id"], "issue": "evidence mismatch", "field": field})
        row["source_excerpt_hash"] = hashlib.sha256(row["text"].encode()).hexdigest()
    write_jsonl(DATA / "real.jsonl", accepted)
    write_jsonl(DATA / "excluded.jsonl", excluded)
    write_jsonl(DATA / "collection_corrections.jsonl", corrections)
    summary = {"actual_count": len(accepted), "requested_count": 25,
               "institutions": dict(Counter(row["institution"] for row in accepted)),
               "proposed_categories": dict(Counter(row["proposed"]["category"] or "needs_review" for row in accepted)),
               "human_reviewed": sum(bool(row.get("human") and row["human"]["decision"] == "accepted") for row in accepted),
               "excluded_records": len(excluded), "independent_groups": len({row["group_id"] for row in accepted})}
    (DATA / "collection_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    report = {**summary, "schema_errors": schema_errors, "source_text_policy": "Only naturally occurring HTML paragraphs; no structured-field concatenation.",
              "proposed_field_coverage": {field: sum(row["proposed"]["fields"][field] is not None for row in accepted) for field in FIELDS},
              "review_status": "Automatic checks only; all category/field suggestions require human review.",
              "quality_findings": ["Candidate proposals are not extraction gold.", "Natural paragraph selection often omits details elsewhere on a page. Missing fields must be annotated against the stored input, not the full page.",
                                   "Source diversity is not balanced class coverage; repeated annual competition pages may share templates.", "Automated duplicate-page exclusions and character-decoding repairs are separately preserved."]}
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "pilot_audit.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
