from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.services.api_client import (
    get_user_api,
    autopost_preview_api,
    autopost_next_api,
)

router = Router()


class PostStates(StatesGroup):
    # Если захочешь вернуть старый сценарий с брифом — оставляем задел
    waiting_for_brief = State()


@router.message(Command("post"))
@router.message(F.text == "✏️ Пост по плану")
async def cmd_post(message: types.Message, state: FSMContext):
    """Показать следующий пост по плану в личку, не помечая его отправленным."""
    # проверим, что у пользователя вообще есть стиль/план
    userdata = await get_user_api(message.from_user.id)
    style_name = userdata.get("active_style_name")
    if not style_name:
        await message.answer(
            "У тебя пока не выбран стиль.\n"
            "Сначала подключи канал и сними стиль командой /connect_channel."
        )
        return

    try:
        preview = await autopost_preview_api(message.from_user.id)
    except Exception as e:
        await message.answer(
            "Не удалось получить следующий пост по плану.\n"
            f"Подробности: {e}"
        )
        return

    post_text = preview["post_text"]

    await message.answer(
        "Вот ближайший пост по текущему контент-плану:\n\n"
        f"{post_text}\n\n"
        "Этот пост <b>пока не считается опубликованным</b>.\n"
        "Чтобы отправить его в канал и отметить как отправленный, используй /autopost_demo."
    )


@router.message(Command("autopost_demo"))
@router.message(F.text == "🚀 Тест автопостинга")
async def cmd_autopost_demo(message: types.Message, state: FSMContext):
    """Отправить ближайший пост по плану в канал и пометить его как отправленный."""
    try:
        resp = await autopost_next_api(message.from_user.id)
    except Exception as e:
        await message.answer(
            "Не удалось выполнить тестовый автопост.\n"
            f"Подробности: {e}"
        )
        return

    sent_to = resp.get("sent_to")

    await message.answer(
        "Я отправил ближайший пост по плану в канал и отметил его как опубликованный ✅\n\n"
        "Теперь, если ты снова вызовешь /post, в личку придёт <b>следующий</b> пост по графику.\n\n"
        f"ID чата, куда был отправлен пост: <code>{sent_to}</code>"
    )
