# bot/main.py
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import BOT_TOKEN
from bot.handlers import start as start_handlers
from bot.handlers import connect as connect_handlers
from bot.handlers import post as post_handlers
from bot.handlers import plan as plan_handlers


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

    print("Bot started. Press Ctrl+C to stop.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())



