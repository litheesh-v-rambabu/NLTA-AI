from fastapi.testclient import TestClient

from app.main import app, get_translator, get_cache
from app.cache import TTLCache

client = TestClient(app)


class FakeTranslator:
    def translate(self, text, source, target):
        return f"[{source}->{target}] {text}"

    def translate_batch(self, texts, source, target):
        return [f"[{source}->{target}] {t}" for t in texts]


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


def test_batch_keeps_order_and_count():
    app.dependency_overrides[get_translator] = lambda: FakeTranslator()
    try:
        response = client.post(
            "/translate/batch",
            json={
                "texts": ["Bonjour le monde", "Merci beaucoup", "Au revoir, à bientôt"],
                "target_lang": "en",
            },
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["source_lang"] == "fr"
    assert len(body["translations"]) == 3
    assert body["translations"][1].endswith("Merci beaucoup")


def test_batch_rejects_empty_list():
    response = client.post("/translate/batch", json={"texts": [], "target_lang": "en"})
    assert response.status_code == 422


def test_batch_rejects_too_many_texts():
    response = client.post(
        "/translate/batch", json={"texts": ["hello"] * 51, "target_lang": "fr"}
    )
    assert response.status_code == 422


def test_batch_rejects_unsupported_target():
    response = client.post("/translate/batch", json={"texts": ["Hello"], "target_lang": "xx"})
    assert response.status_code == 400


class CountingTranslator:
    def __init__(self):
        self.calls = []

    def translate_batch(self, texts, source, target):
        self.calls.append(list(texts))
        return [f"<{t}>" for t in texts]


def _override(translator, cache):
    app.dependency_overrides[get_translator] = lambda: translator
    app.dependency_overrides[get_cache] = lambda: cache


def test_repeated_texts_skip_the_model():
    translator, cache = CountingTranslator(), TTLCache()
    _override(translator, cache)
    try:
        body = {"texts": ["Add to cart", "Checkout"], "source_lang": "en", "target_lang": "fr"}
        first = client.post("/translate/batch", json=body).json()
        second = client.post("/translate/batch", json=body).json()
    finally:
        app.dependency_overrides.clear()
    assert first["translations"] == second["translations"] == ["<Add to cart>", "<Checkout>"]
    assert len(translator.calls) == 1  # the second request never reached the model


def test_duplicates_in_one_request_translate_once_and_keep_order():
    translator, cache = CountingTranslator(), TTLCache()
    _override(translator, cache)
    try:
        body = {"texts": ["Home", "Contact", "Home"], "source_lang": "en", "target_lang": "fr"}
        out = client.post("/translate/batch", json=body).json()
    finally:
        app.dependency_overrides.clear()
    assert out["translations"] == ["<Home>", "<Contact>", "<Home>"]
    assert translator.calls == [["Home", "Contact"]]


def test_only_uncached_texts_go_to_the_model():
    translator, cache = CountingTranslator(), TTLCache()
    _override(translator, cache)
    try:
        client.post("/translate/batch", json={"texts": ["Home"], "source_lang": "en", "target_lang": "fr"})
        out = client.post(
            "/translate/batch",
            json={"texts": ["Home", "About us"], "source_lang": "en", "target_lang": "fr"},
        ).json()
    finally:
        app.dependency_overrides.clear()
    assert out["translations"] == ["<Home>", "<About us>"]
    assert translator.calls == [["Home"], ["About us"]]


class CountingTranslator:
    def __init__(self):
        self.calls = []

    def translate_batch(self, texts, source, target):
        self.calls.append(list(texts))
        return [f"<{t}>" for t in texts]


def _override(translator, cache):
    app.dependency_overrides[get_translator] = lambda: translator
    app.dependency_overrides[get_cache] = lambda: cache


def test_repeated_texts_skip_the_model():
    translator, cache = CountingTranslator(), TTLCache()
    _override(translator, cache)
    try:
        body = {"texts": ["Add to cart", "Checkout"], "source_lang": "en", "target_lang": "fr"}
        first = client.post("/translate/batch", json=body).json()
        second = client.post("/translate/batch", json=body).json()
    finally:
        app.dependency_overrides.clear()
    assert first["translations"] == second["translations"] == ["<Add to cart>", "<Checkout>"]
    assert len(translator.calls) == 1  # the second request never reached the model


def test_duplicates_in_one_request_translate_once_and_keep_order():
    translator, cache = CountingTranslator(), TTLCache()
    _override(translator, cache)
    try:
        body = {"texts": ["Home", "Contact", "Home"], "source_lang": "en", "target_lang": "fr"}
        out = client.post("/translate/batch", json=body).json()
    finally:
        app.dependency_overrides.clear()
    assert out["translations"] == ["<Home>", "<Contact>", "<Home>"]
    assert translator.calls == [["Home", "Contact"]]


def test_only_uncached_texts_go_to_the_model():
    translator, cache = CountingTranslator(), TTLCache()
    _override(translator, cache)
    try:
        client.post("/translate/batch", json={"texts": ["Home"], "source_lang": "en", "target_lang": "fr"})
        out = client.post(
            "/translate/batch",
            json={"texts": ["Home", "About us"], "source_lang": "en", "target_lang": "fr"},
        ).json()
    finally:
        app.dependency_overrides.clear()
    assert out["translations"] == ["<Home>", "<About us>"]
    assert translator.calls == [["Home"], ["About us"]]