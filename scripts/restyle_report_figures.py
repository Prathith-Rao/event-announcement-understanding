"""Replot frozen numeric artifacts in Times New Roman; never rerun an experiment."""
import csv
import json
import os
from collections import Counter
from event_nlp.config import ROOT

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager


def main() -> None:
    directory = ROOT / "reports/expanded_v2"
    assets = ROOT / "output/overleaf/EventLens_Report/assets"
    for name in ["times.ttf", "timesbd.ttf", "timesi.ttf", "timesbi.ttf"]:
        font_manager.fontManager.addfont(ROOT / "output/overleaf/EventLens_Report/fonts" / name)
    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 12,
                         "figure.dpi": 150, "axes.spines.top": False, "axes.spines.right": False})
    summary = json.loads((directory / "corpus/summary.json").read_text(encoding="utf-8"))
    categories = list(summary["class_counts"])
    with (directory / "corpus/lengths.csv").open(encoding="utf-8") as f:
        lengths = [int(r["words"]) for r in csv.DictReader(f)]
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    axes[0].barh(categories, [summary["class_counts"][key] for key in categories], color="#12776e")
    axes[0].set_title("Training class counts")
    axes[1].hist(lengths, bins=10, color="#d3934c", edgecolor="white")
    axes[1].set_title("Training announcement lengths")
    axes[1].set_xlabel("Treebank tokens")
    fig.suptitle("expanded_v2: training partition only")
    fig.tight_layout()
    fig.savefig(assets / "coverage.png")
    plt.close(fig)
    pos = summary["pos"]
    aggregate = Counter()
    for values in pos.values():
        aggregate.update(values)
    tags = [tag for tag, _ in aggregate.most_common(10)]
    matrix = [[pos[c].get(tag, 0) / max(1, sum(pos[c].values())) for tag in tags] for c in categories]
    fig, axis = plt.subplots(figsize=(15, 8))
    im = axis.imshow(matrix, aspect="auto", cmap="YlGnBu")
    axis.set_xticks(range(len(tags)), tags)
    axis.set_yticks(range(len(categories)), categories)
    axis.set_title("Training POS distributions (row proportions)")
    fig.colorbar(im, ax=axis)
    fig.tight_layout()
    fig.savefig(assets / "pos.png")
    plt.close(fig)
    m = json.loads((directory / "test_metrics.json").read_text(encoding="utf-8"))["models"]["logistic_word_char"]
    fig, axis = plt.subplots(figsize=(13, 12))
    axis.imshow(m["confusion_matrix"], cmap="Blues")
    axis.set_xticks(range(len(m["labels"])), m["labels"], rotation=65, ha="right", fontsize=12)
    axis.set_yticks(range(len(m["labels"])), m["labels"])
    for i, row in enumerate(m["confusion_matrix"]):
        for j, count in enumerate(row):
            axis.text(j, i, count, ha="center", va="center")
    axis.set(xlabel="Predicted", ylabel="True", title="expanded_v2 / test / logistic_word_char")
    fig.tight_layout()
    fig.savefig(assets / "confusion.png")
    plt.close(fig)
    print("Restyled three report-only figures from frozen numeric artifacts.")


if __name__ == "__main__":
    main()
