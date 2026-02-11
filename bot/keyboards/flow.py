from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def after_connect_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎨 Снять стиль с канала",
                    callback_data="next_style_capture",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📝 Пост по стилу",
                    callback_data="next_post",
                ),
            ],
        ]
    )

def after_style_capture_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Сгенерировать пост",
                    callback_data="next_post",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📅 План на неделю",
                    callback_data="next_plan_week",
                ),
            ],
        ]
    )

def after_plan_accept_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👀 Посмотреть план",
                    callback_data="next_plan_status",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🚀 Отправить пост /autopost_demo",
                    callback_data="next_autopost_demo",
                ),
            ],
        ]
    )
