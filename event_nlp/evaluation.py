"""Metrics count wrong non-null values as BOTH false positive and false negative."""
import re

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from .config import CATEGORIES, FIELDS
from .extraction import normalize_date


def classification_metrics(truth, predicted, target_labels=None):
    # Abstentions are explicit errors in all five-class metrics; never discard them.
    targets = list(target_labels or CATEGORIES)
    labels = targets + ["ABSTAIN"]
    predicted = [value or "ABSTAIN" for value in predicted]
    report = classification_report(truth, predicted, labels=targets, output_dict=True, zero_division=0)
    return {"accuracy": accuracy_score(truth, predicted), "macro_precision": report["macro avg"]["precision"],
            "macro_recall": report["macro avg"]["recall"], "macro_f1": report["macro avg"]["f1-score"],
            "per_class": {key: report[key] for key in targets}, "labels": labels,
            "confusion_matrix": confusion_matrix(truth, predicted, labels=labels).tolist(),
            "sample_count": len(truth), "abstentions": predicted.count("ABSTAIN")}


def comparable(value, field, reference):
    if value is None:
        return None
    if field == "date":
        normalized, _ = normalize_date(value["raw"], reference)
        # Use the same deterministic normalization for gold and prediction. No guessed years.
        if normalized:
            return normalized
    return " ".join(value["raw"].casefold().split()).strip()


def extraction_metrics(rows, predictions):
    results, errors = {}, []
    complete, raw_complete, unsupported_correct = 0, 0, 0
    missing_correct = missing_total = ambiguity_correct = ambiguity_total = 0
    for field in FIELDS:
        tp = fp = fn = exact = raw_exact = absent_correct = absent_total = 0
        for row, prediction in zip(rows, predictions):
            gold, actual = row["gold"].get(field), prediction["fields"].get(field)
            expected = comparable(gold, field, row.get("reference_date"))
            got = comparable(actual, field, row.get("reference_date"))
            same = expected == got
            exact += same
            raw_exact += (gold["raw"] if gold else None) == (actual["raw"] if actual else None)
            absent_total += gold is None
            absent_correct += gold is None and actual is None
            if expected is not None and got == expected:
                tp += 1
            else:
                fp += got is not None
                fn += expected is not None
            if not same:
                errors.append({"id": row["id"], "text": row["text"], "field": field, "expected": gold, "predicted": actual,
                               "candidates": prediction["candidates"][field], "warnings": prediction["warnings"]})
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        results[field] = {"precision": precision, "recall": recall, "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0,
                          "tp": tp, "fp": fp, "fn": fn, "sample_count": len(rows), "present_gold": tp + fn,
                          "exact_match": exact / len(rows), "raw_exact_match": raw_exact / len(rows),
                          "missing_field_accuracy": absent_correct / absent_total if absent_total else None, "missing_gold": absent_total}
    ambiguity_tags = {"multiple_dates_times", "overlap", "multiple_events", "numeric_ambiguity", "relative_no_reference"}
    for row, prediction in zip(rows, predictions):
        complete += all(comparable(row["gold"].get(field), field, row.get("reference_date")) == comparable(prediction["fields"].get(field), field, row.get("reference_date")) for field in FIELDS)
        raw_complete += all((row["gold"].get(field) or {}).get("raw") == (prediction["fields"].get(field) or {}).get("raw") for field in FIELDS)
        unsupported_correct += (row.get("expected_status") == "unsupported") == (prediction["status"] == "unsupported")
        codes = {warning["code"] for warning in prediction["warnings"]}
        for field in FIELDS:
            if row["gold"].get(field) is None:
                missing_total += 1
                missing_correct += prediction["fields"].get(field) is None and ("missing_" + field in codes or "date_range" in codes or "ambiguous_" + field in codes or prediction.get("field_status", {}).get(field, {}).get("state") in ("missing", "ambiguous"))
        if set(row.get("tags", [])) & ambiguity_tags:
            ambiguity_total += 1
            expected_code = {"multiple_dates_times": "ambiguous_date", "overlap": "category_overlap", "multiple_events": "multiple_events",
                             "numeric_ambiguity": "ambiguous_numeric_date", "relative_no_reference": "relative_date_without_reference"}
            ambiguity_correct += all(expected_code[tag] in codes for tag in set(row["tags"]) & ambiguity_tags)
    return {"fields": results, "complete_record_accuracy": complete / len(rows), "raw_complete_record_accuracy": raw_complete / len(rows),
            "unsupported_detection_accuracy": unsupported_correct / len(rows), "missing_warning_accuracy": missing_correct / missing_total if missing_total else None,
            "ambiguity_warning_accuracy": ambiguity_correct / ambiguity_total if ambiguity_total else None,
            "ambiguity_cases": ambiguity_total, "sample_count": len(rows), "errors": errors}
