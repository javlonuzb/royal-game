import asyncio
import html

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

import config
from database import Database
from utils import fmt

router = Router()
router.message.filter(F.from_user.id.in_(config.ADMIN_IDS))


@router.message(Command("stats"))
async def stats(m: Message, db: Database):
    users, coins, games = await db.stats()
    await m.answer(f"📊 <b>Statistika</b>\n👥 Foydalanuvchilar: <b>{fmt(users)}</b>\n"
                   f"💰 Jami coin: <b>{fmt(coins)}</b>\n🎮 O'yinlar: <b>{fmt(games)}</b>")


@router.message(Command("give"))
async def give(m: Message, db: Database, command: CommandObject):
    """/give <user_id> <coins> [gems]"""
    try:
        parts = (command.args or "").split()
        uid, coins = int(parts[0]), int(parts[1])
        gems = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        return await m.answer("Format: /give <user_id> <coins> [gems]")
    if not await db.user(uid):
        return await m.answer("❌ Foydalanuvchi topilmadi")
    await db.credit(uid, coins=coins, gems=gems)
    await m.answer(f"✅ {uid} ga +{fmt(coins)} 🪙 +{gems} 💎")


@router.message(Command("broadcast"))
async def broadcast(m: Message, db: Database, bot: Bot, command: CommandObject):
    if not command.args:
        return await m.answer("Format: /broadcast <matn> (HTML qo'llab-quvvatlanadi)")
    ok = fail = 0
    for uid in await db.all_ids():
        try:
            await bot.send_message(uid, command.args)
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await m.answer(f"📣 Yuborildi: {ok} · Xato: {fail}")
