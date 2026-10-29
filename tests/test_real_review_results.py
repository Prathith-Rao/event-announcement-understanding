"""Audit the independently reviewed evaluation artifact, without reopening either test run."""
import hashlib
import json
from event_nlp.config import ROOT, MODEL_LABELS


def test_real_gold_has_exact_evidence_and_preserves_collection_text():
    original={r["id"]:r for r in map(json.loads,(ROOT/"data/real_review/records.jsonl").read_text(encoding="utf-8").splitlines())}
    gold=json.loads((ROOT/"reports/real_review_v1/gold.json").read_text(encoding="utf-8"))
    assert len({r["id"] for r in gold})==len(gold)==59
    for row in gold:
        assert row["text"]==original[row["id"]]["text"]
        assert row["label"] in MODEL_LABELS and row["provenance"]=="real"
        for field in row["gold"].values():
            if field:
                assert row["text"][field["start"]:field["end"]]==field["raw"]


def test_real_run_did_not_change_the_frozen_model_or_synthetic_test():
    real=json.loads((ROOT/"reports/real_review_v1/metrics.json").read_text(encoding="utf-8"))
    manifest=json.loads((ROOT/"reports/expanded_v2/manifest.json").read_text(encoding="utf-8"))
    digest=hashlib.sha256((ROOT/"models/expanded_v2.pkl").read_bytes()).hexdigest()
    assert digest==real["model_sha256"]==manifest["model_sha256"]
    assert real["training_performed"] is False
    assert real["decisions"]=={"accepted":59,"needs_review":19,"excluded":4}
    assert sum(real["class_counts"].values())==59
    assert manifest["test_evaluated"] is True
    assert real["new_post_freeze_records"]==34
