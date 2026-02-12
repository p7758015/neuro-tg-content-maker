# bot/handlers/channel.py
from aiogram import Router, types
from aiogram.filters import Command

from bot.services.api_client import set_channel_chat_id_api_for_username

router = Router()


@router.channel_post(Command("link_channel"))
async def link_channel_in_channel(message: types.Message):
    """
    Срабатывает, когда в канале, где бот — админ, отправляют /link_channel.
    Привязывает этот канал к пользователю, который ранее указал channel_username через /connect_channel.
    """
    chat = message.chat

    if chat.type != "channel":
        return

    channel_username = chat.username  # без @
    channel_chat_id = chat.id

    if not channel_username:
        await message.answer(
            "У этого канала нет username. Сейчас поддерживаются только каналы с username.\n"
            "Задай каналу username, добавь меня админом и снова отправь /link_channel."
        )
        return

    try:
        await set_channel_chat_id_api_for_username(
            channel_username=channel_username,
            channel_chat_id=channel_chat_id,
        )
    except Exception as e:
        await message.answer(f"Не удалось привязать канал: {e}")
        return

    await message.answer(
        "Канал привязан! Теперь посты по плану будут отправляться сюда.\n\n"
        "Можешь воспользоваться /autopost_demo, чтобы проверить всё на практике."
    )

