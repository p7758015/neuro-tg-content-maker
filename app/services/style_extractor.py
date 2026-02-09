# app/services/style_extractor.py
from typing import List, Dict
import json

from app.core.openai_client import chat_completion

SYSTEM_STYLE_ANALYZER = (
    "Ты маркетолог и копирайтер. "
    "Анализируешь стиль автора постов в Telegram и описываешь его кратко и по делу."
)

def build_style_prompt(posts: List[str]) -> List[Dict[str, str]]:
    joined = "\n\n---\n\n".join(posts)
    user_msg = (
        "Вот несколько постов автора Telegram-канала.\n\n"
        f"{joined}\n\n"
        "1) Кратко опиши стиль автора (тон, длина, структура, любимые приёмы) в 4–6 предложениях.\n"
        "2) Перечисли 10–20 характерных слов/фраз автора.\n"
        "3) Перечисли 10–20 слов/фраз, которых лучше избегать (штампы и 'нейрословечки').\n"
        "Ответ верни в строго таком JSON-формате без комментариев:\n"
        "{\n"
        '  \"style_description\": \"...\",\n'
        '  \"preferred_phrases\": [\"...\"],\n'
        '  \"stop_phrases\": [\"...\"]\n'
        "}"
    )
    return [
        {"role": "system", "content": SYSTEM_STYLE_ANALYZER},
        {"role": "user", "content": user_msg},
    ]

def extract_style(posts: List[str]) -> Dict:
    messages = build_style_prompt(posts)
    raw = chat_completion(messages, max_tokens=650)

    # Простая попытка распарсить JSON, с fallback'ом
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # На первых тестах просто выведем текст и упадём
        print("Не удалось распарсить JSON от модели:\n", raw)
        raise
