# bot/services/api_client.py
import httpx
from typing import Any, Dict

from bot.config import API_BASE_URL


async def generate_from_channel(
    channel_username: str,
    topic: str,
    goal: str,
    audience: str,
) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/v1/generate-from-channel"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            url,
            json={
                "channel_username": channel_username,
                "topic": topic,
                "goal": goal,
                "audience": audience,
                "max_chars": 1000,
                "force_recreate_style": False,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def generate_plan(
    style_name: str,
    start_date: str,
    goal: str,
    audience: str,
    posts_per_day: int = 1,
) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/v1/plan/generate"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            url,
            json={
                "style_name": style_name,
                "start_date": start_date,
                "goal": goal,
                "audience": audience,
                "posts_per_day": posts_per_day,
            },
        )
        resp.raise_for_status()
        return resp.json()

async def generate_post_api(
    style_name: str,
    topic: str,
    goal: str,
    audience: str,
    max_chars: int = 1200,
) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/v1/generate"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            url,
            json={
                "style_name": style_name,
                "topic": topic,
                "goal": goal,
                "audience": audience,
                "max_chars": max_chars,
            },
        )
        resp.raise_for_status()
        return resp.json()

async def rename_style_api(old_name: str, new_name: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/v1/styles/rename"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            json={"old_name": old_name, "new_name": new_name},
        )
        resp.raise_for_status()
        return resp.json()

async def get_user_api(telegram_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/v1/user/{telegram_id}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def set_user_style_api(telegram_id: int, style_name: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/v1/user/set-style"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            url,
            json={"telegram_id": telegram_id, "style_name": style_name},
        )
        resp.raise_for_status()
        return resp.json()

async def confirm_plan_api(plan_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    plan_payload — это ровно то, что вернул /v1/plan/generate,
    + добавим сюда user_telegram_id на стороне бота.
    """
    url = f"{API_BASE_URL}/v1/plan/confirm"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=plan_payload)
        resp.raise_for_status()
        return resp.json()

async def autopost_next_api(telegram_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/v1/autopost/next/{telegram_id}"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url)
        resp.raise_for_status()
        return resp.json()

async def get_current_plan_api(telegram_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/v1/plan/current/{telegram_id}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        # если 404 — плана нет, вернём None
        if resp.status_code == 404:
            return {}
        resp.raise_for_status()
        return resp.json()

async def set_user_channel_api(telegram_id: int, channel_username: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/v1/user/set-channel"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            url,
            json={"telegram_id": telegram_id, "channel_username": channel_username},
        )
        resp.raise_for_status()
        return resp.json()

async def update_plan_times_api(plan_id: int, items: list[dict]) -> Dict[str, Any]:
    """
    items: список словарей вида {"item_id": int, "time": "HH:MM"}
    """
    url = f"{API_BASE_URL}/v1/plan/update-times"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            json={"plan_id": plan_id, "items": items},
        )
        resp.raise_for_status()
        return resp.json()

async def autopost_preview_api(telegram_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/v1/autopost/preview/{telegram_id}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()

async def set_channel_chat_id_api(telegram_id: int, channel_chat_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/v1/user/set-channel-chat-id"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            json={"telegram_id": telegram_id, "channel_chat_id": channel_chat_id},
        )
        resp.raise_for_status()
        return resp.json()

async def set_channel_chat_id_api_for_username(
    channel_username: str,
    channel_chat_id: int,
) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/v1/user/link-channel"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            json={
                "channel_username": channel_username,
                "channel_chat_id": channel_chat_id,
            },
        )
        resp.raise_for_status()
        return resp.json()
