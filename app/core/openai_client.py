# app/core/openai_client.py
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)

def chat_completion(messages, max_tokens: int | None = None, temperature: float | None = None, model: str | None = None) -> str:
    response = client.chat.completions.create(
        model=model or settings.model,
        messages=messages,
        max_tokens=max_tokens or settings.max_tokens,
        temperature=temperature or settings.temperature,
    )
    return response.choices[0].message.content.strip()
