# app/services/plan_generator.py
from datetime import datetime, timedelta
from typing import Dict, List

from app.core.openai_client import chat_completion
from app.schemas.plan import PlanGenerateRequest, PlanItem


SYSTEM_PLAN_WRITER = (
    "Ты контент-маркетолог и редактор Telegram-каналов. "
    "Составляешь недельный контент-план с темами постов по дням."
)

def _build_plan_prompt(style: Dict, req: PlanGenerateRequest) -> list[dict]:
    style_desc = style.get("style_description", "")
    # можно использовать и preferred_phrases, но для экономии токенов пока берём только описание стиля

    user_msg = (
        f"Стиль автора:\n{style_desc}\n\n"
        f"Дата начала недели: {req.start_date}\n"
        f"Цель недели: {req.goal}\n"
        f"Целевая аудитория: {req.audience}\n"
        f"Постов в день: {req.posts_per_day}\n\n"
        "Составь контент-план на 7 дней для Telegram-канала.\n"
        "Для каждого поста укажи:\n"
        "- номер дня относительно начала недели (0..6),\n"
        "- примерное время публикации (формат HH:MM),\n"
        "- тип поста (прогрев, польза, продажа, история, кейс и т.п.),\n"
        "- тему поста (кратко),\n"
        "- при необходимости короткие пометки.\n\n"
        "Ответ верни строго в JSON-массиве без комментариев, вида:\n"
        "[\n"
        "  {\n"
        '    \"day_index\": 0,\n'
        '    \"time\": \"11:00\",\n'
        '    \"post_type\": \"прогрев\",\n'
        '    \"topic\": \"...\",\n'
        '    \"notes\": \"...\"\n'
        "  }\n"
        "]"
    )

    return [
        {"role": "system", "content": SYSTEM_PLAN_WRITER},
        {"role": "user", "content": user_msg},
    ]

def generate_week_plan(style: Dict, req: PlanGenerateRequest) -> List[PlanItem]:
    messages = _build_plan_prompt(style, req)
    raw = chat_completion(messages, max_tokens=900)

    import json
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("Не удалось распарсить JSON плана:\n", raw)
        raise

    # добавляем поле date из start_date + day_index
    start_dt = datetime.strptime(req.start_date, "%Y-%m-%d").date()
    items: List[PlanItem] = []
    for item in data:
        day_idx = int(item["day_index"])
        date_str = (start_dt + timedelta(days=day_idx)).strftime("%Y-%m-%d")
        items.append(
            PlanItem(
                day_index=day_idx,
                date=date_str,
                time=item["time"],
                post_type=item["post_type"],
                topic=item["topic"],
                notes=item.get("notes", ""),
            )
        )
    return items
