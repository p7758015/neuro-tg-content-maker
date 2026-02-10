# app/services/telegram_sender.py
import os
import httpx
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


async def send_telegram_message(chat_id: int, text: str, parse_mode: Optional[str] = "HTML") -> None:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан для отправки сообщений")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            API_URL,
            data={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            },
        )
        resp.raise_for_status()
