import time

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery


class Throttle(BaseMiddleware):
    """Spamdan himoya: bir foydalanuvchidan tez-tez kelgan so'rovlarni o'tkazib yuboradi."""

    def __init__(self, rate: float = 0.45):
        self.rate = rate
        self.last: dict[int, float] = {}

    async def __call__(self, handler, event, data):
        user = event.from_user
        if user is None:
            return await handler(event, data)
        now = time.monotonic()
        if now - self.last.get(user.id, 0) < self.rate:
            if isinstance(event, CallbackQuery):
                await event.answer()
            return
        self.last[user.id] = now
        return await handler(event, data)


class UserMiddleware(BaseMiddleware):
    def __init__(self, db):
        self.db = db

    async def __call__(self, handler, event, data):
        u = event.from_user
        if u is None or u.is_bot:
            return
        data["is_new"] = await self.db.ensure_user(u.id, u.username, u.full_name)
        return await handler(event, data)
