# app/main.py
from fastapi import FastAPI

from app.api.v1.routes import router as api_v1_router
from app.db.session import init_db

app = FastAPI(
    title="Neuro TG Content Maker",
    version="0.1.0",
)

init_db()

# добавляем префикс /v1
app.include_router(api_v1_router, prefix="/v1")


@app.get("/")
async def root():
    return {"message": "Neuro TG Content Maker API is running"}
