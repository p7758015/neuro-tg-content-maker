# bot/handlers/post.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.api_client import (
    generate_post_api,
    get_user_api,
    autopost_next_api,
    autopost_preview_api,
)

router = Router()


class PostStates(StatesGroup):
    waiting_for_brief = State()


@router.message(Command("post"))
async def cmd_post(message: types.Message, state: FSMContext):
    user_data = await get_user_api(message.from_user.id)
    style_name = user_data.get("active_style_name")

    if not style_name:
        await message.answer(
            "Сначала нужно подключить канал и выбрать стиль через /connect_channel."
        )
        return

    await state.update_data(style_name=style_name)

    await message.answer(
        "Пришли краткий бриф для поста в одном сообщении.\n\n"
        "Формат, например:\n"
        "Тема: запуск мини-курса по AutoML\n"
        "Цель: прогрев перед регистрацией\n"
        "Аудитория: подписчики канала, новичок в AI\n\n"
        "Можно писать в свободной форме — я постараюсь вытащить суть."
    )
    await state.set_state(PostStates.waiting_for_brief)


@router.message(PostStates.waiting_for_brief)
async def process_post_brief(message: types.Message, state: FSMContext):
    data = await state.get_data()
    style_name = data.get("style_name")

    if not style_name:
        # на всякий случай ещё раз спросим БД
        user_data = await get_user_api(message.from_user.id)
        style_name = user_data.get("active_style_name")

    if not style_name:
        await message.answer("Стиль не найден. Попробуй снова через /connect_channel.")
        await state.clear()
        return

    text = message.text or ""
    topic = text.strip() or "Пост по теме недели"
    goal = "донести ценность и вовлечь аудиторию"
    audience = "подписчики канала"

    await message.answer("Генерирую пост…")

    try:
        resp = await generate_post_api(
            style_name=style_name,
            topic=topic,
            goal=goal,
            audience=audience,
            max_chars=1200,
        )
    except Exception as e:
        await message.answer(f"Не получилось сгенерировать пост: {e}")
        await state.clear()
        return

    post_text = resp["post"]

    await message.answer(
        "<b>Черновик поста:</b>\n\n" + post_text
    )

    await state.clear()


@router.message(Command("autopost_demo"))
async def cmd_autopost_demo(message: types.Message, state: FSMContext):
    # 1. Проверяем, привязан ли канал
    try:
        user_data = await get_user_api(message.from_user.id)
    except Exception as e:
        await message.answer(f"Не удалось получить данные пользователя: {e}")
        return

    channel_chat_id = user_data.get("channel_chat_id")
    channel_username = user_data.get("channel_username")

    if not channel_chat_id:
        # Канал не привязан — даём понятную инструкцию и выходим
        text = (
            "Канал для автопостинга пока не подключён.\n\n"
            "Чтобы я мог отправлять посты по плану в канал, сделай три шага:\n"
            "1️⃣ В личке со мной выполни /connect_channel и укажи ссылку или @username канала.\n"
            "2️⃣ Добавь этого бота администратором в этот канал.\n"
            "3️⃣ В самом канале отправь команду /link_channel.\n\n"
        )
        if channel_username:
            text += (
                f"Сейчас у тебя сохранён канал @{channel_username}. "
                "Если всё верно — просто добавь меня админом и отправь /link_channel в этом канале.\n\n"
                "После этого вернись к команде /autopost_demo — я покажу ближайший пост по плану "
                "и уже смогу отправить его в канал."
            )
        else:
            text += (
                "После этого вернись к /autopost_demo — я покажу ближайший пост по плану "
                "и буду отправлять его в подключённый канал."
            )

        await message.answer(text)
        return

    # 2. Канал привязан — показываем превью ближайшего поста
    try:
        preview = await autopost_preview_api(message.from_user.id)
    except Exception as e:
        await message.answer(f"Не удалось получить пост по плану: {e}")
        return

    post_text = preview["post_text"]
    plan_id = preview["plan_id"]
    item_id = preview["item_id"]

    await state.update_data(
        autopost_preview_plan_id=plan_id,
        autopost_preview_item_id=item_id,
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Отправить сейчас по плану",
                    callback_data="autopost_send_now",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Не отправлять",
                    callback_data="autopost_cancel",
                )
            ],
        ]
    )

    await message.answer(
        "<b>Ближайший пост по плану (превью):</b>\n\n" + post_text,
        reply_markup=kb,
    )


@router.callback_query(F.data == "autopost_send_now")
async def autopost_send_now(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Отправляю пост по плану…")

    try:
        resp = await autopost_next_api(callback.from_user.id)
    except Exception as e:
        await callback.message.answer(f"Не удалось отправить пост: {e}")
        await callback.answer()
        return

    await callback.message.answer(
        "Пост отправлен.\n"
        f"plan_id: <code>{resp.get('plan_id')}</code>, "
        f"item_id: <code>{resp.get('item_id')}</code>."
    )
    await callback.answer()


@router.callback_query(F.data == "autopost_cancel")
async def autopost_cancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Ок, этот пост не отправляю.")
    await state.clear()
    await callback.answer()
