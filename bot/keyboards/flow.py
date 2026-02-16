from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def after_connect_keyboard() -> InlineKeyboardMarkup:
    # после подключения канала и снятия стиля
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Сделать план на неделю",
                    callback_data="next_planweek",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Посмотреть пост по плану",
                    callback_data="next_post",
                )
            ],
        ]
    )


def after_style_capture_keyboard() -> InlineKeyboardMarkup:
    # после того как предложено название стиля / переименовано
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Посмотреть пост по плану",
                    callback_data="next_post",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Сделать план на неделю",
                    callback_data="next_planweek",
                )
            ],
        ]
    )


def after_plan_accept_keyboard() -> InlineKeyboardMarkup:
    # после одобрения плана
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Посмотреть ближайший пост",
                    callback_data="next_post",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Изменить время постов",
                    callback_data="next_plan_edit_time",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Посмотреть статус плана",
                    callback_data="next_planstatus",
                )
            ],
        ]
    )
