from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
MODELS = ROOT / "models"
SEED = 42
from .taxonomy import DEFINITIONS, NON_EVENT

CATEGORIES = list(DEFINITIONS)
MODEL_LABELS = CATEGORIES + [NON_EVENT]
FIELDS = ["event_name", "date", "time", "venue"]
