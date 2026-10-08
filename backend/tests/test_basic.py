from fastapi.testclient import TestClient

from app.main import app, get_translator

client = TestClient(app)


class FakeTranslator:
    def translate(self, text, source, target):
        return f"[{source}->{target}] {text}"


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


def test_translate_uses_translator_and_detects_source():
    app.dependency_overrides[get_translator] = lambda: FakeTranslator()
    try:
        response = client.post(
            "/translate",
            json={"text": "Bonjour tout le monde, comment allez-vous ?", "target_lang": "en"},
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["source_lang"] == "fr"
    assert body["translated_text"].startswith("[fr->en]")


def test_translate_rejects_unsupported_target():
    response = client.post("/translate", json={"text": "Hello", "target_lang": "xx"})
    assert response.status_code == 400