from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

mainmenu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔗 Подключить канал"),
            KeyboardButton(text="✏️ Пост по плану"),
        ],
        [
            KeyboardButton(text="📅 План на неделю"),
            KeyboardButton(text="✅ Статус плана"),
        ],
        [
            KeyboardButton(text="⏰ Изменить время постов"),
            KeyboardButton(text="🚀 Тест автопостинга"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери действие…",
)
