from aiogram import Router, types
from aiogram.filters import CommandStart, Command

from bot.keyboards.main_menu import mainmenu_keyboard

router = Router()

WELCOME_TEXT = (
    "Привет! Я нейро-контентмейкер для Telegram.\n\n"
    "Я умею:\n"
    "• снимать стиль с любого канала по ссылке,\n"
    "• генерировать посты в этом стиле,\n"
    "• делать контент-план на неделю и автопостить его в канал.\n\n"
    "Как начать:\n"
    "1️⃣ Подключи канал и сними стиль — команда /connect_channel.\n"
    "2️⃣ Сгенерируй план постов на неделю и одобри его, после одобрения посты будут автоматически выкладываться в твой канал — команда /plan_week.\n"
    "3️⃣ При необходимости поправь время постов — команда /plan_edit_time.\n"
    "4️⃣ Протестируй автопостинг — команда /autopost_demo.\n\n"
    "В любой момент можешь посмотреть текущий план через /plan_status."
)


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(WELCOME_TEXT, reply_markup=mainmenu_keyboard)


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Доступные команды:\n"
        "/connect_channel — подключить канал и снять стиль\n"
        "/post — показать следующий пост по плану в личке\n"
        "/plan_week — сделать план постов на неделю\n"
        "/plan_status — показать текущий план\n"
        "/plan_edit_time — изменить время постов\n"
        "/autopost_demo — тестово отправить пост в канал по плану"
    )
