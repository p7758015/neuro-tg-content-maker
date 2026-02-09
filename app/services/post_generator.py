# app/services/post_generator.py
from typing import Dict, List

from app.core.openai_client import chat_completion

SYSTEM_POST_WRITER = (
    "Ты копирайтер, который пишет посты в Telegram в заданном стиле автора.\n"
    "Строго соблюдай стиль, длину и лексику автора, не используй 'нейрословечки'."
)

def build_post_prompt(
    style: Dict,
    topic: str,
    goal: str,
    audience: str,
    max_chars: int = 1200,
) -> List[Dict[str, str]]:
    style_desc = style.get("style_description", "")
    preferred = ", ".join(style.get("preferred_phrases", [])[:15])
    stop = ", ".join(style.get("stop_phrases", [])[:15])

    user_msg = (
        f"Стиль автора:\n{style_desc}\n\n"
        f"Характерные слова/фразы: {preferred}\n"
        f"Слова/фразы, которых избегаем: {stop}\n\n"
        f"Тема поста: {topic}\n"
        f"Цель поста: {goal}\n"
        f"Целевая аудитория: {audience}\n\n"
        f"Напиши один пост для Telegram до {max_chars} символов. "
        "Без эмодзи, без хештегов. Без вступительных фраз про то, что ты нейросеть."
    )

    return [
        {"role": "system", "content": SYSTEM_POST_WRITER},
        {"role": "user", "content": user_msg},
    ]

def generate_post(style: Dict, topic: str, goal: str, audience: str) -> str:
    messages = build_post_prompt(style, topic, goal, audience)
    return chat_completion(messages, max_tokens=500)

