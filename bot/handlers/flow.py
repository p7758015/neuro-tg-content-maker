from aiogram import Router, types, F

router = Router()

@router.callback_query(F.data == "next_style_capture")
async def cb_next_style_capture(callback: types.CallbackQuery):
    await callback.message.answer(
        "Чтобы ещё раз снять стиль, используй команду /connect_channel."
    )
    await callback.answer()

@router.callback_query(F.data == "next_post")
async def cb_next_post(callback: types.CallbackQuery):
    await callback.message.answer(
        "Чтобы сгенерировать пост, отправь команду /post."
    )
    await callback.answer()

@router.callback_query(F.data == "next_plan_week")
async def cb_next_plan_week(callback: types.CallbackQuery):
    await callback.message.answer(
        "Чтобы сделать план на неделю, отправь команду /plan_week."
    )
    await callback.answer()

@router.callback_query(F.data == "next_plan_status")
async def cb_next_plan_status(callback: types.CallbackQuery):
    await callback.message.answer(
        "Чтобы посмотреть текущий план, отправь команду /plan_status."
    )
    await callback.answer()

@router.callback_query(F.data == "next_autopost_demo")
async def cb_next_autopost_demo(callback: types.CallbackQuery):
    await callback.message.answer(
        "Чтобы отправить ближайший пост по плану, отправь команду /autopost_demo."
    )
    await callback.answer()


