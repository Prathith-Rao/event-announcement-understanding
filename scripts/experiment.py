"""Fit on train; choose C on validation. No test predictions are made here."""
import argparse
import hashlib
import importlib.metadata
import json
import pickle
from collections import Counter
from datetime import datetime, timezone

import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from event_nlp.classification import keyword_prediction, nb_features, training_vocabulary
from event_nlp.config import DATA, MODELS, REPORTS, SEED
from event_nlp.data import group_records, read_jsonl, split_records, write_jsonl, validate_human
from event_nlp.evaluation import classification_metrics
from event_nlp.linguistics import preprocess


def dataset_hash(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def predictions(bundle, texts):
    return {"majority": [bundle["majority"]] * len(texts),
            "keywords": [keyword_prediction(text)["label"] for text in texts],
            "nltk_nb": [bundle["nb"].classify(nb_features(text, bundle["vocabulary"])) for text in texts],
            "logistic_raw": bundle["raw"].predict(texts).tolist(),
            "logistic_preprocessed": bundle["preprocessed"].predict(texts).tolist()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["development", "provisional", "reviewed"], default="development")
    parser.add_argument("--overwrite", action="store_true", help="Retrain only before any final evaluation; previous final runs are immutable")
    args = parser.parse_args()
    directory = REPORTS / args.mode
    directory.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(exist_ok=True)
    if (directory / "test_metrics.json").exists():
        raise SystemExit("This run has been finally evaluated. Create a new dataset/versioned run; do not tune against its test results.")
    if (directory / "manifest.json").exists() and not args.overwrite:
        raise SystemExit("Run already exists; use --overwrite only while final test remains unopened.")
    source = DATA / ("synthetic_development.jsonl" if args.mode == "development" else "real.jsonl")
    rows = read_jsonl(source)
    if args.mode == "reviewed":
        rows = [row for row in rows if row.get("human") and row["human"]["decision"] == "accepted"]
        for row in rows:
            validate_human(row, row["human"])
            row["label"] = row["human"]["category"]
    elif args.mode == "provisional":
        rows = [row for row in rows if row["proposed"]["category"]]
        for row in rows:
            row["label"] = row["proposed"]["category"]
    if not rows or len(set(row["label"] for row in rows)) < 2:
        raise SystemExit("Insufficient eligible labels: need at least two classes and five independent groups. Continue human review.")
    rows, audit = split_records(group_records(rows))
    train = [row for row in rows if row["split"] == "train"]
    validation = [row for row in rows if row["split"] == "validation"]
    if len(set(row["label"] for row in train)) < 2:
        raise SystemExit("Grouped training partition has fewer than two classes.")
    texts, labels = [row["text"] for row in train], [row["label"] for row in train]
    val_text, val_labels = [row["text"] for row in validation], [row["label"] for row in validation]
    vocabulary = training_vocabulary(texts)
    nb = nltk.NaiveBayesClassifier.train([(nb_features(text, vocabulary), label) for text, label in zip(texts, labels)])
    bundle = {"majority": Counter(labels).most_common(1)[0][0], "nb": nb, "vocabulary": vocabulary,
              "mode": args.mode, "data_hash": dataset_hash(rows)}
    selection = {}
    for name, preprocessor in [("raw", None), ("preprocessed", preprocess)]:
        trials = []
        for c in [.5, 2.0]:
            pipeline = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, preprocessor=preprocessor)),
                                 ("classifier", LogisticRegression(C=c, random_state=SEED, max_iter=1500))])
            pipeline.fit(texts, labels)
            score = classification_metrics(val_labels, pipeline.predict(val_text).tolist())["macro_f1"]
            trials.append({"C": c, "validation_macro_f1": score, "pipeline": pipeline})
        winner = max(trials, key=lambda trial: trial["validation_macro_f1"])
        bundle[name] = winner["pipeline"]
        selection[name] = {"selected_C": winner["C"], "trials": [{key: value for key, value in trial.items() if key != "pipeline"} for trial in trials]}
    result = predictions(bundle, val_text)
    metrics = {name: classification_metrics(val_labels, values) for name, values in result.items()}
    errors = [{"id": row["id"], "text": row["text"], "truth": row["label"], "model": name, "prediction": values[index]}
              for name, values in result.items() for index, row in enumerate(validation) if values[index] != row["label"]]
    manifest = {"mode": args.mode, "seed": SEED, "label_status": "human reviewed" if args.mode == "reviewed" else "AI-authored synthetic" if args.mode == "development" else "automatic provisional labels",
                "source_file": str(source.relative_to(DATA.parent)), "data_hash": bundle["data_hash"], "source_hash": hashlib.sha256(source.read_bytes()).hexdigest(),
                "created_at": datetime.now(timezone.utc).isoformat(), "split_sizes": dict(Counter(row["split"] for row in rows)),
                "audit": audit, "selection": selection, "nb_vocabulary_size": len(vocabulary), "nb_vocabulary": vocabulary,
                "feature_notes": "NB: train-derived binary presence of POS-aware lemmas, top 1500 by document frequency. LR: TF-IDF unigrams/bigrams with sublinear TF; raw versus POS-aware lemmas use identical rows. NB vs LR changes both representation and algorithm.",
                "test_evaluated": False, "versions": {name: importlib.metadata.version(name) for name in ["nltk", "scikit-learn", "numpy", "python-dateutil"]}}
    with (MODELS / (args.mode + ".pkl")).open("wb") as file:
        pickle.dump(bundle, file)
    manifest["model_sha256"] = hashlib.sha256((MODELS / (args.mode + ".pkl")).read_bytes()).hexdigest()
    write_jsonl(directory / "assignments.jsonl", rows)
    # Also keep a concise split map alongside the available dataset.
    (DATA / ("splits_" + args.mode + ".json")).write_text(json.dumps({row["id"]: {"group_id": row["group_id"], "split": row["split"]} for row in rows}, indent=2), encoding="utf-8")
    for filename, value in [("manifest.json", manifest), ("validation_metrics.json", metrics), ("validation_errors.json", errors)]:
        (directory / filename).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"manifest": manifest, "validation": {name: {key: value[key] for key in ["accuracy", "macro_f1", "sample_count"]} for name, value in metrics.items()}}, indent=2))


if __name__ == "__main__":
    main()
