# bot/handlers/start.py
from aiogram import Router, types
from aiogram.filters import CommandStart, Command

router = Router()

WELCOME_TEXT = (
    "Привет! Я нейро-контентмейкер для Telegram.\n\n"
    "Я умею:\n"
    "• снимать стиль с твоего канала по ссылке,\n"
    "• генерировать посты в этом стиле,\n"
    "• делать контент-план на неделю.\n\n"
    "Начать можно с команды /connect_channel."
)

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(WELCOME_TEXT)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Основные команды:\n"
        "/connect_channel — подключить канал и снять стиль\n"
        "/styles — посмотреть доступные стили\n"
        "/post — сгенерировать один пост\n"
        "/plan_week — предложить план на неделю\n"
    )
