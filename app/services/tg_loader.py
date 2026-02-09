# app/services/tg_loader.py
from typing import List

from telethon import TelegramClient
from telethon.tl.types import Message

from app.core.config import settings


def _get_client() -> TelegramClient:
    if not settings.tg_api_id or not settings.tg_api_hash:
        raise RuntimeError("TG_API_ID и TG_API_HASH должны быть заданы в .env")
    client = TelegramClient(
        settings.tg_session_name,
        settings.tg_api_id,
        settings.tg_api_hash,
    )
    return client


async def fetch_channel_posts(username: str, limit: int = 50) -> List[str]:
    client = _get_client()
    await client.start()

    texts: List[str] = []
    async for msg in client.iter_messages(username, limit=limit):
        if isinstance(msg, Message) and msg.message:
            texts.append(msg.message)

    await client.disconnect()
    return list(reversed(texts))

