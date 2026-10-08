from fastapi import FastAPI

app = FastAPI(title="NLTA Translation API")


@app.get("/health")
def health():
    return {"status": "ok"}