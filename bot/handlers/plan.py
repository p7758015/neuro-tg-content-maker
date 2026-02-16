from datetime import datetime

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards.flow import after_plan_accept_keyboard
from bot.keyboards.main_menu import mainmenu_keyboard
from bot.services.api_client import (
    get_user_api,
    generate_plan,
    confirm_plan_api,
    get_current_plan_api,
    update_plan_times_api,
)

router = Router()


class PlanStates(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_first_time = State()
    waiting_for_goal = State()
    waiting_for_posts_per_day = State()
    waiting_for_plan_decision = State()


class PlanEditStates(StatesGroup):
    waiting_for_item_choice = State()
    waiting_for_new_time = State()


def posts_per_day_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 пост в день", callback_data="ppd_1"),
                InlineKeyboardButton(text="2 поста в день", callback_data="ppd_2"),
                InlineKeyboardButton(text="3 поста в день", callback_data="ppd_3"),
            ]
        ]
    )


def plan_decision_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить план",
                    callback_data="plan_accept",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔁 Сгенерировать план заново",
                    callback_data="plan_regenerate",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="plan_cancel",
                )
            ],
        ]
    )


def plan_items_edit_keyboard(plan: dict) -> InlineKeyboardMarkup:
    buttons = []
    for item in plan["items"]:
        text = f"{item['date']} {item['time']} — {item['post_type']}"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"edit_item_{item['item_id']}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_plan_text(plan: dict) -> str:
    lines = []
    lines.append(
        f"<b>Стиль:</b> <code>{plan['style_name']}</code>\n"
        f"<b>Цель недели:</b> {plan['goal']}\n"
        f"<b>Аудитория:</b> {plan['audience']}\n"
    )
    for item in plan["items"]:
        lines.append(
            f"{item['date']} {item['time']} — "
            f"<b>{item['post_type']}</b>: {item['topic']}"
        )
    return "\n".join(lines)


@router.message(Command("plan_week"))
@router.message(F.text == "📅 План на неделю")
async def cmd_plan_week(message: types.Message, state: FSMContext):
    userdata = await get_user_api(message.from_user.id)
    style_name = userdata.get("active_style_name")
    if not style_name:
        await message.answer(
            "У тебя пока не выбран стиль.\n"
            "Сначала подключи канал и сними стиль командой /connect_channel."
        )
        return

    # Проверим, есть ли уже текущий план
    try:
        current_plan = await get_current_plan_api(message.from_user.id)
    except Exception:
        current_plan = None

    if current_plan:
        await message.answer(
            "У тебя уже есть сохранённый контент-план.\n"
            "Если сгенерируешь новый, старый не будет использоваться для автопостинга.\n\n"
            "Если хочешь только поменять время постов — используй /plan_edit_time."
        )

    await state.update_data(style_name=style_name)

    await message.answer(
        "Давай сделаем новый план на неделю.\n\n"
        "Сначала пришли дату начала недели в формате YYYY-MM-DD.\n"
        "Например: 2026-02-11",
    )
    await state.set_state(PlanStates.waiting_for_start_date)


@router.message(PlanStates.waiting_for_start_date)
async def process_start_date(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()
    try:
        dt = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer(
            "Не получилось распознать дату.\n"
            "Пришли, пожалуйста, в формате YYYY-MM-DD, например: 2026-02-11."
        )
        return

    await state.update_data(start_date=dt.strftime("%Y-%m-%d"))

    await message.answer(
        "Теперь укажи время первого поста в формате HH:MM.\n"
        "Например: 10:00",
    )
    await state.set_state(PlanStates.waiting_for_first_time)


@router.message(PlanStates.waiting_for_first_time)
async def process_first_time(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()
    try:
        datetime.strptime(text, "%H:%M")
    except ValueError:
        await message.answer(
            "Не получилось распознать время.\n"
            "Пришли, пожалуйста, в формате HH:MM, например: 10:00."
        )
        return

    await state.update_data(first_time=text)

    data = await state.get_data()
    style_name = data["style_name"]

    await message.answer(
        "Опиши цель недели одной-двумя фразами.\n\n"
        "Например: «привлечь новых подписчиков на консультации по теме канала» "
        "или «подогреть аудиторию к запуску продукта по теме канала».\n"
        f"(Стиль: <b>{style_name}</b>)"
    )
    await state.set_state(PlanStates.waiting_for_goal)


@router.message(PlanStates.waiting_for_goal)
async def process_goal(message: types.Message, state: FSMContext):
    goal = (message.text or "").strip()
    if not goal:
        await message.answer("Цель недели не может быть пустой. Напиши её текстом.")
        return

    await state.update_data(goal=goal)
    await message.answer(
        "Сколько постов в день планируем публиковать?",
        reply_markup=posts_per_day_keyboard(),
    )
    await state.set_state(PlanStates.waiting_for_posts_per_day)


@router.callback_query(
    PlanStates.waiting_for_posts_per_day,
    F.data.startswith("ppd_"),
)
async def process_posts_per_day(callback: types.CallbackQuery, state: FSMContext):
    posts_per_day = int(callback.data.split("_")[1])
    await state.update_data(posts_per_day=posts_per_day)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Генерирую план на неделю, подожди немного…")

    await generate_and_show_plan(callback.message, state)
    await callback.answer()


async def generate_and_show_plan(message: types.Message, state: FSMContext):
    data = await state.get_data()
    style_name = data["style_name"]
    goal = data["goal"]
    posts_per_day = data["posts_per_day"]
    start_date = data["start_date"]
    first_time = data["first_time"]
    audience = "аудитория канала"

    try:
        plan = await generate_plan(
            style_name=style_name,
            start_date=start_date,
            goal=goal,
            audience=audience,
            posts_per_day=posts_per_day,
        )
    except Exception as e:
        await message.answer(f"Не удалось сгенерировать план: {e}")
        await state.clear()
        return

    # постобработка: учесть выбранное время первого поста для day_index == 0
    for item in plan["items"]:
        if item["day_index"] == 0:
            item["time"] = first_time

    text = format_plan_text(plan)

    await state.update_data(plan=plan)
    await message.answer(
        "Вот сгенерированный контент-план на неделю:\n\n" + text,
        reply_markup=plan_decision_keyboard(),
    )
    await state.set_state(PlanStates.waiting_for_plan_decision)


@router.callback_query(
    PlanStates.waiting_for_plan_decision,
    F.data == "plan_regenerate",
)
async def plan_regenerate_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Перегенерирую план…")
    await generate_and_show_plan(callback.message, state)
    await callback.answer()


@router.callback_query(
    PlanStates.waiting_for_plan_decision,
    F.data == "plan_cancel",
)
async def plan_cancel_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Ок, план на эту неделю не будем сохранять.")
    await state.clear()
    await callback.answer()


@router.callback_query(
    PlanStates.waiting_for_plan_decision,
    F.data == "plan_accept",
)
async def plan_accept_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    plan = data["plan"]
    style_name = data["style_name"]
    goal = data["goal"]
    start_date = data["start_date"]
    audience = "аудитория канала"

    plan_payload = {
        "user_telegram_id": callback.from_user.id,
        "style_name": style_name,
        "start_date": start_date,
        "goal": goal,
        "audience": audience,
        "items": plan["items"],
    }

    try:
        confirm_resp = await confirm_plan_api(plan_payload)
    except Exception as e:
        await callback.message.answer(
            f"Не удалось сохранить план в систему: {e}"
        )
        await state.clear()
        await callback.answer()
        return

    await callback.message.answer(
        "План <b>сохранён</b> ✅\n"
        "Теперь посты будут автоматически выходить по этому графику.\n\n"
        "Чтобы посмотреть ближайший пост в личке, используй /post.\n"
        "Чтобы тестово отправить пост в канал и пометить его отправленным — /autopost_demo.",
        reply_markup=mainmenu_keyboard,
    )

    # Дополнительная подсказка + кнопки
    await callback.message.answer(
        "Что дальше хочешь сделать?",
        reply_markup=after_plan_accept_keyboard(),
    )

    await state.clear()
    await callback.answer()


@router.message(Command("plan_status"))
@router.message(F.text == "✅ Статус плана")
async def cmd_plan_status(message: types.Message, state: FSMContext):
    try:
        plan = await get_current_plan_api(message.from_user.id)
    except Exception as e:
        await message.answer(f"Не удалось получить текущий план: {e}")
        return

    text = format_plan_text(plan)
    await message.answer(text)


@router.message(Command("plan_edit_time"))
@router.message(F.text == "⏰ Изменить время постов")
async def cmd_plan_edit_time(message: types.Message, state: FSMContext):
    try:
        plan = await get_current_plan_api(message.from_user.id)
    except Exception as e:
        await message.answer(
            "Не удалось получить текущий план.\n"
            f"Подробности: {e}"
        )
        await state.clear()
        return

    text = format_plan_text(plan)
    await message.answer(
        "Текущий план:\n\n" + text + "\n\nВыбери пост, для которого хочешь изменить время:",
        reply_markup=plan_items_edit_keyboard(plan),
    )
    await state.set_state(PlanEditStates.waiting_for_item_choice)
    await state.update_data(edit_plan_id=plan["plan_id"])


@router.callback_query(
    PlanEditStates.waiting_for_item_choice,
    F.data.startswith("edit_item_"),
)
async def plan_edit_choose_item(callback: types.CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split("_")[-1])
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.update_data(edit_item_id=item_id)

    await callback.message.answer(
        "Введи новое время для этого поста в формате HH:MM.\n"
        "Например: 16:30"
    )
    await state.set_state(PlanEditStates.waiting_for_new_time)
    await callback.answer()


@router.message(PlanEditStates.waiting_for_new_time)
async def plan_edit_set_time(message: types.Message, state: FSMContext):
    new_time = (message.text or "").strip()
    try:
        datetime.strptime(new_time, "%H:%M")
    except ValueError:
        await message.answer(
            "Не получилось распознать время.\n"
            "Пришли, пожалуйста, в формате HH:MM, например: 16:30."
        )
        return

    data = await state.get_data()
    plan_id = data.get("edit_plan_id")
    item_id = data.get("edit_item_id")

    if not plan_id or not item_id:
        await message.answer("Не удалось найти план или пост для обновления.")
        await state.clear()
        return

    try:
        await update_plan_times_api(
            plan_id=plan_id,
            items=[{"item_id": item_id, "time": new_time}],
        )
    except Exception as e:
        await message.answer(f"Не удалось обновить время поста: {e}")
        await state.clear()
        return

    await message.answer(
        "Готово ✅\n"
        "Время поста обновлено. Посты будут выходить по <b>новому графику</b>.\n\n"
        "Если хочешь поменять время других постов — ещё раз открой /plan_edit_time."
    )
    await state.clear()
