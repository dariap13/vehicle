def test_health_endpoint(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["agent_available"] is True
    assert payload["agent_provider"] == "rule-based"
    assert payload["llm_model"] is None


def test_classify_upload_endpoint(client, tiny_png_bytes):
    response = client.post(
        "/api/classify/upload",
        files={"file": ("sample.png", tiny_png_bytes, "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["vehicle_type"] == "samochod osobowy"
    assert payload["is_vehicle"] is True


def test_ask_endpoint_enriches_rows_with_classification(client):
    response = client.post("/api/ask", json={"question": "co ma Kowalski?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert len(payload["rows"]) == 1
    row = payload["rows"][0]
    assert row["classification_vehicle_type"] == "motocykl"
    assert "classification_confidence" in row
