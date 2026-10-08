from fastapi import FastAPI

from app.language_map import LANGUAGES

app = FastAPI(title="NLTA Translation API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/languages")
def list_languages():
    return [{"code": lang.code, "name": lang.name} for lang in LANGUAGES]