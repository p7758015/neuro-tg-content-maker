# bot/handlers/post.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.services.state import get_user_style
from bot.services.api_client import generate_post_api, get_user_api, autopost_next_api

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
async def cmd_autopost_demo(message: types.Message):
    try:
        resp = await autopost_next_api(message.from_user.id)
    except Exception as e:
        await message.answer(f"Не удалось отправить пост по плану: {e}")
        return

    await message.answer(
        "Отправил пост по текущему плану.\n"
        f"plan_id: <code>{resp.get('plan_id')}</code>, "
        f"item_id: <code>{resp.get('item_id')}</code>."
    )