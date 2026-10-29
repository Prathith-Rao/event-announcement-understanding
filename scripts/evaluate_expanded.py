"""Explicit version-2 evaluation. Historical final challenges are never loaded."""
import argparse
import hashlib
import json
from datetime import datetime, timezone

from event_nlp.config import DATA, MODEL_LABELS, REPORTS, ROOT
from event_nlp.data import read_jsonl, write_jsonl, leakage_audit
from event_nlp.evaluation import classification_metrics, extraction_metrics
from event_nlp.service import analyze, load_model
from event_nlp.taxonomy import NON_EVENT
from scripts.train_expanded import predict_models


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--partition", choices=["validation", "test"], default="validation")
    args = parser.parse_args()
    directory = REPORTS / "expanded_v2"
    path = directory / ("extraction_" + args.partition + ".json")
    if args.partition == "test" and path.exists():
        raise SystemExit("Version-2 final test is frozen. Save a new run version for further development.")
    source = DATA / "expanded_v2/records.jsonl"
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if hashlib.sha256(source.read_bytes()).hexdigest() != manifest["source_hash"]:
        raise SystemExit("Training dataset hash mismatch")
    rows = read_jsonl(source)
    leakage_audit(rows)
    rows = [row for row in rows if row["split"] == args.partition]
    rows = [{**row, "expected_status": "unsupported" if row["label"] == NON_EVENT else "ok"} for row in rows]
    bundle = load_model("expanded_v2")
    predictions = predict_models(bundle, [row["text"] for row in rows])
    metrics = {name: classification_metrics([row["label"] for row in rows], values, MODEL_LABELS) for name, values in predictions.items()}
    classifier_output = {"mode": "expanded_v2", "label_status": "AI-authored synthetic", "partition": args.partition, "models": metrics,
                         "errors": [{"id": row["id"], "text": row["text"], "model": name, "truth": row["label"], "prediction": values[i]}
                                    for name, values in predictions.items() for i, row in enumerate(rows) if row["label"] != values[i]]}
    result = {"partition": args.partition, "provenance": "synthetic", "label_status": "Authored expectations; not human-reviewed real-data results",
              "extractor_sha256": hashlib.sha256((ROOT / "event_nlp/extraction.py").read_bytes()).hexdigest(),
              "temporal_sha256": hashlib.sha256((ROOT / "event_nlp/temporal.py").read_bytes()).hexdigest(),
              "data_sha256": manifest["source_hash"]}
    result["code_sha256"] = {name: hashlib.sha256((ROOT / "event_nlp" / name).read_bytes()).hexdigest() for name in ["extraction.py", "temporal.py", "service.py", "context.py", "sequence.py", "linguistics.py"]}
    result["evaluated_at"] = datetime.now(timezone.utc).isoformat()
    for method in ["rules", "hybrid"]:
        output = []
        for index, row in enumerate(rows):
            output.append(analyze(row["text"], row.get("reference_date"), extraction_mode=method))
            if index and index % 500 == 0:
                print(f"{method}: {index}/{len(rows)}", flush=True)
        result[method] = extraction_metrics(rows, output)
        if method == "hybrid":
            system_labels = [prediction["category"]["label"] or NON_EVENT for prediction in output]
            classifier_output["models"]["hybrid_context"] = classification_metrics([row["label"] for row in rows], system_labels, MODEL_LABELS)
        write_jsonl(directory / f"predictions_{args.partition}_{method}.jsonl", [{"id": row["id"], **prediction} for row, prediction in zip(rows, output)])
    (directory / ("test_metrics.json" if args.partition == "test" else "validation_metrics_bundle.json")).write_text(json.dumps(classifier_output, indent=2), encoding="utf-8")
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({method: {"complete_record": result[method]["complete_record_accuracy"],
                              "field_f1": {field: metric["f1"] for field, metric in result[method]["fields"].items()}} for method in ["rules", "hybrid"]}, indent=2))
    if args.partition == "test":
        manifest["test_evaluated"] = True
        (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
