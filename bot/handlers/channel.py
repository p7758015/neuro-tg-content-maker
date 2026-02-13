# bot/handlers/channel.py
from aiogram import Router, types
from aiogram.filters import Command

from bot.services.api_client import link_channel_api
from bot.services.state import get_last_connect_user

router = Router()


@router.channel_post(Command("link_channel"))
async def link_channel_in_channel(message: types.Message):
    chat = message.chat

    if chat.type != "channel":
        return

    channel_chat_id = chat.id

    # пытаемся понять, кто последний проходил /connect_channel
    owner_telegram_id = get_last_connect_user()
    if not owner_telegram_id:
        await message.answer(
            "Не получилось понять, для какого пользователя привязывать канал.\n\n"
            "Сначала в личке со мной выполни /connect_channel, оформи стиль до конца,\n"
            "а уже потом отправь /link_channel в канале."
        )
        return

    try:
        await link_channel_api(
            telegram_id=owner_telegram_id,
            channel_chat_id=channel_chat_id,
        )
    except Exception as e:
        await message.answer(f"Не удалось привязать канал: {e}")
        return

    await message.answer(
        "Канал привязан! Теперь посты по плану будут отправляться сюда.\n\n"
        "Можешь воспользоваться /autopost_demo, чтобы проверить всё на практике."
    )
