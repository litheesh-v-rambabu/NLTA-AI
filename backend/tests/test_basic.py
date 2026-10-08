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