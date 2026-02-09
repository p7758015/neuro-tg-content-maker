# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    openai_api_key: str
    model: str = "gpt-4.1-mini"
    temperature: float = 0.7
    max_tokens: int = 400

    tg_api_id: int | None = None
    tg_api_hash: str | None = None
    tg_session_name: str = "neuro_tg_session"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # на всякий случай игнорировать лишнее
    )

settings = Settings()


