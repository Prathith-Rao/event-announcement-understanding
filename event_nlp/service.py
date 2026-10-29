"""Local inference orchestration. Learned categories are not vetoed by keyword ties."""
import hashlib
import json
import pickle
import re
from functools import lru_cache

from .classification import nb_features
from .config import CATEGORIES, MODELS, REPORTS
from .extraction import extract
from .taxonomy import NON_EVENT
from .context import explicit_format, general_discussion
from .temporal import DATE_RE, TIME_RE


@lru_cache(maxsize=4)
def load_model(mode: str):
    path = MODELS / (mode + ".pkl")
    manifest_path = REPORTS / mode / "manifest.json"
    if not path.exists() or not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != manifest["model_sha256"]:
        raise ValueError("Local model checksum mismatch; restore or retrain the trusted model")
    return pickle.loads(content)


def active_mode() -> str:
    for mode in ["reviewed_v2", "expanded_v2", "reviewed", "development"]:
        if (MODELS / (mode + ".pkl")).exists():
            return mode
    return "expanded_v2"


def analyze(text: str, reference_date=None, include_analysis=False, extraction_mode="hybrid", classifier="auto"):
    mode = active_mode()
    bundle = load_model(mode)
    scores, predicted = {}, None
    selected = classifier
    if bundle and classifier != "keywords":
        if classifier == "auto":
            selected = "logistic_" + bundle.get("default_classifier", "raw")
        if selected == "nltk_nb":
            distribution = bundle["nb"].prob_classify(nb_features(text, bundle["vocabulary"]))
            scores = {label: distribution.prob(label) for label in distribution.samples()}
        else:
            name = selected.removeprefix("logistic_")
            pipeline = bundle.get(name, bundle["raw"])
            scores = dict(zip(pipeline.classes_, pipeline.predict_proba([text])[0].tolist()))
        predicted = max(scores, key=scores.get)
    learned_label = predicted
    format_label, format_raw = explicit_format(text)
    temporal_context = bool(DATE_RE.search(text) or TIME_RE.search(text))
    invitation = bool(re.search(r"\b(?:join|attend|invited|invitation|hosting|host|held|starts?|begins?|scheduled|happening|upcoming|our next)\b", text, re.I))
    has_event_context = temporal_context or invitation
    if scores and format_label and has_event_context and not general_discussion(text):
        predicted = format_label
    elif scores and predicted == NON_EVENT and invitation and temporal_context and not general_discussion(text):
        predicted = "Other event"
    allow_event = predicted is not None and predicted != NON_EVENT and (scores.get(predicted, 0) >= .18 or invitation or format_label and temporal_context)
    result = extract(text, reference_date, extraction_mode, include_analysis,
                     entity_model=bundle.get("entity_crf") if bundle else None, allow_event=allow_event)
    result["categories"] = CATEGORIES
    result["model_status"] = "Local classifier and entity model" if bundle else "Category model unavailable; keyword fallback"
    result["training_metadata"] = {"run": mode, "provenance": bundle.get("provenance", "synthetic") if bundle else None,
                                   "training_records": bundle.get("training_records") if bundle else None,
                                   "human_reviewed": mode.startswith("reviewed")}
    if not bundle and classifier != "keywords":
        result["field_status"]["category"] = {"state": "notice", "message": "Category model unavailable; keyword fallback"}
        result["warnings"].append({"code": "model_unavailable", "message": "Category model unavailable; using keyword rules.", "field": "category", "severity": "warning"})
    if scores:
        ranked = sorted(scores.items(), key=lambda pair: -pair[1])
        result["category"] = {**result["category"], "method": selected, "suggested_label": None if predicted == NON_EVENT else predicted,
                              "model_scores": scores, "training_mode": mode,
                              "score_explanation": "Naive Bayes posterior" if selected == "nltk_nb" else "Logistic regression predict_proba",
                              "score_limitation": "Model scores are uncalibrated; they are not verified probabilities of correctness."}
        if predicted == NON_EVENT or general_discussion(text) and not invitation or not result["event_like"] and scores.get(predicted, 0) < .18:
            result["status"] = "unsupported"
            result["category"]["label"] = None
            result["fields"] = dict.fromkeys(result["fields"])
            for field in result["field_status"]:
                result["field_status"][field] = {"state": "missing", "message": "No event details identified"}
            result["warnings"] = [{"code": "unsupported_text", "message": "This appears to be general text rather than a specific event announcement.", "field": None, "severity": "warning"}]
        elif not result["multiple_events"]:
            result["category"]["label"] = predicted
            result["category"]["learned_label"] = learned_label
            result["category"]["explicit_format"] = format_raw
            result["category"]["decision_basis"] = "Explicit event format in context" if predicted != learned_label else "Trained model"
            uncertain = not format_label and ranked[0][1] - ranked[1][1] < .06
            result["category"]["needs_review"] = uncertain
            result["field_status"]["category"] = {"state": "notice" if uncertain else "ok", "message": "Category is uncertain — check the alternatives" if uncertain else None}
            result["warnings"] = [warning for warning in result["warnings"] if warning["code"] not in ("category_overlap", "unsupported_text")]
    return result
