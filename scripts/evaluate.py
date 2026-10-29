"""Explicit frozen final evaluation, or development-only extraction evaluation."""
import argparse
import hashlib
import json
import pickle

from event_nlp.config import DATA, MODELS, REPORTS, ROOT
from event_nlp.data import read_jsonl, leakage_audit
from event_nlp.evaluation import classification_metrics, extraction_metrics
from event_nlp.extraction import extract
from scripts.experiment import dataset_hash, predictions


def evaluate_challenge(partition):
    path = REPORTS / ("extraction_" + partition + ".json")
    if partition == "final" and path.exists():
        raise SystemExit("Final challenge already evaluated. Retain this result; do not rerun after tuning.")
    source = DATA / ("challenge_" + partition + ".jsonl")
    rows = read_jsonl(source)
    result = {"provenance": "synthetic", "label_status": "AI-authored expectations; human review pending", "partition": partition,
              "dataset_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "extractor_sha256": hashlib.sha256((ROOT / "event_nlp/extraction.py").read_bytes()).hexdigest()}
    for mode in ["rules", "hybrid"]:
        outputs = [extract(row["text"], row.get("reference_date"), mode=mode) for row in rows]
        result[mode] = extraction_metrics(rows, outputs)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: {field: value for field, value in result[key].items() if field != "errors"} for key in ["rules", "hybrid"]}, indent=2))


def evaluate_test(mode):
    directory = REPORTS / mode
    if (directory / "test_metrics.json").exists():
        raise SystemExit("Final test already evaluated; saved results are immutable for this run.")
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    rows = read_jsonl(directory / "assignments.jsonl")
    leakage_audit(rows)
    model_bytes = (MODELS / (mode + ".pkl")).read_bytes()
    if dataset_hash(rows) != manifest["data_hash"] or hashlib.sha256(model_bytes).hexdigest() != manifest["model_sha256"]:
        raise SystemExit("Frozen data/model hash mismatch")
    if hashlib.sha256((ROOT / manifest["source_file"]).read_bytes()).hexdigest() != manifest["source_hash"]:
        raise SystemExit("Source data changed since training; create a fresh experiment before final evaluation")
    bundle = pickle.loads(model_bytes)  # Only locally generated, hash-checked artifacts.
    test = [row for row in rows if row["split"] == "test"]
    truth = [row["label"] for row in test]
    output = predictions(bundle, [row["text"] for row in test])
    result = {"mode": mode, "label_status": manifest["label_status"], "data_hash": manifest["data_hash"],
              "models": {name: classification_metrics(truth, values) for name, values in output.items()},
              "errors": [{"id": row["id"], "text": row["text"], "truth": row["label"], "model": name, "prediction": values[i]}
                         for name, values in output.items() for i, row in enumerate(test) if values[i] != row["label"]]}
    # Extraction on exactly the same human-reviewed real test records, if available.
    if mode == "reviewed":
        gold_rows = [{**row, "gold": row["human"]["fields"]} for row in test]
        result["real_extraction"] = {method: extraction_metrics(gold_rows, [extract(row["text"], row.get("reference_date"), mode=method) for row in test]) for method in ["rules", "hybrid"]}
    (directory / "test_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest["test_evaluated"] = True
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"label_status": result["label_status"], "models": {name: {key: value[key] for key in ["accuracy", "macro_f1", "sample_count"]} for name, value in result["models"].items()}}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--challenge", choices=["development", "final"])
    parser.add_argument("--test", choices=["development", "reviewed"])
    arguments = parser.parse_args()
    if bool(arguments.challenge) == bool(arguments.test):
        parser.error("Choose exactly one of --challenge or --test")
    REPORTS.mkdir(exist_ok=True)
    evaluate_challenge(arguments.challenge) if arguments.challenge else evaluate_test(arguments.test)
