from fastapi import FastAPI
from app.api.quiz import router as quiz_router

app = FastAPI(title="SABIFY AI Microservice", version="1.0.0")

app.include_router(quiz_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "sabify-ai"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)