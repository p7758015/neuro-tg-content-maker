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
from bot.handlers import channel as channel_handlers


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запуск и инструкция"),
        BotCommand(command="connect_channel", description="Подключить канал и снять стиль"),
        BotCommand(command="post", description="Показать следующий пост по плану в личке"),
        BotCommand(command="plan_week", description="Сделать план постов на неделю"),
        BotCommand(command="plan_status", description="Показать текущий план"),
        BotCommand(command="plan_edit_time", description="Изменить время постов в плане"),
        BotCommand(command="autopost_demo", description="Тестовый автопост ближайшего поста в канал"),
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
    dp.include_router(channel_handlers.router)

    await set_bot_commands(bot)

    print("Bot started. Press Ctrl+C to stop.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
