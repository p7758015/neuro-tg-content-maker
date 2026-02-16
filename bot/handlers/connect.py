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
from bot.services.state import set_last_connect_user
from bot.keyboards.flow import after_connect_keyboard, after_style_capture_keyboard
from bot.keyboards.main_menu import mainmenu_keyboard

router = Router()


class ConnectStates(StatesGroup):
    waiting_for_channel = State()
    waiting_for_style_name_decision = State()
    waiting_for_custom_style_name = State()


@router.message(Command("connect_channel"))
@router.message(F.text == "🔗 Подключить канал")
async def cmd_connect_channel(message: types.Message, state: FSMContext):
    await message.answer(
        "Отправь username канала или ссылку на него.\n\n"
        "Например: https://t.me/yourchannel или @yourchannel"
    )
    await state.set_state(ConnectStates.waiting_for_channel)


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
        await message.answer(
            "Не удалось распознать username канала.\n"
            "Пришли, пожалуйста, ссылку вида https://t.me/yourchannel или @yourchannel."
        )
        return

    await message.answer("Снимаю стиль с канала, подожди немного…")

    try:
        resp = await generate_from_channel(
            channel_username=username,
            topic="",
            goal="-",
            audience="-",
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при снятии стиля: {e}")
        await state.clear()
        return

    style_name = resp["style_name"]

    # Сохраняем канал за пользователем в бэкенде
    try:
        await set_user_channel_api(message.from_user.id, username)
    except Exception:
        # если тут ошибка, просто уведомим, но не падаем
        await message.answer(
            "Стиль снят, но не удалось сохранить канал в профиле. "
            "Попробуй позже ещё раз /connect_channel."
        )

    await state.update_data(suggested_style_name=style_name, channel_username=username)

    # Предлагаем имя стиля, связанное с тематикой канала
    await message.answer(
        f"Я снял стиль с канала @{username}.\n\n"
        f"Предлагаю назвать этот стиль так: <b>{style_name}</b>.\n\n"
        "Если тебя устраивает такое название — нажми кнопку ниже.\n"
        "Если хочешь другое, введи своё название (например, «инфобизнес», «фитнес», «крипта»).",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Оставить это название",
                        callback_data="style_name_ok",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Задать своё название",
                        callback_data="style_name_custom",
                    )
                ],
            ]
        ),
    )
    await state.set_state(ConnectStates.waiting_for_style_name_decision)


@router.callback_query(
    ConnectStates.waiting_for_style_name_decision,
    F.data == "style_name_ok",
)
async def style_name_ok_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    style_name = data.get("suggested_style_name")

    if style_name:
        try:
            await set_user_style_api(callback.from_user.id, style_name)
        except Exception:
            await callback.message.answer(
                "Не удалось сохранить стиль за пользователем, но стиль уже создан."
            )

    set_last_connect_user(callback.from_user.id)

    await callback.message.answer(
        f"Стиль <b>{style_name}</b> сохранён и привязан к тебе. ✅\n\n"
        "Что важно сделать, чтобы автопостинг работал:\n"
        "1️⃣ Добавь этого бота в администраторы канала с правом публиковать посты.\n"
        "2️⃣ В самом канале один раз отправь сообщение: /link_channel — бот запомнит этот канал.\n"
        "3️⃣ В личке с ботом создай и одобри контент-план через /plan_week.\n\n"
        "После этого посты будут автоматически выходить в канал по расписанию.\n\n"
        "Для теста можно использовать:\n"
        "• /post — посмотреть ближайший пост по плану в личке;\n"
        "• /autopost_demo — отправить ближайший пост в канал и отметить его как отправленный.",
        reply_markup=mainmenu_keyboard,
    )

    await callback.message.answer(
        "Что дальше хочешь сделать?",
        reply_markup=after_style_capture_keyboard(),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(
    ConnectStates.waiting_for_style_name_decision,
    F.data == "style_name_custom",
)
async def style_name_custom_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Введи своё название стиля.\n"
        "Например: «инфобизнес», «фитнес», «крипта», «личный блог»."
    )
    await state.set_state(ConnectStates.waiting_for_custom_style_name)
    await callback.answer()


@router.message(ConnectStates.waiting_for_custom_style_name)
async def process_custom_style_name(message: types.Message, state: FSMContext):
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("Название не может быть пустым. Попробуй ещё раз.")
        return

    data = await state.get_data()
    suggested_name = data.get("suggested_style_name")

    await message.answer("Переименовываю стиль, подожди секунду…")

    try:
        if suggested_name and suggested_name != new_name:
            await rename_style_api(suggested_name, new_name)
        await set_user_style_api(message.from_user.id, new_name)
    except Exception as e:
        await message.answer(f"Не удалось переименовать или сохранить стиль: {e}")
        await state.clear()
        return

    set_last_connect_user(message.from_user.id)

    await message.answer(
        f"Стиль <b>{new_name}</b> сохранён и привязан к тебе. ✅\n\n"
        "Что важно сделать, чтобы автопостинг работал:\n"
        "1️⃣ Добавь этого бота в администраторы канала с правом публиковать посты.\n"
        "2️⃣ В самом канале один раз отправь сообщение: /link_channel — бот запомнит этот канал.\n"
        "3️⃣ В личке с ботом создай и одобри контент-план через /plan_week.\n\n"
        "После этого посты будут автоматически выходить в канал по расписанию.\n\n"
        "Для теста можно использовать:\n"
        "• /post — посмотреть ближайший пост по плану в личке;\n"
        "• /autopost_demo — отправить ближайший пост в канал и отметить его как отправленный.",
        reply_markup=mainmenu_keyboard,
    )

    await message.answer(
        "Что дальше хочешь сделать?",
        reply_markup=after_style_capture_keyboard(),
    )
    await state.clear()
