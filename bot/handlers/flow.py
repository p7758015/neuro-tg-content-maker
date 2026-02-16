from aiogram import Router, types, F

router = Router()


@router.callback_query(F.data == "next_style_capture")
async def cb_next_style_capture(callback: types.CallbackQuery):
    await callback.message.answer(
        "Стиль уже снят. Теперь:\n"
        "1) Подключи канал, если ещё не подключал — /connect_channel.\n"
        "2) Сделай план постов на неделю — /plan_week.\n"
        "3) При необходимости измени время постов — /plan_edit_time."
    )
    await callback.answer()


@router.callback_query(F.data == "next_post")
async def cb_next_post(callback: types.CallbackQuery):
    await callback.message.answer(
        "Чтобы посмотреть следующий пост по плану в личке, используй команду /post.\n\n"
        "Команда /post показывает текст ближайшего поста по графику в личку — "
        "он не считается опубликованным.\n"
        "Команда /autopost_demo отправляет ближайший пост прямо в канал и помечает его как отправленный."
    )
    await callback.answer()


@router.callback_query(F.data == "next_planweek")
async def cb_next_planweek(callback: types.CallbackQuery):
    await callback.message.answer(
        "Сделать план постов на неделю можно командой /plan_week.\n"
        "После одобрения плана посты будут автоматически выходить по графику."
    )
    await callback.answer()


@router.callback_query(F.data == "next_planstatus")
async def cb_next_planstatus(callback: types.CallbackQuery):
    await callback.message.answer(
        "Посмотреть текущий план можно командой /plan_status.\n"
        "Если нужно — измени время постов через /plan_edit_time."
    )
    await callback.answer()


@router.callback_query(F.data == "next_autopostdemo")
async def cb_next_autopostdemo(callback: types.CallbackQuery):
    await callback.message.answer(
        "Тестовый автопост ближайшего поста в канал — команда /autopost_demo.\n"
        "После неё этот пост считается отправленным, и следующий /post покажет уже другой пост."
    )
    await callback.answer()


@router.callback_query(F.data == "next_plan_edit_time")
async def cb_next_plan_edit_time(callback: types.CallbackQuery):
    await callback.message.answer(
        "Чтобы изменить время постов в уже созданном плане, используй команду /plan_edit_time.\n\n"
        "После изменения времени бот подтвердит, что расписание обновлено, и посты будут "
        "выходить по новому графику."
    )
    await callback.answer()
