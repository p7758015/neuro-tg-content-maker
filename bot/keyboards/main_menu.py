from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="/connect_channel"),
                KeyboardButton(text="/post"),
            ],
            [
                KeyboardButton(text="/plan_week"),
                KeyboardButton(text="/plan_status"),
            ],
            [
                KeyboardButton(text="/plan_edit_time"),
                KeyboardButton(text="/autopost_demo"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери команду из меню",
    )
