import asyncio
import logging
import random

from aiogram import F, Router
from aiogram.types import CallbackQuery

import config
from database import Database
from keyboards import kb
from utils import fmt, levelup_text, safe_edit

router = Router()
log = logging.getLogger(__name__)
rng = random.SystemRandom()
busy: set[int] = set()

GAMES = {
    "slots": ("🎰", "Slot mashinasi",
              "🎰 777 → <b>x20</b> + 3 💎\n🍇🍋🅱️ uchtalik → <b>x8</b>\nIkkita bir xil → <b>x0.5</b>"),
    "dice": ("🎲", "Dice dueli",
             "Siz va dealer kub tashlaysiz — kattasi yutadi!\n🏆 G'alaba → <b>x1.9</b>\n🤝 Durang → stavka qaytadi"),
    "coin": ("🪙", "Tanga",
             "Gerb yoki Raqam — tanlang!\n🏆 To'g'ri topsangiz → <b>x1.95</b>"),
    "chest": ("🗝", "Xazina sandig'i",
              "3 ta sandiqdan birida xazina yashirilgan.\n🏆 Topsangiz → <b>x2.8</b>"),
}
SYMBOLS = ["🅱️", "🍇", "🍋", "7️⃣"]


def result_kb(key, bet):
    return kb(
        [(f"🔁 Yana {fmt(bet)} 🪙", f"bet:{key}:{bet}")],
        [("🎚 Stavkani o'zgartirish", f"game:{key}"), ("🏠 Menyu", "menu")],
    )


@router.callback_query(F.data == "games")
async def cb_games(cb: CallbackQuery):
    rows = [[(f"{e} {n}", f"game:{k}")] for k, (e, n, _) in GAMES.items()]
    rows.append([("⬅️ Orqaga", "menu")])
    await safe_edit(cb, "🎮 <b>O'YINLAR</b>\n━━━━━━━━━━━━━━━━\nO'yinni tanlang 👇", kb(*rows))
    await cb.answer()


@router.callback_query(F.data.startswith("game:"))
async def cb_game(cb: CallbackQuery, db: Database):
    key = cb.data.split(":")[1]
    if key not in GAMES:
        return await cb.answer()
    e, name, desc = GAMES[key]
    u = await db.user(cb.from_user.id)
    bets = config.BETS
    rows = [[(f"{fmt(b)} 🪙", f"bet:{key}:{b}") for b in bets[i:i + 3]] for i in range(0, len(bets), 3)]
    rows.append([("⬅️ Orqaga", "games")])
    text = (f"{e} <b>{name.upper()}</b>\n━━━━━━━━━━━━━━━━\n{desc}\n━━━━━━━━━━━━━━━━\n"
            f"💰 Balans: <b>{fmt(u['coins'])}</b> 🪙\n\n<b>Stavkani tanlang:</b>")
    await safe_edit(cb, text, kb(*rows))
    await cb.answer()


async def play_slots(cb, bet):
    msg = await cb.message.answer_dice(emoji="🎰")
    v = msg.dice.value - 1
    reels = [v & 3, (v >> 2) & 3, (v >> 4) & 3]
    await asyncio.sleep(2.8)
    line = "  ".join(SYMBOLS[r] for r in reels)
    gems = 0
    if reels == [3, 3, 3]:
        mult, gems, title = 20, 3, "🔥 <b>JACKPOT 777!</b> 🔥"
    elif len(set(reels)) == 1:
        mult, title = 8, "✨ <b>Uchta bir xil!</b>"
    elif len(set(reels)) == 2:
        mult, title = 0.5, "Ikkita bir xil"
    else:
        mult, title = 0, "Omad kelmadi"
    body = f"🎰 <b>SLOT MASHINASI</b>\n━━━━━━━━━━━━━━━━\n{line}\n{title}\n"
    return int(bet * mult), body, False, gems


async def play_dice(cb, bet):
    await cb.message.answer("🎲 <b>Dice dueli</b>\n1-kub — <b>siz</b>, 2-kub — <b>dealer</b>")
    m1 = await cb.message.answer_dice(emoji="🎲")
    m2 = await cb.message.answer_dice(emoji="🎲")
    a, b = m1.dice.value, m2.dice.value
    await asyncio.sleep(4)
    payout = int(bet * 1.9) if a > b else (bet if a == b else 0)
    body = f"🎲 <b>DICE DUELI</b>\n━━━━━━━━━━━━━━━━\n👤 Siz: <b>{a}</b>\n🎩 Dealer: <b>{b}</b>\n"
    return payout, body, False, 0


async def play_coin(cb, bet, side):
    await safe_edit(cb, "🪙 <b>Tanga havoga uloqtirildi...</b>")
    await asyncio.sleep(1.0)
    await safe_edit(cb, "🌀 <b>Aylanmoqda...</b>")
    await asyncio.sleep(1.0)
    res = rng.choice("ht")
    names = {"h": "🦅 Gerb", "t": "🔢 Raqam"}
    payout = int(bet * 1.95) if res == side else 0
    body = (f"🪙 <b>TANGA</b>\n━━━━━━━━━━━━━━━━\nSiz tanladingiz: <b>{names[side]}</b>\n"
            f"Tushdi: <b>{names[res]}</b>\n")
    return payout, body, True, 0


async def play_chest(cb, bet, pick):
    await safe_edit(cb, "🗝 <b>Sandiq ochilmoqda...</b>")
    await asyncio.sleep(1.2)
    win = rng.randint(1, 3)
    boxes = "   ".join("💎" if i == win else "💀" for i in (1, 2, 3))
    payout = int(bet * 2.8) if pick == win else 0
    body = (f"🗝 <b>XAZINA SANDIG'I</b>\n━━━━━━━━━━━━━━━━\n{boxes}\n"
            f"Siz tanladingiz: <b>{pick}-sandiq</b>\n")
    return payout, body, True, 0


async def run(cb: CallbackQuery, db: Database, key: str, bet: int, *args):
    uid = cb.from_user.id
    if uid in busy:
        return await cb.answer("⏳ O'yin davom etmoqda...")
    if not await db.charge(uid, coins=bet):
        return await cb.answer("❌ Mablag' yetarli emas! Kunlik sovg'ani oling 🎁", show_alert=True)
    busy.add(uid)
    await cb.answer()
    try:
        fn = {"slots": play_slots, "dice": play_dice, "coin": play_coin, "chest": play_chest}[key]
        try:
            payout, body, edit, gems = await fn(cb, bet, *args)
        except Exception:
            log.exception("O'yin xatosi — stavka qaytarildi")
            await db.credit(uid, coins=bet)
            await cb.message.answer("⚠️ Xatolik yuz berdi. Stavkangiz qaytarildi.")
            return
        old, new = await db.settle(uid, bet, payout, gems)
        u = await db.user(uid)
        if payout > bet:
            foot = f"🏆 <b>Yutuq: +{fmt(payout - bet)}</b> 🪙" + (f"  💎 +{gems}" if gems else "")
        elif payout == bet:
            foot = "🤝 Stavka qaytdi"
        elif payout > 0:
            foot = f"💸 Qaytim: {fmt(payout)} (−{fmt(bet - payout)}) 🪙"
        else:
            foot = f"💔 Yutqazdingiz: −{fmt(bet)} 🪙"
        text = (f"{body}━━━━━━━━━━━━━━━━\n{foot}\n💰 Balans: <b>{fmt(u['coins'])}</b> 🪙"
                f"{levelup_text(old, new)}")
        if edit:
            await safe_edit(cb, text, result_kb(key, bet))
        else:
            await cb.message.answer(text, reply_markup=result_kb(key, bet))
    finally:
        busy.discard(uid)


@router.callback_query(F.data.startswith("bet:"))
async def cb_bet(cb: CallbackQuery, db: Database):
    try:
        _, key, a = cb.data.split(":")
        bet = int(a)
    except ValueError:
        return await cb.answer()
    if key not in GAMES or bet not in config.BETS:
        return await cb.answer()
    uid = cb.from_user.id
    if uid in busy:
        return await cb.answer("⏳ O'yin davom etmoqda...")
    u = await db.user(uid)
    if u["coins"] < bet:
        return await cb.answer("❌ Mablag' yetarli emas!", show_alert=True)
    if key == "coin":
        await safe_edit(cb, f"🪙 <b>TANGA</b> · Stavka: <b>{fmt(bet)}</b> 🪙\n\nTomonni tanlang 👇",
                        kb([("🦅 Gerb", f"pick:coin:h:{bet}"), ("🔢 Raqam", f"pick:coin:t:{bet}")],
                           [("⬅️ Orqaga", "game:coin")]))
        return await cb.answer()
    if key == "chest":
        await safe_edit(cb, f"🗝 <b>XAZINA</b> · Stavka: <b>{fmt(bet)}</b> 🪙\n\nSandiqni tanlang 👇",
                        kb([(f"📦 {i}", f"pick:chest:{i}:{bet}") for i in (1, 2, 3)],
                           [("⬅️ Orqaga", "game:chest")]))
        return await cb.answer()
    await run(cb, db, key, bet)


@router.callback_query(F.data.startswith("pick:"))
async def cb_pick(cb: CallbackQuery, db: Database):
    try:
        _, key, choice, a = cb.data.split(":")
        bet = int(a)
    except ValueError:
        return await cb.answer()
    if bet not in config.BETS:
        return await cb.answer()
    if key == "coin" and choice in ("h", "t"):
        await run(cb, db, "coin", bet, choice)
    elif key == "chest" and choice in ("1", "2", "3"):
        await run(cb, db, "chest", bet, int(choice))
    else:
        await cb.answer()
