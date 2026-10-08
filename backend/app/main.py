from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.detector import detect_language
from app.language_map import LANGUAGES
from app.translator import Translator

app = FastAPI(title="NLTA Translation API")


class DetectRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


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


SUPPORTED = {lang.code for lang in LANGUAGES}
_translator = Translator()


def get_translator() -> Translator:
    return _translator


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    target_lang: str
    source_lang: str | None = None


@app.post("/translate")
def translate(req: TranslateRequest, translator: Translator = Depends(get_translator)):
    if req.target_lang not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: {req.target_lang}")

    source = req.source_lang or detect_language(req.text)[0]
    if source not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Unsupported source language: {source}")

    translated = translator.translate(req.text, source, req.target_lang)
    return {"translated_text": translated, "source_lang": source, "target_lang": req.target_lang}