from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.quiz import router as quiz_router
from app.core.config import settings

app = FastAPI(title="SABIFY AI Microservice", version="1.0.0")
app.include_router(quiz_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "sabify-ai"}


frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
    )