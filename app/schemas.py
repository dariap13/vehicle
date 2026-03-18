"""Schematy Pydantic dla requestów i responsów API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    image_url: str = Field(..., description="URL obrazu do klasyfikacji")


class ClassifyResponse(BaseModel):
    vehicle_type: str = Field(..., description="Typ pojazdu")
    imagenet_class: str = Field(..., description="Oryginalna klasa ImageNet")
    confidence: float = Field(..., description="Pewność klasyfikacji (0-1)")
    is_vehicle: bool = Field(..., description="Czy rozpoznano pojazd")


class AskRequest(BaseModel):
    question: str = Field(..., description="Pytanie w języku naturalnym", min_length=3)


class AskResponse(BaseModel):
    question: str
    sql_query: str = ""
    explanation: str = ""
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    classifier_loaded: bool = False
    agent_available: bool = False
    agent_mode: str = "rule-based"
    agent_provider: str = "rule-based"
    llm_model: str | None = None
