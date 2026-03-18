from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class DummyClassifier:
    def classify_from_url(self, image_url: str):
        from app.classifier.vehicle_classifier import ClassificationResult

        lowered = image_url.lower()
        if "honda" in lowered or "cbr" in lowered or "vehicle_4" in lowered:
            return ClassificationResult("motocykl", "moped", 0.97, True)
        if "man" in lowered or "tgs" in lowered or "truck" in lowered or "vehicle_3" in lowered:
            return ClassificationResult("ciezarowka", "trailer truck", 0.94, True)
        return ClassificationResult("samochod osobowy", "sports car", 0.91, True)

    def classify_from_bytes(self, data: bytes):
        from app.classifier.vehicle_classifier import ClassificationResult

        return ClassificationResult("samochod osobowy", "sports car", 0.88, True)

    def classify_from_path(self, image_path: str):
        return self.classify_from_url(str(image_path))


@pytest.fixture()
def test_environment(tmp_path, monkeypatch):
    database_path = tmp_path / "vehicles.db"
    images_path = tmp_path / "images"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.resolve()}")
    monkeypatch.setenv("IMAGES_DIR", str(images_path.resolve()))
    monkeypatch.setenv("ENABLE_LLM_AGENT", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from app.agent.sql_agent import reset_agent_cache
    from app.classifier.vehicle_classifier import reset_classifier_cache
    from app.config import settings
    from app.database import reset_database

    settings.reload()
    reset_agent_cache()
    reset_classifier_cache()
    reset_database()

    yield

    reset_agent_cache()
    reset_classifier_cache()
    reset_database()


@pytest.fixture()
def db_session(test_environment):
    from app.database import configure_database, get_session_factory, init_db
    from app.seed import seed_database

    configure_database(force=True)
    init_db()
    session = get_session_factory()()
    seed_database(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(test_environment, monkeypatch):
    from fastapi.testclient import TestClient

    from app.api import routes
    from app.main import create_app

    monkeypatch.setattr(routes, "get_classifier", lambda: DummyClassifier())

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def tiny_png_bytes() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9l9XQAAAAASUVORK5CYII="
    )
