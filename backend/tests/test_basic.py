from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_languages_lists_english():
    response = client.get("/languages")
    assert response.status_code == 200
    codes = [lang["code"] for lang in response.json()]
    assert "en" in codes


def test_detect_french():
    response = client.post("/detect", json={"text": "Bonjour tout le monde, comment allez-vous ?"})
    assert response.status_code == 200
    assert response.json()["language"] == "fr"


def test_detect_rejects_empty_text():
    response = client.post("/detect", json={"text": ""})
    assert response.status_code == 422