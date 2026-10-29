"""Public response contract, including source evidence and per-field notices."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Evidence(BaseModel):
    model_config = ConfigDict(extra="allow")
    raw: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    normalized: str | None = None
    method: str
    role: str


class FieldStatus(BaseModel):
    state: Literal["ok", "missing", "notice", "needs_reference", "ambiguous"]
    message: str | None = None


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    input: str
    reference_date: str | None = None
    status: Literal["ok", "needs_review", "unsupported"]
    mode: Literal["rules", "hybrid"]
    fields: dict[str, Evidence | None]
    field_status: dict[str, FieldStatus]
    category: dict
    warnings: list[dict]
    candidates: dict[str, list[dict]]
    analysis: dict | None = None
    model_status: str
    categories: list[str]
    training_metadata: dict
