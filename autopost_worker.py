import asyncio
import time
from typing import List

import httpx


API_BASE_URL = "http://localhost:8000/v1"  # как у тебя настроен uvicorn
INTERVAL_SECONDS = 60  # раз в минуту, настрой как нужно


async def fetch_autopost_users(client: httpx.AsyncClient) -> List[int]:
    url = f"{API_BASE_URL}/users/autopost-enabled"
    resp = await client.get(url)
    resp.raise_for_status()
    data = resp.json()
    return [u["telegram_id"] for u in data]


async def trigger_autopost_for_user(client: httpx.AsyncClient, telegram_id: int):
    url = f"{API_BASE_URL}/autopost/next/{telegram_id}"
    try:
        resp = await client.post(url)
        resp.raise_for_status()
        print(f"[autopost] OK for user {telegram_id}: {resp.json()}")
    except httpx.HTTPStatusError as e:
        # 404 «нет плана / нет запланированных постов» — это нормальная ситуация
        if e.response.status_code == 404:
            print(f"[autopost] No posts to send for user {telegram_id}: {e.response.text}")
        else:
            print(f"[autopost] Error for user {telegram_id}: {e.response.text}")
    except Exception as e:
        print(f"[autopost] Failed for user {telegram_id}: {e}")


async def main_loop():
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            try:
                users = await fetch_autopost_users(client)
                print(f"[autopost] Users with autopost enabled: {users}")
                for telegram_id in users:
                    await trigger_autopost_for_user(client, telegram_id)
            except Exception as e:
                print(f"[autopost] Loop error: {e}")

            await asyncio.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main_loop())
