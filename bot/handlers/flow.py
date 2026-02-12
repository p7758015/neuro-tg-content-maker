from aiogram import Router, types, F

router = Router()


@router.callback_query(F.data == "next_style_capture")
async def cb_next_style_capture(callback: types.CallbackQuery):
    await callback.message.answer(
        "Чтобы ещё раз снять стиль с другого канала, используй команду /connect_channel.\n\n"
        "После этого не забудь добавить бота админом в новый канал и отправить там /link_channel."
    )
    await callback.answer()


@router.callback_query(F.data == "next_post")
async def cb_next_post(callback: types.CallbackQuery):
    await callback.message.answer(
        "Чтобы сгенерировать одиночный пост в выбранном стиле, отправь команду /post."
    )
    await callback.answer()


@router.callback_query(F.data == "next_plan_week")
async def cb_next_plan_week(callback: types.CallbackQuery):
    await callback.message.answer(
        "Чтобы сделать план на неделю, отправь команду /plan_week.\n\n"
        "После генерации плана ты можешь изменить время отдельных постов командой /plan_edit_time."
    )
    await callback.answer()


@router.callback_query(F.data == "next_plan_status")
async def cb_next_plan_status(callback: types.CallbackQuery):
    await callback.message.answer(
        "Чтобы посмотреть текущий сохранённый план, отправь команду /plan_status.\n\n"
        "Если нужно поменять время постов — используй /plan_edit_time."
    )
    await callback.answer()


@router.callback_query(F.data == "next_autopost_demo")
async def cb_next_autopost_demo(callback: types.CallbackQuery):
    await callback.message.answer(
        "Чтобы посмотреть ближайший пост по плану и решить, отправлять ли его сейчас, "
        "отправь команду /autopost_demo.\n\n"
        "Я покажу превью поста и спрошу, отправлять ли его в канал."
    )
    await callback.answer()
