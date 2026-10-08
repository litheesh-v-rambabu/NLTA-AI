from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.detector import detect_language
from app.language_map import LANGUAGES

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