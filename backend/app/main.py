from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, StringConstraints

from app.detector import detect_language
from app.language_map import LANGUAGES
from app.translator import Translator

app = FastAPI(title="NLTA Translation API")

SUPPORTED = {lang.code for lang in LANGUAGES}
_translator = Translator()

NonEmptyText = Annotated[str, StringConstraints(min_length=1, max_length=5000)]


def get_translator() -> Translator:
    return _translator


class DetectRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    target_lang: str
    source_lang: str | None = None


class BatchTranslateRequest(BaseModel):
    texts: list[NonEmptyText] = Field(min_length=1, max_length=50)
    target_lang: str
    source_lang: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/languages")
def list_languages():
    return [{"code": lang.code, "name": lang.name} for lang in LANGUAGES]


@app.post("/detect")
def detect(req: DetectRequest):
    language, confidence = detect_language(req.text)
    return {"language": language, "confidence": confidence}


@app.post("/translate")
def translate(req: TranslateRequest, translator: Translator = Depends(get_translator)):
    if req.target_lang not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: {req.target_lang}")

    source = req.source_lang or detect_language(req.text)[0]
    if source not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Unsupported source language: {source}")

    translated = translator.translate(req.text, source, req.target_lang)
    return {"translated_text": translated, "source_lang": source, "target_lang": req.target_lang}


@app.post("/translate/batch")
def translate_batch(req: BatchTranslateRequest, translator: Translator = Depends(get_translator)):
    if req.target_lang not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: {req.target_lang}")

    # Detect once from the combined text: more text gives a more reliable guess than short strings.
    source = req.source_lang or detect_language(" ".join(req.texts)[:2000])[0]
    if source not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Unsupported source language: {source}")

    translations = translator.translate_batch(req.texts, source, req.target_lang)
    return {"translations": translations, "source_lang": source, "target_lang": req.target_lang}