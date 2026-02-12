# bot/handlers/plan.py
from datetime import datetime

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards.flow import after_plan_accept_keyboard
from bot.keyboards.main_menu import main_menu_keyboard
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


def _posts_per_day_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 пост в день", callback_data="ppd_1"),
                InlineKeyboardButton(text="2 поста в день", callback_data="ppd_2"),
            ],
            [
                InlineKeyboardButton(text="3 поста в день", callback_data="ppd_3"),
            ],
        ]
    )


def _plan_decision_keyboard() -> InlineKeyboardMarkup:
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
                    text="🔁 Сгенерировать заново",
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


def _format_plan_text(plan: dict) -> str:
    lines = []
    lines.append(
        f"<b>План на неделю</b> (стиль: <code>{plan['style_name']}</code>)\n"
        f"Цель: {plan['goal']}\n"
        f"Аудитория: {plan['audience']}\n"
    )
    for item in plan["items"]:
        lines.append(
            f"• {item['date']} {item['time']} — <b>{item['post_type']}</b>: {item['topic']}"
        )
    return "\n".join(lines)


@router.message(Command("plan_week"))
async def cmd_plan_week(message: types.Message, state: FSMContext):
    user_data = await get_user_api(message.from_user.id)
    style_name = user_data.get("active_style_name")

    if not style_name:
        await message.answer(
            "Сначала нужно подключить канал и выбрать стиль через /connect_channel."
        )
        return

    # проверяем текущий план
    current_plan = await get_current_plan_api(message.from_user.id)
    if current_plan:
        await message.answer(
            "У тебя уже есть актуальный план на неделю.\n\n"
            "Если хочешь, можешь всё равно сгенерировать новый вариант — "
            "он станет текущим, а старый останется в истории.\n\n"
            "Продолжаем создание нового плана: сначала выберем дату старта."
        )

    await state.update_data(style_name=style_name)

    await message.answer(
        "С какого дня начинаем план? Напиши дату в формате ГГГГ-ММ-ДД.\n"
        "Например: 2026-02-11"
    )
    await state.set_state(PlanStates.waiting_for_start_date)


@router.message(PlanStates.waiting_for_start_date)
async def process_start_date(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()
    try:
        dt = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer(
            "Не понял дату. Напиши в формате ГГГГ-ММ-ДД, например 2026-02-11."
        )
        return

    await state.update_data(start_date=dt.strftime("%Y-%m-%d"))

    await message.answer(
        "Во сколько примерно делать первый пост? Напиши время в формате ЧЧ:ММ.\n"
        "Например: 10:00"
    )
    await state.set_state(PlanStates.waiting_for_first_time)


@router.message(PlanStates.waiting_for_first_time)
async def process_first_time(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()
    try:
        datetime.strptime(text, "%H:%M")
    except ValueError:
        await message.answer(
            "Не понял время. Напиши в формате ЧЧ:ММ, например 10:00."
        )
        return

    await state.update_data(first_time=text)

    await message.answer(
        "Опиши, пожалуйста, <b>цель недели</b>.\n\n"
        "Например: прогреть аудиторию перед запуском мини-курса по AutoML."
    )
    await state.set_state(PlanStates.waiting_for_goal)


@router.message(PlanStates.waiting_for_goal)
async def process_goal(message: types.Message, state: FSMContext):
    goal = (message.text or "").strip()
    if not goal:
        await message.answer("Цель не должна быть пустой. Попробуй ещё раз.")
        return

    await state.update_data(goal=goal)

    await message.answer(
        "Сколько постов в день планируем?",
        reply_markup=_posts_per_day_keyboard(),
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
    await callback.message.answer("Генерирую черновой план на неделю…")
    await _generate_and_show_plan(callback.message, state)
    await callback.answer()


async def _generate_and_show_plan(message: types.Message, state: FSMContext):
    data = await state.get_data()
    style_name = data["style_name"]
    goal = data["goal"]
    posts_per_day = data["posts_per_day"]
    start_date = data["start_date"]
    first_time = data["first_time"]

    audience = "подписчики канала"

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

    # прокинем first_time в план, чтобы дальше scheduler знал, когда первый пост
    plan["start_date"] = start_date
    await state.update_data(current_plan=plan)

    # Форматируем и отправляем план пользователю
    text = _format_plan_text(plan)
    await message.answer(
        text + "\n\nУстроит такой план?",
        reply_markup=_plan_decision_keyboard(),
    )

    # Переводим FSM в состояние ожидания решения по плану
    await state.set_state(PlanStates.waiting_for_plan_decision)


@router.callback_query(
    PlanStates.waiting_for_plan_decision,
    F.data == "plan_regenerate",
)
async def plan_regenerate(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Ок, генерирую другой вариант плана…")
    await _generate_and_show_plan(callback.message, state)
    await callback.answer()


@router.callback_query(
    PlanStates.waiting_for_plan_decision,
    F.data == "plan_cancel",
)
async def plan_cancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "План на эту неделю отменён, ничего не сохранил."
    )
    await state.clear()
    await callback.answer()


@router.callback_query(
    PlanStates.waiting_for_plan_decision,
    F.data == "plan_accept",
)
async def plan_accept(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    plan = data.get("current_plan")

    if not plan:
        await callback.message.answer(
            "Не нашёл текущий план. Попробуй ещё раз через /plan_week."
        )
        await state.clear()
        await callback.answer()
        return

    # добавляем user_telegram_id к payload
    plan_payload = {
        "user_telegram_id": callback.from_user.id,
        "style_name": plan["style_name"],
        "start_date": plan["start_date"],
        "goal": plan["goal"],
        "audience": plan["audience"],
        "items": plan["items"],
    }

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Сохраняю план в сервисе…")

    try:
        resp = await confirm_plan_api(plan_payload)
    except Exception as e:
        await callback.message.answer(f"Не удалось сохранить план: {e}")
        await state.clear()
        await callback.answer()
        return

    total_posts = resp["items_count"]
    posts_per_day = total_posts // 7 if total_posts >= 7 else total_posts
    start_date = plan["start_date"]

    await callback.message.answer(
        "Готово! План сохранён.\n\n"
        f"id: <code>{resp['plan_id']}</code>\n"
        f"Дата старта: <code>{start_date}</code>\n"
        f"Кол-во постов: <code>{total_posts}</code>\n"
        f"Примерно постов в день: <code>{posts_per_day}</code>\n\n"
        "Теперь можно посмотреть план через /plan_status "
        "и использовать /autopost_demo для отправки постов.",
        reply_markup=main_menu_keyboard(),
    )

    await callback.message.answer(
        "Следующие шаги:",
        reply_markup=after_plan_accept_keyboard(),
    )

    await state.clear()
    await callback.answer()


@router.message(Command("plan_status"))
async def cmd_plan_status(message: types.Message):
    try:
        plan = await get_current_plan_api(message.from_user.id)
    except Exception as e:
        await message.answer(f"Не удалось получить план: {e}")
        return

    if not plan:
        await message.answer(
            "Для тебя пока нет сохранённых планов. Попробуй /plan_week."
        )
        return

    text = _format_plan_text(plan)
    await message.answer(text)

def _plan_items_edit_keyboard(plan: dict) -> InlineKeyboardMarkup:
    rows = []
    for idx, item in enumerate(plan["items"], start=1):
        btn = InlineKeyboardButton(
            text=f"✏ {idx}) {item['date']} {item['time']}",
            callback_data=f"edit_time_{item['item_id']}",
        )
        rows.append([btn])
    # Доп. кнопка "Готово" для выхода
    rows.append(
        [
            InlineKeyboardButton(
                text="✅ Готово",
                callback_data="edit_time_done",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.message(Command("plan_edit_time"))
async def cmd_plan_edit_time(message: types.Message, state: FSMContext):
    try:
        plan = await get_current_plan_api(message.from_user.id)
    except Exception as e:
        await message.answer(f"Не удалось получить план: {e}")
        return

    if not plan:
        await message.answer(
            "Для тебя пока нет сохранённых планов. Попробуй /plan_week."
        )
        return

    # Сохраняем план в state, чтобы не дёргать API каждый раз
    await state.update_data(
        edit_plan_id=plan["plan_id"],
        edit_items=plan["items"],
    )

    text = _format_plan_text(plan)
    await message.answer(
        text + "\n\nВыбери пост, у которого хочешь изменить время:",
        reply_markup=_plan_items_edit_keyboard(plan),
    )
    await state.set_state(PlanEditStates.waiting_for_item_choice)

@router.callback_query(
    PlanEditStates.waiting_for_item_choice,
    F.data.startswith("edit_time_"),
)
async def plan_edit_choose_item(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    edit_items = data.get("edit_items") or []
    plan_id = data.get("edit_plan_id")

    if not plan_id or not edit_items:
        await callback.message.answer(
            "Не нашёл текущий план. Попробуй ещё раз через /plan_status и /plan_edit_time."
        )
        await state.clear()
        await callback.answer()
        return

    payload = callback.data  # edit_time_<item_id> или edit_time_done
    if payload == "edit_time_done":
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("Редактирование времени завершено.")
        await state.clear()
        await callback.answer()
        return

    try:
        item_id = int(payload.split("_")[-1])
    except ValueError:
        await callback.answer()
        return

    # Сохраняем выбранный item_id в state
    await state.update_data(
        edit_plan_id=plan_id,
        edit_items=edit_items,
        edit_item_id=item_id,
    )

    await callback.message.answer(
        "Напиши новое время для этого поста в формате ЧЧ:ММ.\nНапример: 16:30"
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
            "Не понял время. Напиши в формате ЧЧ:ММ, например 16:30."
        )
        return

    data = await state.get_data()
    plan_id = data.get("edit_plan_id")
    item_id = data.get("edit_item_id")
    edit_items = data.get("edit_items") or []

    if not plan_id or not item_id:
        await message.answer(
            "Не нашёл текущий план. Попробуй ещё раз через /plan_edit_time."
        )
        await state.clear()
        return

    # Обновляем время у выбранного item локально
    for item in edit_items:
        if item.get("item_id") == item_id:
            item["time"] = new_time
            break

    await message.answer("Обновляю время поста в плане…")

    try:
        await update_plan_times_api(
            plan_id=plan_id,
            items=[{"item_id": item_id, "time": new_time}],
        )
    except Exception as e:
        await message.answer(f"Не удалось обновить время: {e}")
        await state.clear()
        return

    # Сохраняем обновлённый список в state
    await state.update_data(edit_items=edit_items)

    # Покажем обновлённый план
    try:
        plan = await get_current_plan_api(message.from_user.id)
    except Exception as e:
        await message.answer(f"Не удалось заново получить план: {e}")
        await state.clear()
        return

    text = _format_plan_text(plan)
    await message.answer(
        text + "\n\nЕсли хочешь, можешь изменить время ещё одного поста:",
        reply_markup=_plan_items_edit_keyboard(plan),
    )
    await state.set_state(PlanEditStates.waiting_for_item_choice)




