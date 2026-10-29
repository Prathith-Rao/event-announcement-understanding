"""Extraction keeps original text; classification gets a separate representation."""
import re
from functools import lru_cache

import nltk
from nltk import RegexpParser
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import TreebankWordTokenizer, PunktTokenizer

from .config import ROOT

nltk.data.path.insert(0, str(ROOT / "nltk_data"))

EVENT_GRAMMAR = r"""
    EVENT: {<DT>?<JJ.*|NN.*|CD>+<IN><DT>?<JJ.*|NN.*|CD>+}
    EVENT: {<DT>?<JJ.*|NN.*|CD>+}
"""
VENUE_GRAMMAR = r"""
    VENUE: {<NNP.*|JJ.*|NN|CD>+<IN><DT>?<NNP.*|JJ.*|NN|CD>+}
    VENUE: {<DT>?<NNP.*|JJ.*|NN|CD>+}
"""


def analyze_language(text: str) -> dict:
    """Run trained English Punkt, Treebank words, Penn POS, explicit chunk grammars."""
    sentences, tokens, chunks = [], [], []
    for start, end in PunktTokenizer("english").span_tokenize(text):
        sentence = text[start:end]
        spans = list(TreebankWordTokenizer().span_tokenize(sentence))
        words = [sentence[a:b] for a, b in spans]
        tags = nltk.pos_tag(words, lang="eng")
        sentence_index = len(sentences)
        sentences.append({"raw": sentence, "start": start, "end": end})
        local = [{"text": word, "pos": pos, "start": start + a, "end": start + b,
                  "sentence": sentence_index}
                 for (word, pos), (a, b) in zip(tags, spans)]
        tokens.extend(local)
        for label, grammar in [("EVENT", EVENT_GRAMMAR), ("VENUE", VENUE_GRAMMAR)]:
            tree = RegexpParser(grammar).parse(tags)
            index = 0
            for node in tree:
                if isinstance(node, nltk.Tree):
                    count = len(node.leaves())
                    a, b = local[index]["start"], local[index + count - 1]["end"]
                    chunks.append({"label": label, "raw": text[a:b], "start": a, "end": b,
                                   "pattern": " ".join(pos for _, pos in node.leaves())})
                    index += count
                else:
                    index += 1
    return {"sentences": sentences, "tokens": tokens, "chunks": chunks,
            "grammars": {"event": EVENT_GRAMMAR, "venue": VENUE_GRAMMAR}}


@lru_cache(maxsize=1)
def lexical_resources():
    return set(stopwords.words("english")), WordNetLemmatizer()


@lru_cache(maxsize=50000)
def lemma(word, pos):
    return lexical_resources()[1].lemmatize(word, pos)


@lru_cache(maxsize=20000)
def preprocess(text: str) -> str:
    """Classification only: alphabetic, lowercase, stopwords, POS-aware WordNet lemmas."""
    tags = []
    for sentence in nltk.sent_tokenize(text):
        tags.extend(nltk.pos_tag(nltk.word_tokenize(sentence, preserve_line=True)))
    stops, _ = lexical_resources()
    result = []
    for raw, tag in tags:
        word = raw.lower()
        if not re.fullmatch(r"[a-z]+", word) or word in stops:
            continue
        pos = {"J": "a", "V": "v", "N": "n", "R": "r"}.get(tag[0], "n")
        result.append(lemma(word, pos))
    return " ".join(result)
