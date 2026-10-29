"""FastAPI adapter. No data annotation writes in the main analysis flow."""
import json
from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from event_nlp.config import DATA, REPORTS, ROOT, CATEGORIES
from event_nlp.taxonomy import DEFINITIONS
from event_nlp.service import analyze
from .schemas import AnalysisResponse

app = FastAPI(title="EventLens · Hybrid NLP", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


class Announcement(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    reference_date: date | None = None
    include_analysis: bool = False
    extraction_mode: Literal["rules", "hybrid"] = "hybrid"
    classifier: Literal["auto", "keywords", "nltk_nb", "logistic_raw", "logistic_preprocessed", "logistic_word_char"] = "auto"

    @field_validator("text")
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError("Enter an English event announcement")
        return value


def saved_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


@app.get("/api/health")
def health():
    from event_nlp.linguistics import analyze_language, preprocess
    try:
        analyze_language("Check the event.")
        preprocess("Students are learning.")
        resources = True
    except LookupError:
        resources = False
    return {"status": "ok" if resources else "setup_required", "nltk_resources": resources, "version": "2.0.0",
            "expanded_model": (ROOT / "models/expanded_v2.pkl").exists(), "category_count": len(CATEGORIES),
            "reviewed_model": (ROOT / "models/reviewed.pkl").exists(), "development_model": (ROOT / "models/development.pkl").exists()}


@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze_announcement(announcement: Announcement):
    try:
        return analyze(announcement.text, announcement.reference_date.isoformat() if announcement.reference_date else None,
                       announcement.include_analysis, announcement.extraction_mode, announcement.classifier)
    except LookupError as error:
        raise HTTPException(status_code=503, detail="NLTK resources missing. Run: python -m scripts.download_nltk") from error
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/api/evaluation")
def evaluation():
    runs = {}
    for mode in ["expanded_v2", "reviewed_v2", "development", "provisional", "reviewed"]:
        directory = REPORTS / mode
        manifest = saved_json(directory / "manifest.json")
        if manifest:
            runs[mode] = {"manifest": manifest, "validation": saved_json(directory / "validation_metrics.json"), "test": saved_json(directory / "test_metrics.json")}
    return {"collection": saved_json(DATA / "collection_summary.json"), "runs": runs,
            "expanded_dataset": saved_json(DATA / "expanded_v2/manifest.json"),
            "expanded_extraction": saved_json(REPORTS / "expanded_v2/extraction_validation.json"),
            "expanded_final_extraction": saved_json(REPORTS / "expanded_v2/extraction_test.json"),
            "extraction_development": saved_json(REPORTS / "extraction_development.json"),
            "extraction_final": saved_json(REPORTS / "extraction_final.json")}


@app.get("/api/config")
def configuration():
    return {"categories": CATEGORIES, "definitions": DEFINITIONS, "default_classifier": "auto", "version": "2.0.0"}


@app.get("/api/methodology")
def methodology():
    return {"specification": (ROOT / "docs/SPECIFICATION.md").read_text(encoding="utf-8"),
            "metrics": (ROOT / "docs/METRICS.md").read_text(encoding="utf-8")}


dist = ROOT / "frontend/dist"
if (dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(dist / "assets")), name="assets")


@app.get("/")
def homepage():
    if (dist / "index.html").exists():
        return FileResponse(dist / "index.html")
    return {"message": "API ready. Build frontend with npm ci && npm run build, or start Vite on port 5173.", "docs": "/docs"}
