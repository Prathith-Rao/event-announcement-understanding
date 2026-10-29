"""NLTK token/POS features for a supervised BIO sequence extractor."""
import re


def features(tokens: list[dict]) -> list[dict]:
    result = []
    for index, token in enumerate(tokens):
        word = token["text"]
        value = {"bias": 1.0, "lower": word.lower(), "pos": token["pos"],
                 "shape": re.sub(r"[a-z]", "x", re.sub(r"[A-Z]", "X", re.sub(r"\d", "d", word))),
                 "title": word.istitle(), "upper": word.isupper(), "digit": word.isdigit(),
                 "suffix2": word[-2:].lower(), "suffix3": word[-3:].lower()}
        for offset in (-2, -1, 1, 2):
            neighbor = index + offset
            if 0 <= neighbor < len(tokens) and tokens[neighbor]["sentence"] == token["sentence"]:
                other = tokens[neighbor]
                value[f"{offset}:lower"] = other["text"].lower()
                value[f"{offset}:pos"] = other["pos"]
                value[f"{offset}:title"] = other["text"].istitle()
            else:
                value[f"{offset}:boundary"] = True
        result.append(value)
    return result


def bio_labels(tokens: list[dict], gold: dict) -> list[str]:
    labels = ["O"] * len(tokens)
    for field, name in [("event_name", "NAME"), ("venue", "VENUE")]:
        span = gold.get(field)
        if not span:
            continue
        indices = [i for i, token in enumerate(tokens) if token["start"] >= span["start"] and token["end"] <= span["end"]]
        for order, index in enumerate(indices):
            labels[index] = ("B-" if order == 0 else "I-") + name
    return labels


def decode(text: str, tokens: list[dict], labels: list[str], marginals: list[dict]) -> list[dict]:
    spans, active = [], []

    def flush():
        if not active:
            return
        name = labels[active[0]][2:]
        start, end = tokens[active[0]]["start"], tokens[active[-1]]["end"]
        score = sum(marginals[i].get(labels[i], 0) for i in active) / len(active)
        spans.append({"field": "event_name" if name == "NAME" else "venue", "raw": text[start:end],
                      "start": start, "end": end, "normalized": None, "method": "nltk_pos_crf", "role": "event", "sequence_score": score})
        active.clear()

    for index, label in enumerate(labels):
        if label == "O":
            flush()
        elif active and (label.startswith("B-") or labels[active[0]][2:] != label[2:] or tokens[index]["sentence"] != tokens[active[-1]]["sentence"]):
            flush()
            active.append(index)
        else:
            active.append(index)
    flush()
    return spans
