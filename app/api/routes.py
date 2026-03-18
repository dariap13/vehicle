"""Endpointy REST API."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.agent.sql_agent import get_agent
from app.classifier.vehicle_classifier import ClassificationResult, get_classifier
from app.config import settings
from app.database import get_db
from app.models import Vehicle, VehicleImage
from app.schemas import (
    AskRequest,
    AskResponse,
    ClassifyRequest,
    ClassifyResponse,
    HealthResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["API"])

CLASSIFICATION_COLUMNS = [
    "classification_vehicle_type",
    "classification_confidence",
    "classification_imagenet_class",
    "classification_is_vehicle",
]


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    try:
        get_classifier()
        classifier_ok = True
    except Exception:
        classifier_ok = False

    agent = get_agent()
    return HealthResponse(
        status="ok",
        classifier_loaded=classifier_ok,
        agent_available=agent.is_available,
        agent_mode=agent.mode,
        agent_provider=agent.provider if agent.mode != "rule-based" else "rule-based",
        llm_model=agent.model,
    )


@router.post("/classify", response_model=ClassifyResponse)
def classify_from_url(request: ClassifyRequest) -> ClassifyResponse:
    if not request.image_url:
        raise HTTPException(status_code=400, detail="Podaj image_url.")

    classifier = get_classifier()
    try:
        result = classifier.classify_from_url(request.image_url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Nie udalo sie pobrac obrazu: {exc}") from exc

    return _to_classify_response(result)


@router.post("/classify/upload", response_model=ClassifyResponse)
async def classify_from_upload(file: UploadFile = File(...)) -> ClassifyResponse:
    classifier = get_classifier()
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Przeslany plik jest pusty.")

    try:
        result = classifier.classify_from_bytes(data)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Nie udalo sie sklasyfikowac pliku: {exc}",
        ) from exc

    return _to_classify_response(result)


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest, db: Session = Depends(get_db)) -> AskResponse:
    agent = get_agent()
    result = agent.ask(request.question, db)

    if result.sql_query:
        logger.info("Pytanie: %s", request.question)
        logger.info("SQL: %s", result.sql_query)
        logger.info("Wyjasnienie: %s", result.explanation)
    if result.error:
        logger.warning("Blad agenta: %s", result.error)

    rows = result.rows
    columns = result.columns
    if not result.error:
        rows, columns = _append_classification_columns(result.rows, result.columns, db)

    return AskResponse(
        question=request.question,
        sql_query=result.sql_query,
        explanation=result.explanation,
        columns=columns,
        rows=rows,
        error=result.error,
    )


@router.get("/vehicles")
def list_vehicles(db: Session = Depends(get_db)) -> list[dict]:
    vehicles = db.query(Vehicle).all()
    return [
        {
            "vehicle_id": vehicle.vehicle_id,
            "brand": vehicle.brand,
            "model": vehicle.model,
            "year": vehicle.year,
            "price": float(vehicle.price),
            "availability": vehicle.availability,
            "images": [
                {"image_id": image.image_id, "image_url": image.image_url}
                for image in vehicle.images
            ],
        }
        for vehicle in vehicles
    ]


def _append_classification_columns(
    rows: list[dict],
    columns: list[str],
    db: Session,
) -> tuple[list[dict], list[str]]:
    if not rows:
        merged_columns = list(dict.fromkeys(columns + CLASSIFICATION_COLUMNS))
        return rows, merged_columns

    classifier = None
    try:
        classifier = get_classifier()
    except Exception as exc:
        logger.warning("Klasyfikator niedostepny: %s", exc)

    enriched_rows: list[dict] = []
    for row in rows:
        enriched_row = dict(row)
        image_reference = _resolve_image_reference(enriched_row, db)
        if image_reference and "image_url" not in enriched_row:
            enriched_row["image_url"] = image_reference

        classification_payload = _empty_classification_payload()
        if classifier and image_reference:
            try:
                classification = _classify_image(classifier, image_reference)
                classification_payload = {
                    "classification_vehicle_type": classification.vehicle_type,
                    "classification_confidence": round(classification.confidence, 4),
                    "classification_imagenet_class": classification.imagenet_class,
                    "classification_is_vehicle": classification.is_vehicle,
                }
            except Exception as exc:
                logger.warning(
                    "Klasyfikacja nieudana dla vehicle_id=%s: %s",
                    row.get("vehicle_id"),
                    exc,
                )

        enriched_row.update(classification_payload)
        enriched_rows.append(enriched_row)

    merged_columns = list(dict.fromkeys(columns + ["image_url"] + CLASSIFICATION_COLUMNS))
    return enriched_rows, merged_columns


def _resolve_image_reference(row: dict, db: Session) -> str | None:
    image_url = row.get("image_url")
    if image_url:
        return image_url

    vehicle_id = row.get("vehicle_id")
    if vehicle_id is None:
        return None

    image = db.query(VehicleImage).filter(VehicleImage.vehicle_id == vehicle_id).first()
    return image.image_url if image else None


def _empty_classification_payload() -> dict[str, str | float | bool | None]:
    return {
        "classification_vehicle_type": None,
        "classification_confidence": None,
        "classification_imagenet_class": None,
        "classification_is_vehicle": None,
    }


def _classify_image(classifier, image_reference: str) -> ClassificationResult:
    if image_reference.startswith(("http://", "https://")):
        return classifier.classify_from_url(image_reference)

    full_path = settings.project_root / image_reference
    if not full_path.exists():
        full_path = settings.images_dir / Path(image_reference).name
    if not full_path.exists():
        full_path = Path(image_reference)
    if not full_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {image_reference}")
    return classifier.classify_from_path(full_path)


def _to_classify_response(result: ClassificationResult) -> ClassifyResponse:
    return ClassifyResponse(
        vehicle_type=result.vehicle_type,
        imagenet_class=result.imagenet_class,
        confidence=result.confidence,
        is_vehicle=result.is_vehicle,
    )
