"""Testy edge-case: SQL injection, puste dane, nieznane pytania, paginacja, klasyfikator."""

import pytest

from app.agent.sql_agent import SQLAgent, get_agent
from app.api.routes import _resolve_safe_image_path
from app.classifier.vehicle_classifier import map_imagenet_label

# ── Path traversal ──


def test_path_traversal_blocked(test_environment):
    with pytest.raises(FileNotFoundError):
        _resolve_safe_image_path("../../../../etc/passwd")


def test_absolute_path_blocked(test_environment):
    with pytest.raises(FileNotFoundError):
        _resolve_safe_image_path("/etc/passwd")


def test_sql_injection_blocked():
    agent = SQLAgent()
    assert agent._is_safe_sql("SELECT * FROM vehicles; DROP TABLE vehicles") is False


def test_sql_insert_blocked():
    agent = SQLAgent()
    sql = "INSERT INTO vehicles VALUES (99, 'x', 'y', 2020, 1, 'available')"
    assert agent._is_safe_sql(sql) is False


def test_sql_update_blocked():
    agent = SQLAgent()
    assert agent._is_safe_sql("UPDATE vehicles SET price = 0") is False


def test_sql_delete_blocked():
    agent = SQLAgent()
    assert agent._is_safe_sql("DELETE FROM vehicles") is False


def test_safe_select_allowed():
    agent = SQLAgent()
    assert agent._is_safe_sql("SELECT * FROM vehicles WHERE price > 100000") is True


def test_safe_with_cte_allowed():
    agent = SQLAgent()
    assert agent._is_safe_sql("WITH cte AS (SELECT 1) SELECT * FROM cte") is True


# ── Agent: puste / nieznane pytanie ──


def test_empty_question_returns_error(db_session):
    agent = get_agent()
    result = agent.ask("", db_session)
    assert result.error is not None
    assert "puste" in result.error.lower() or result.error != ""


def test_whitespace_only_question_returns_error(db_session):
    agent = get_agent()
    result = agent.ask("   ", db_session)
    assert result.error is not None


def test_unrecognized_question_returns_error(db_session):
    agent = get_agent()
    result = agent.ask("jaki jest sens zycia?", db_session)
    assert result.error is not None
    assert result.rows == []


# ── Agent: more query patterns ──


def test_agent_available_count(db_session):
    agent = get_agent()
    result = agent.ask("ile aut jest dostepnych?", db_session)
    assert result.error is None
    assert len(result.rows) == 1
    assert "available_vehicle_count" in result.columns


def test_agent_vehicles_below_price(db_session):
    agent = get_agent()
    result = agent.ask("pokaz auta ponizej 50k", db_session)
    assert result.error is None
    for row in result.rows:
        assert row["price"] < 50000


def test_agent_transaction_by_year(db_session):
    agent = get_agent()
    result = agent.ask("co kupiono w 2021?", db_session)
    assert result.error is None
    assert len(result.rows) >= 1
    for row in result.rows:
        assert "2021" in str(row.get("transaction_date", ""))


def test_agent_vehicle_history(db_session):
    agent = get_agent()
    result = agent.ask("jak szla Corolla - kto kupowal, kto sprzedawal?", db_session)
    assert result.error is None
    assert len(result.rows) >= 1
    assert "buyer" in result.columns


def test_agent_vehicle_current_owner(db_session):
    agent = get_agent()
    result = agent.ask("do kogo poszlo BMW X5?", db_session)
    assert result.error is None
    assert len(result.rows) == 1
    assert "current_owner" in result.columns


# ── Classifier: label mapping edge cases ──


def test_map_limousine_label():
    vehicle_type, is_vehicle = map_imagenet_label("limousine")
    assert vehicle_type == "samochod osobowy"
    assert is_vehicle is True


def test_map_trailer_truck_label():
    vehicle_type, is_vehicle = map_imagenet_label("trailer truck")
    assert vehicle_type == "ciezarowka"
    assert is_vehicle is True


def test_map_ambulance_label():
    vehicle_type, is_vehicle = map_imagenet_label("ambulance")
    assert vehicle_type == "inne"
    assert is_vehicle is True


def test_map_random_object_label():
    vehicle_type, is_vehicle = map_imagenet_label("laptop")
    assert vehicle_type == "inne"
    assert is_vehicle is False


def test_map_case_insensitive():
    vehicle_type, is_vehicle = map_imagenet_label("SPORTS CAR")
    assert vehicle_type == "samochod osobowy"
    assert is_vehicle is True


# ── API: paginacja ──


def test_vehicles_pagination(client):
    response = client.get("/api/vehicles?limit=2&offset=0")
    assert response.status_code == 200
    page1 = response.json()
    assert len(page1) <= 2

    response = client.get("/api/vehicles?limit=2&offset=2")
    assert response.status_code == 200
    page2 = response.json()

    ids_1 = {v["vehicle_id"] for v in page1}
    ids_2 = {v["vehicle_id"] for v in page2}
    assert ids_1.isdisjoint(ids_2), "Strony nie powinny sie pokrywac"


def test_vehicles_pagination_invalid_limit(client):
    response = client.get("/api/vehicles?limit=0")
    assert response.status_code == 422


def test_vehicles_pagination_negative_offset(client):
    response = client.get("/api/vehicles?limit=10&offset=-1")
    assert response.status_code == 422


# ── API: szczegoly pojazdu ──


def test_get_vehicle_by_id(client):
    response = client.get("/api/vehicles/1")
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_id"] == 1
    assert "brand" in data
    assert "images" in data


def test_get_vehicle_not_found(client):
    response = client.get("/api/vehicles/999")
    assert response.status_code == 404


# ── API: klasyfikacja edge cases ──


def test_classify_url_missing_url(client):
    response = client.post("/api/classify", json={"image_url": ""})
    assert response.status_code == 400


def test_classify_url_returns_classification(client):
    response = client.post(
        "/api/classify", json={"image_url": "http://example.com/car.jpg"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "vehicle_type" in data
    assert "confidence" in data
    assert "is_vehicle" in data


def test_classify_empty_file(client):
    response = client.post(
        "/api/classify/upload",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 400


def test_ask_too_short_question(client):
    response = client.post("/api/ask", json={"question": "ab"})
    assert response.status_code == 422


def test_ask_missing_question(client):
    response = client.post("/api/ask", json={})
    assert response.status_code == 422
