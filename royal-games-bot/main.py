import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

import config
from database import Database
from handlers import admin, economy, games, start
from middlewares import Throttle, UserMiddleware


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    if not config.BOT_TOKEN:
        sys.exit("❌ BOT_TOKEN topilmadi. .env faylga yoki GitHub Secrets ga qo'shing.")

    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    db = Database(config.DB_PATH)
    await db.connect()

    dp = Dispatcher()
    dp["db"] = db
    throttle, users = Throttle(), UserMiddleware(db)
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(throttle)
        observer.outer_middleware(users)

    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(games.router)
    dp.include_router(economy.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="👑 Botni ishga tushirish"),
        BotCommand(command="menu", description="🏠 Asosiy menyu"),
    ])
    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.me()
    logging.info("Bot ishga tushdi: @%s", me.username)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
