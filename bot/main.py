import asyncio
import logging
from aiogram import Bot, Dispatcher

from bot.config import BOT_TOKEN
from bot.handlers.commands import router as commands_router
from bot.handlers.messages import router as messages_router

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(commands_router)
    dp.include_router(messages_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
