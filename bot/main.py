# bot/main.py
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeDefault

from bot.config import BOT_TOKEN
from bot.handlers import start as start_handlers
from bot.handlers import connect as connect_handlers
from bot.handlers import post as post_handlers
from bot.handlers import plan as plan_handlers
from bot.handlers import flow as flow_handlers


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="connect_channel", description="Снять стиль с канала"),
        BotCommand(command="post", description="Сгенерировать одиночный пост"),
        BotCommand(command="plan_week", description="Сделать план на неделю"),
        BotCommand(command="plan_status", description="Показать сохранённый план"),
        BotCommand(command="autopost_demo", description="Отправить пост по плану"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(start_handlers.router)
    dp.include_router(connect_handlers.router)
    dp.include_router(post_handlers.router)
    dp.include_router(plan_handlers.router)
    dp.include_router(flow_handlers.router)

    await set_bot_commands(bot)

    print("Bot started. Press Ctrl+C to stop.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())




