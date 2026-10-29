import nltk

from event_nlp.config import ROOT

RESOURCES = ["punkt_tab", "averaged_perceptron_tagger_eng", "wordnet", "omw-1.4", "stopwords"]

if __name__ == "__main__":
    target = ROOT / "nltk_data"
    target.mkdir(exist_ok=True)
    for resource in RESOURCES:
        if not nltk.download(resource, download_dir=str(target), quiet=False, raise_on_error=True):
            raise RuntimeError(f"Could not download {resource}")
    print(f"NLTK resources ready in {target}")
