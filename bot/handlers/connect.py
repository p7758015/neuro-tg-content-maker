# bot/handlers/connect.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.api_client import (
    generate_from_channel,
    rename_style_api,
    set_user_style_api,
    set_user_channel_api,
)
from bot.services.state import set_last_connect_user  # ← добавили
from bot.keyboards.flow import (
    after_connect_keyboard,
    after_style_capture_keyboard,
)
from bot.keyboards.main_menu import main_menu_keyboard

router = Router()


class ConnectStates(StatesGroup):
    waiting_for_channel = State()
    waiting_for_style_name_decision = State()
    waiting_for_custom_style_name = State()


@router.message(Command("connect_channel"))
async def cmd_connect_channel(message: types.Message, state: FSMContext):
    await message.answer(
        "Пришли ссылку или @username канала, с которого нужно снять стиль.\n\n"
        "Например:\n"
        "https://t.me/your_channel\n"
        "или @your_channel"
    )
    await state.set_state(ConnectStates.waiting_for_channel)
    # здесь пока НЕ показываем «канал подключён», он ещё не обработан


@router.message(ConnectStates.waiting_for_channel)
async def process_channel_username(message: types.Message, state: FSMContext):
    username_raw = (message.text or "").strip()
    username = (
        username_raw.replace("https://t.me/", "")
        .replace("http://t.me/", "")
        .replace("@", "")
        .strip()
    )
    if not username:
        await message.answer("Не смог прочитать username. Пришли, пожалуйста, ещё раз.")
        return

    await message.answer("Секунду, снимаю стиль с канала…")

    try:
        # временный бриф, чтобы получить стиль + пример поста
        resp = await generate_from_channel(
            channel_username=username,
            topic="Тестовый пост в стиле автора",
            goal="проверить стиль для нейро-контентмейкера",
            audience="подписчики этого канала",
        )
    except Exception as e:
        await message.answer(f"Не получилось снять стиль: {e}")
        await state.clear()
        return

    style_name = resp["style_name"]

    # Сохраняем username канала за пользователем (без chat_id пока)
    try:
        await set_user_channel_api(message.from_user.id, username)
    except Exception:
        # не ломаем сценарий, если не удалось сохранить канал
        pass

    await state.update_data(
        channel_username=username,
        suggested_style_name=style_name,
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Оставить имя: {style_name}",
                    callback_data="style_name_keep",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Ввести своё имя",
                    callback_data="style_name_custom",
                )
            ],
        ]
    )

    await message.answer(
        f"Снял стиль с канала @{username}.\n\n"
        f"Предлагаю название стиля: <b>{style_name}</b>.\n"
        "Оставить так или ввести своё?",
        reply_markup=kb,
    )
    await state.set_state(ConnectStates.waiting_for_style_name_decision)


@router.callback_query(
    ConnectStates.waiting_for_style_name_decision,
    F.data == "style_name_keep",
)
async def style_name_keep(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    style_name = data["suggested_style_name"]

    try:
        await set_user_style_api(callback.from_user.id, style_name)
    except Exception as e:
        await callback.message.answer(
            f"Не удалось сохранить стиль для пользователя: {e}"
        )
        await state.clear()
        await callback.answer()
        return

    # фиксируем, что этот пользователь последний прошёл connect_channel
    set_last_connect_user(callback.from_user.id)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"Ок, стиль закреплён как <b>{style_name}</b>.\n\n"
        "Дальше сделай два шага, чтобы я мог постить в канал:\n"
        "1️⃣ Добавь этого бота администратором в свой канал.\n"
        "2️⃣ В самом канале отправь команду /link_channel.\n\n"
        "После этого можно генерировать посты (/post) и планы (/plan_week).",
        reply_markup=main_menu_keyboard(),
    )
    await callback.message.answer(
        "Что делаем дальше?",
        reply_markup=after_style_capture_keyboard(),
    )

    await state.clear()
    await callback.answer()


@router.callback_query(
    ConnectStates.waiting_for_style_name_decision,
    F.data == "style_name_custom",
)
async def style_name_custom(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Введи, пожалуйста, своё название для этого стиля.\n"
        "Например: edler_autoML или cherkashov_main."
    )
    await state.set_state(ConnectStates.waiting_for_custom_style_name)
    await callback.answer()


@router.message(ConnectStates.waiting_for_custom_style_name)
async def process_custom_style_name(message: types.Message, state: FSMContext):
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("Имя стиля не должно быть пустым. Попробуй ещё раз.")
        return

    data = await state.get_data()
    suggested_name = data["suggested_style_name"]

    await message.answer("Переименовываю стиль на стороне сервиса…")

    try:
        await rename_style_api(suggested_name, new_name)
        await set_user_style_api(message.from_user.id, new_name)
    except Exception as e:
        await message.answer(
            "Не удалось полностью оформить стиль.\n"
            f"Подробнее: {e}\n\n"
            f"Попробуй ещё раз или используй имя: <b>{suggested_name}</b>."
        )
        await state.clear()
        return

    # фиксируем, что этот пользователь последний прошёл connect_channel
    set_last_connect_user(message.from_user.id)

    await message.answer(
        f"Готово! Стиль переименован и теперь называется <b>{new_name}</b>.\n\n"
        "Дальше сделай два шага, чтобы я мог постить в канал:\n"
        "1️⃣ Добавь этого бота администратором в свой канал.\n"
        "2️⃣ В самом канале отправь команду /link_channel.\n\n"
        "После этого можешь генерировать посты (/post) и планы (/plan_week).",
        reply_markup=main_menu_keyboard(),
    )
    await message.answer(
        "Что делаем дальше?",
        reply_markup=after_style_capture_keyboard(),
    )

    await state.clear()
