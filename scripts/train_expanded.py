"""Versioned broad-coverage classifier and entity training. Test is never predicted here."""
import argparse
import hashlib
import importlib.metadata
import json
import pickle
import random
from collections import Counter
from datetime import datetime, timezone

import nltk
import sklearn_crfsuite
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from event_nlp.classification import keyword_prediction, nb_features, training_vocabulary
from event_nlp.config import DATA, MODELS, MODEL_LABELS, REPORTS, ROOT, SEED
from event_nlp.data import read_jsonl, write_jsonl, leakage_audit
from event_nlp.evaluation import classification_metrics
from event_nlp.linguistics import analyze_language, preprocess
from event_nlp.sequence import bio_labels, features
from event_nlp.taxonomy import NON_EVENT


def predict_models(bundle: dict, texts: list[str]) -> dict:
    return {"majority": [bundle["majority"]] * len(texts),
            "keywords": [keyword_prediction(text)["label"] for text in texts],
            "nltk_nb": [bundle["nb"].classify(nb_features(text, bundle["vocabulary"])) for text in texts],
            **{f"logistic_{name}": bundle[name].predict(texts).tolist() for name in ["raw", "preprocessed", "word_char"]}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="expanded_v2")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    directory = REPORTS / args.run
    directory.mkdir(exist_ok=True, parents=True)
    if (directory / "test_metrics.json").exists() or ((directory / "manifest.json").exists() and not args.overwrite):
        raise SystemExit("Run exists/frozen. Use another run version; overwrite is only allowed before test evaluation.")
    source = DATA / "expanded_v2/records.jsonl"
    rows = read_jsonl(source)
    audit = leakage_audit(rows)
    audit["coverage"] = {split: dict(Counter(row["label"] for row in rows if row["split"] == split)) for split in ["train", "validation", "test"]}
    # Check both construction and normalized exact duplicates, without using class predictions.
    train, validation = [[row for row in rows if row["split"] == split] for split in ["train", "validation"]]
    texts, labels = [row["text"] for row in train], [row["label"] for row in train]
    val_texts, val_labels = [row["text"] for row in validation], [row["label"] for row in validation]
    print(f"Train {len(train)} / validation {len(validation)}; {len(MODEL_LABELS)} labels. Test unopened.", flush=True)
    vocabulary = training_vocabulary(texts, limit=1500)
    print("Fitting NLTK Naive Bayes on train-only lemma presence...", flush=True)
    nb = nltk.NaiveBayesClassifier.train((nb_features(text, vocabulary), label) for text, label in zip(texts, labels))
    bundle = {"nb": nb, "vocabulary": vocabulary, "majority": Counter(labels).most_common(1)[0][0], "mode": args.run,
              "labels": MODEL_LABELS, "provenance": "synthetic", "training_records": len(train)}
    selection = {}
    for name in ["raw", "preprocessed", "word_char"]:
        print(f"Fitting {name} TF-IDF logistic models...", flush=True)
        trials = []
        for regularization in [1.0, 4.0]:
            word = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                                   preprocessor=preprocess if name == "preprocessed" else None, max_features=65000)
            representation = FeatureUnion([("words", word), ("characters", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, max_features=45000, sublinear_tf=True))]) if name == "word_char" else word
            pipeline = Pipeline([("tfidf", representation), ("classifier", LogisticRegression(C=regularization, max_iter=1000, random_state=SEED))])
            pipeline.fit(texts, labels)
            metrics = classification_metrics(val_labels, pipeline.predict(val_texts).tolist(), MODEL_LABELS)
            trials.append({"C": regularization, "macro_f1": metrics["macro_f1"], "pipeline": pipeline})
        winner = max(trials, key=lambda trial: trial["macro_f1"])
        bundle[name] = winner["pipeline"]
        selection[name] = {"selected_C": winner["C"], "trials": [{"C": trial["C"], "macro_f1": trial["macro_f1"]} for trial in trials]}
        print(f"{name}: validation macro F1 {winner['macro_f1']:.4f}", flush=True)
    print("Preparing NLTK token/POS features for supervised BIO extraction...", flush=True)
    rng = random.Random(SEED)
    sequence_rows = sorted(rng.sample(train, min(4000, len(train))), key=lambda row: row["id"])
    x_train, y_train = [], []
    for index, row in enumerate(sequence_rows):
        tokens = analyze_language(row["text"])["tokens"]
        x_train.append(features(tokens))
        y_train.append(bio_labels(tokens, row["gold"]))
        if index and index % 1000 == 0:
            print(f"Prepared {index} sequence examples", flush=True)
    crf = sklearn_crfsuite.CRF(algorithm="lbfgs", c1=.1, c2=.1, max_iterations=80, all_possible_transitions=True)
    crf.fit(x_train, y_train)
    bundle["entity_crf"] = crf
    print("Sequence model trained. Saving models and validation results...", flush=True)
    predicted = predict_models(bundle, val_texts)
    metrics = {name: classification_metrics(val_labels, values, MODEL_LABELS) for name, values in predicted.items()}
    bundle["default_classifier"] = max(["word_char", "raw", "preprocessed"], key=lambda name: metrics["logistic_" + name]["macro_f1"])
    model_path = MODELS / (args.run + ".pkl")
    MODELS.mkdir(exist_ok=True)
    model_path.write_bytes(pickle.dumps(bundle))
    manifest = {"version": args.run, "mode": args.run, "label_status": "AI-authored synthetic", "provenance": "synthetic", "seed": SEED,
                "created_at": datetime.now(timezone.utc).isoformat(), "source_file": source.relative_to(ROOT).as_posix(),
                "source_hash": hashlib.sha256(source.read_bytes()).hexdigest(), "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                "split_sizes": dict(Counter(row["split"] for row in rows)), "audit": audit, "categories": MODEL_LABELS, "selection": selection,
                "default_classifier": bundle["default_classifier"], "nb_vocabulary_size": len(vocabulary), "sequence_training_records": len(sequence_rows),
                "feature_notes": "NB: 1500 train-derived binary POS-aware lemmas. LR: raw/lemmatized word unigrams+bigrams, plus an additional word/character 3–5-gram model. CRF: NLTK token/POS, shape and +/-2-token features; 4000 deterministic train-only examples. Select classifiers on validation only. Scores are uncalibrated.",
                "test_evaluated": False, "versions": {name: importlib.metadata.version(name) for name in ["nltk", "scikit-learn", "sklearn-crfsuite", "python-crfsuite"]}}
    write_jsonl(directory / "assignments.jsonl", rows)
    errors = [{"id": row["id"], "model": name, "text": row["text"], "truth": row["label"], "prediction": values[i]}
              for name, values in predicted.items() for i, row in enumerate(validation) if values[i] != row["label"]]
    for filename, value in [("manifest.json", manifest), ("validation_metrics.json", metrics), ("validation_errors.json", errors)]:
        (directory / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"saved": str(model_path), "default": bundle["default_classifier"], "validation": {name: metric["macro_f1"] for name, metric in metrics.items()}}, indent=2), flush=True)


if __name__ == "__main__":
    main()
