# bot/handlers/start.py
from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from bot.keyboards.main_menu import main_menu_keyboard

router = Router()

WELCOME_TEXT = (
    "Привет! Я нейро-контентмейкер для Telegram.\n\n"
    "Я умею:\n"
    "• снимать стиль с твоего канала по ссылке,\n"
    "• генерировать посты в этом стиле,\n"
    "• делать контент-план на неделю и автопостить его в канал.\n\n"
    "Как начать:\n"
    "1️⃣ Подключи канал и сними стиль — команда /connect_channel.\n"
    "2️⃣ Сгенерируй план постов на неделю — команда /plan_week.\n"
    "3️⃣ При необходимости поправь время постов — команда /plan_edit_time.\n"
    "4️⃣ Протестируй автопостинг — команда /autopost_demo.\n\n"
    "В любой момент можешь посмотреть текущий план через /plan_status."
)


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Основные команды:\n"
        "/connect_channel — подключить канал и снять стиль\n"
        "/styles — посмотреть доступные стили\n"
        "/post — сгенерировать один пост\n"
        "/plan_week — предложить план на неделю\n"
        "/plan_status — показать сохранённый план\n"
        "/plan_edit_time — изменить время постов в плане\n"
        "/autopost_demo — показать ближайший пост и отправить его по плану\n"
    )
