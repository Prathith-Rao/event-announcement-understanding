import re
from collections import Counter

from .config import CATEGORIES
from .taxonomy import KEYWORDS

def keyword_prediction(text: str) -> dict:
    scores = {category: sum(len(re.findall(r"\b" + re.escape(word) + r"(?:s)?\b", text, re.I))
                            for word in words) for category, words in KEYWORDS.items()}
    maximum = max(scores.values())
    winners = [key for key, value in scores.items() if value == maximum and value]
    return {"label": winners[0] if len(winners) == 1 else None, "scores": scores,
            "method": "keyword_rules", "needs_review": len(winners) != 1,
            "score_explanation": "Keyword occurrence counts; not probabilities."}


def nb_features(text: str, vocabulary: list[str]) -> dict:
    from .linguistics import preprocess
    words = set(preprocess(text).split())
    return {"contains(" + word + ")": word in words for word in vocabulary}


def training_vocabulary(texts: list[str], limit: int = 1500) -> list[str]:
    from .linguistics import preprocess
    counts = Counter(word for text in texts for word in set(preprocess(text).split()))
    return [word for word, _ in sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:limit]]
