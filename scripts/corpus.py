"""All linguistic distributions come exclusively from assigned training rows."""
import argparse
import csv
import json
import math
import os
from collections import Counter

from event_nlp.config import ROOT
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp/matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from nltk import FreqDist
from nltk.collocations import BigramCollocationFinder, BigramAssocMeasures

from event_nlp.config import CATEGORIES, MODEL_LABELS, REPORTS
from event_nlp.data import read_jsonl, leakage_audit
from event_nlp.linguistics import analyze_language, preprocess


def table(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["development", "provisional", "reviewed", "expanded_v2"], default="development")
    args = parser.parse_args()
    categories = MODEL_LABELS if args.mode == "expanded_v2" else CATEGORIES
    directory = REPORTS / args.mode
    assigned = read_jsonl(directory / "assignments.jsonl")
    leakage_audit(assigned)
    rows = [row for row in assigned if row["split"] == "train"]
    output = directory / "corpus"
    output.mkdir(exist_ok=True)
    counts = Counter(row["label"] for row in rows)
    raw, cleaned = FreqDist(), FreqDist()
    per_class = {category: FreqDist() for category in categories}
    pos = {category: Counter() for category in categories}
    chunk_patterns, lengths, documents = Counter(), [], []
    chunk_examples, example_seen = [], set()
    for row in rows:
        analysis = analyze_language(row["text"])
        tokens = [token["text"] for token in analysis["tokens"]]
        lemmas = preprocess(row["text"]).split()
        raw.update(tokens)
        cleaned.update(lemmas)
        per_class[row["label"]].update(lemmas)
        pos[row["label"]].update(token["pos"] for token in analysis["tokens"])
        chunk_patterns.update((chunk["label"], chunk["pattern"]) for chunk in analysis["chunks"])
        for chunk in analysis["chunks"]:
            key = row["label"], chunk["label"], chunk["pattern"]
            if key not in example_seen:
                chunk_examples.append({"id": row["id"], "category": row["label"], "label": chunk["label"], "raw": chunk["raw"], "pattern": chunk["pattern"], "start": chunk["start"], "end": chunk["end"]})
                example_seen.add(key)
        lengths.append({"id": row["id"], "category": row["label"], "words": len(tokens), "characters": len(row["text"])})
        # Separate sentences prevent spurious cross-document/sentence bigrams.
        for sentence_index in range(len(analysis["sentences"])):
            documents.append([token["text"].lower() for token in analysis["tokens"] if token["sentence"] == sentence_index and token["text"].isalpha()])
    finder = BigramCollocationFinder.from_documents(documents)
    finder.apply_freq_filter(2)
    collocations = [{"bigram": " ".join(pair), "frequency": finder.ngram_fd[pair], "pmi": score} for pair, score in finder.score_ngrams(BigramAssocMeasures.pmi)[:30]]
    distinctive = []
    frequent = []
    for category, distribution in per_class.items():
        frequent.extend({"category": category, "word": word, "count": count} for word, count in distribution.most_common(20))
        if not distribution:
            continue
        scores = []
        for word, count in distribution.items():
            inside = (count + 1) / (distribution.N() + len(cleaned))
            outside = (cleaned[word] - count + 1) / (cleaned.N() - distribution.N() + len(cleaned))
            scores.append((word, math.log(inside / outside), count))
        distinctive.extend({"category": category, "word": word, "log_probability_ratio": score, "count": count} for word, score, count in sorted(scores, key=lambda item: -item[1])[:15])
    summary = {"partition": "train_only", "mode": args.mode, "records": len(rows), "class_counts": dict(counts),
               "raw_tokens": raw.N(), "raw_vocabulary": len(raw), "preprocessed_tokens": cleaned.N(), "preprocessed_vocabulary": len(cleaned),
               "collocation_min_frequency": 2, "collocation_statistic": "PMI within sentences; no cross-sentence pairs",
               "frequent": frequent, "distinctive": distinctive, "collocations": collocations,
               "pos": {key: dict(value) for key, value in pos.items()},
               "chunk_patterns": [{"label": key[0], "pattern": key[1], "count": count} for key, count in chunk_patterns.most_common(30)]}
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    table(output / "lengths.csv", lengths, ["id", "category", "words", "characters"])
    table(output / "frequent_words.csv", frequent, ["category", "word", "count"])
    table(output / "distinctive_words.csv", distinctive, ["category", "word", "log_probability_ratio", "count"])
    table(output / "collocations.csv", collocations, ["bigram", "frequency", "pmi"])
    table(output / "pos.csv", [{"category": category, "pos": tag, "count": count} for category, values in pos.items() for tag, count in values.items()], ["category", "pos", "count"])
    table(output / "chunk_patterns.csv", summary["chunk_patterns"], ["label", "pattern", "count"])
    table(output / "chunk_examples.csv", chunk_examples, ["id", "category", "label", "raw", "pattern", "start", "end"])
    plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(16, 8) if args.mode == "expanded_v2" else (12, 4))
    axes[0].barh(categories, [counts[key] for key in categories], color="#12776e")
    axes[0].tick_params(axis="y", labelsize=9)
    axes[0].set_title("Training class counts")
    axes[1].hist([row["words"] for row in lengths], bins=10, color="#d3934c", edgecolor="white")
    axes[1].set_title("Training announcement lengths")
    axes[1].set_xlabel("Treebank tokens")
    fig.suptitle(f"{args.mode}: training partition only")
    fig.tight_layout()
    fig.savefig(output / "coverage_lengths.png")
    plt.close(fig)
    fig, axis = plt.subplots(figsize=(15, 8) if args.mode == "expanded_v2" else (10, 4))
    supported = [category for category in categories if counts[category]]
    axis.boxplot([[row["words"] for row in lengths if row["category"] == category] for category in supported], patch_artist=True)
    axis.set_xticks(range(1, len(supported) + 1), supported, rotation=65)
    axis.set_ylabel("Treebank tokens")
    axis.set_title(f"{args.mode}: training lengths by category")
    fig.tight_layout()
    fig.savefig(output / "lengths_by_category.png")
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].bar(["Raw", "Preprocessed"], [raw.N(), cleaned.N()], color=["#12776e", "#d3934c"])
    axes[0].set_title("Token counts")
    axes[1].bar(["Raw", "Preprocessed"], [len(raw), len(cleaned)], color=["#12776e", "#d3934c"])
    axes[1].set_title("Vocabulary sizes")
    fig.tight_layout()
    fig.savefig(output / "preprocessing.png")
    plt.close(fig)
    tags = [tag for tag, _ in Counter(tag for values in pos.values() for tag, count in values.items() for _ in range(count)).most_common(10)]
    fig, axis = plt.subplots(figsize=(15, 8) if args.mode == "expanded_v2" else (10, 4))
    matrix = [[pos[category][tag] / max(1, sum(pos[category].values())) for tag in tags] for category in categories]
    image = axis.imshow(matrix, aspect="auto", cmap="YlGnBu")
    axis.set_xticks(range(len(tags)), tags)
    axis.set_yticks(range(len(categories)), categories)
    axis.set_title("Training POS distributions (row proportions)")
    fig.colorbar(image, ax=axis)
    fig.tight_layout()
    fig.savefig(output / "pos_distribution.png")
    plt.close(fig)
    for partition, filename in [("validation", "validation_metrics.json"), ("test", "test_metrics.json")]:
        path = directory / filename
        if not path.exists():
            continue
        metrics = json.loads(path.read_text(encoding="utf-8"))
        metrics = metrics.get("models", metrics)
        for name, metric in metrics.items():
            fig, axis = plt.subplots(figsize=(13, 12) if args.mode == "expanded_v2" else (7, 6))
            axis.imshow(metric["confusion_matrix"], cmap="Blues")
            axis.set_xticks(range(len(metric["labels"])), metric["labels"], rotation=65, ha="right", fontsize=8)
            axis.set_yticks(range(len(metric["labels"])), metric["labels"])
            for i, values in enumerate(metric["confusion_matrix"]):
                for j, count in enumerate(values):
                    axis.text(j, i, count, ha="center", va="center")
            axis.set(xlabel="Predicted", ylabel="True", title=f"{args.mode} / {partition} / {name}")
            fig.tight_layout()
            fig.savefig(directory / f"confusion_{partition}_{name}.png")
            plt.close(fig)
    interpretation = f"""# Training corpus interpretation ({args.mode})

Only {len(rows)} assigned training records contribute to these linguistic statistics. Class counts: {dict(counts)}.
Raw token count {raw.N()} and vocabulary {len(raw)} become {cleaned.N()} and {len(cleaned)} after filtering and POS-aware lemmatization. Lower vocabulary is not evidence of better classification; compare held-out raw/preprocessed results.

`distinctive_words.csv` ranks add-one-smoothed log class-versus-rest token probability ratios. These are descriptive training associations, not causal effects. Repeated format words can reveal template artifacts. `collocations.csv` uses sentence-local PMI and minimum frequency 2; rare pairs remain unstable at this corpus size. `pos.csv` shows linguistic composition by category; formatting and genre confound any class-specific interpretation.

`chunk_patterns.csv` reports candidate EVENT and VENUE grammars, not successfully extracted or manually confirmed entities. Proper-noun sequences can identify unfamiliar titles and locations; generic noun phrases, addresses, and names of speakers produce false candidates. Selection context is therefore necessary. The controlled extraction comparison, rather than chunk counts, measures usefulness.

Observed top five preprocessed words per category: { {category: distribution.most_common(5) for category, distribution in per_class.items()} }.

Observed high-PMI collocations after the minimum-frequency-2 filter: {collocations[:6]}. Their recurrence motivates testing bigram features, but templates and institutional names can dominate. This is a training-data observation, not held-out evidence for choosing a model.

`chunk_examples.csv` gives actual training input spans and POS patterns so each representative chunk can be checked. `lengths_by_category.png` shows the class-conditional length distributions; small supports and synthetic construction constrain interpretation.

If this is development mode, all these examples are AI-authored synthetic text. Balanced class counts and clean vocabulary reflect fixture construction and do not establish performance on real institutional announcements. Real-data training analysis will only be academically final after human review and a reviewed-mode run.
"""
    (output / "interpretation.md").write_text(interpretation, encoding="utf-8")
    print(f"Saved training-only tables, plots and interpretations to {output}")


if __name__ == "__main__":
    main()
