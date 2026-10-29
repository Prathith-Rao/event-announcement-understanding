import hashlib
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from .config import CATEGORIES, FIELDS, SEED


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()] if path.exists() else []


def write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def fingerprint(text: str) -> str:
    clean = re.sub(r"\b(?:jan\w*|feb\w*|mar\w*|apr\w*|may|jun\w*|jul\w*|aug\w*|sep\w*|oct\w*|nov\w*|dec\w*)\b|\d+", "#", text.lower())
    return " ".join(re.findall(r"\w+|#", clean))


def group_records(rows: list[dict]) -> list[dict]:
    """Union existing template IDs, exact normalized duplicates and high sequence similarity."""
    parents = list(range(len(rows)))

    def root(i):
        while i != parents[i]:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    fingerprints = [fingerprint(row["text"]) for row in rows]
    def source_template(row):
        url = (row.get("source_url") or "").split("?")[0].rstrip("/")
        # Annual pages of the same event series belong together even when prose changed.
        url = re.sub(r"20[0-2]\d", "YEAR", url)
        if "teaching-and-learning.hsu.edu.hk/" in url:
            url = url.replace("hsmc-", "hsuhk-").replace("hsuhk-social-innovation-", "hsuhk-innovation-")
        return url
    source_templates = [source_template(row) for row in rows]
    for i in range(len(rows)):
        for j in range(i):
            same_template = bool(rows[i].get("group_id") and rows[i].get("group_id") == rows[j].get("group_id"))
            same_page = bool(rows[i].get("source_url") and rows[j].get("source_url") and rows[i]["source_url"].split("?")[0].rstrip("/") == rows[j]["source_url"].split("?")[0].rstrip("/"))
            same_series = bool(source_templates[i] and source_templates[i] == source_templates[j])
            if same_template or same_page or same_series or fingerprints[i] == fingerprints[j] or SequenceMatcher(None, fingerprints[i], fingerprints[j]).ratio() >= 0.84:
                parents[root(i)] = root(j)
    groups = {}
    for i, row in enumerate(rows):
        group = root(i)
        groups.setdefault(group, "g-" + hashlib.sha256("|".join(sorted(r["id"] for k, r in enumerate(rows) if root(k) == group)).encode()).hexdigest()[:12])
        row["group_id"] = groups[group]
    return rows


def split_records(rows: list[dict]) -> tuple[list[dict], dict]:
    """Select deterministic group allocations for coverage/size using labels, never model outcomes."""
    import numpy as np
    groups = sorted(set(row["group_id"] for row in rows))
    if len(groups) < 5:
        raise ValueError("Need at least five independent groups for train/validation/test.")
    supported = {row["label"] for row in rows}
    best = None
    for attempt in range(300):
        order = np.random.default_rng(SEED + attempt).permutation(groups).tolist()
        n_test = max(1, round(len(groups) * 0.2))
        n_val = max(1, round(len(groups) * 0.2))
        allocation = {g: "test" if i < n_test else "validation" if i < n_test + n_val else "train" for i, g in enumerate(order)}
        sizes = Counter(allocation[row["group_id"]] for row in rows)
        missing = sum(len(supported - {row["label"] for row in rows if allocation[row["group_id"]] == split}) for split in ("train", "validation", "test"))
        missing_train = len(supported - {row["label"] for row in rows if allocation[row["group_id"]] == "train"})
        score = missing_train * 10000 + missing * 1000 + sum(abs(sizes[split] / len(rows) - fraction) for split, fraction in [("train", .6), ("validation", .2), ("test", .2)])
        if best is None or score < best[0]:
            best = score, allocation
    for row in rows:
        row["split"] = best[1][row["group_id"]]
    audit = leakage_audit(rows)
    audit["coverage"] = {split: dict(Counter(row["label"] for row in rows if row["split"] == split)) for split in ("train", "validation", "test")}
    audit["unsupported_classes"] = sorted(set(CATEGORIES) - supported)
    audit["unsupported_by_split"] = {split: sorted(set(CATEGORIES) - set(audit["coverage"][split])) for split in ("train", "validation", "test")}
    return rows, audit


def leakage_audit(rows: list[dict]) -> dict:
    groups, texts, ids = {}, {}, set()
    for row in rows:
        if row["id"] in ids:
            raise ValueError("Duplicate record ID")
        ids.add(row["id"])
        for key, registry in [(row["group_id"], groups), (fingerprint(row["text"]), texts)]:
            if key in registry and registry[key] != row["split"]:
                raise ValueError("Leakage: duplicate/template crosses split boundary")
            registry[key] = row["split"]
    return {"group_overlap": 0, "normalized_duplicate_overlap": 0, "groups": len(groups), "records": len(rows)}


def validate_human(row: dict, human: dict) -> None:
    if human.get("category") not in CATEGORIES + [None]:
        raise ValueError("Invalid category")
    if not human.get("reviewer", "").strip() or not human.get("reviewed_at"):
        raise ValueError("Human reviewer and timestamp required")
    if human.get("decision") not in ["accepted", "needs_review", "excluded"]:
        raise ValueError("Explicit review decision required")
    if human.get("decision") == "accepted" and human.get("category") not in CATEGORIES:
        raise ValueError("Accepted classification requires an unambiguous category")
    if set(human.get("fields", {})) != set(FIELDS):
        raise ValueError("Every field needs a value or explicit null")
    for field, value in human["fields"].items():
        if value is not None:
            if not isinstance(value, dict) or not value.get("raw"):
                raise ValueError(f"{field}: raw evidence required")
            start, end = value.get("start"), value.get("end")
            if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= len(row["text"]) or row["text"][start:end] != value["raw"]:
                raise ValueError(f"{field}: evidence offsets do not match original text")
