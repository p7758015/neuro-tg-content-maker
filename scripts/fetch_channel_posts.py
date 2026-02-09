# scripts/fetch_channel_posts.py
import asyncio

from app.services.tg_loader import fetch_channel_posts
from app.services.style_extractor import extract_style
from app.services.post_generator import generate_post


async def main():
    username = input("Введи username канала (без https://t.me/): ").strip()
    posts = await fetch_channel_posts(username, limit=40)

    print(f"Загружено сообщений: {len(posts)}")

    sample_posts = posts[-5:]  # берём 5 последних для анализа стиля
    style = extract_style(sample_posts)

    print("\n=== КРАТКИЙ СТИЛЬ АВТОРА ===")
    print(style["style_description"])

    post = generate_post(
        style=style,
        topic="Тестовый пост в стиле автора",
        goal="проверить, насколько похоже",
        audience="та же аудитория, что у канала",
    )

    print("\n=== СГЕНЕРИРОВАННЫЙ ПОСТ ===\n")
    print(post)


if __name__ == "__main__":
    asyncio.run(main())
