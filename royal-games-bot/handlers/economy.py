import time

from aiogram import F, Router
from aiogram.types import CallbackQuery

import config
from database import Database
from keyboards import kb
from utils import fmt, safe_edit, vip_level

router = Router()


@router.callback_query(F.data == "shop")
async def cb_shop(cb: CallbackQuery, db: Database):
    u = await db.user(cb.from_user.id)
    lines = []
    rows = []
    for lvl, (name, icon, mult, cost) in config.VIP_TIERS.items():
        if lvl == 0:
            continue
        lines.append(f"{icon} <b>{name}</b> — {cost} 💎 · kunlik bonus <b>x{mult}</b>")
        rows.append([(f"{icon} {name} — {cost} 💎", f"shop:vip:{lvl}")])
    rows.append([("💱 Valyuta almashtirish", "shop:ex")])
    rows.append([("⬅️ Orqaga", "menu")])
    text = (
        "💎 <b>PREMIUM DO'KON</b>\n━━━━━━━━━━━━━━━━\n"
        f"VIP obuna ({config.VIP_DAYS} kun):\n" + "\n".join(lines) +
        f"\n━━━━━━━━━━━━━━━━\n💰 <b>{fmt(u['coins'])}</b> 🪙   💎 <b>{fmt(u['gems'])}</b>"
    )
    await safe_edit(cb, text, kb(*rows))
    await cb.answer()


@router.callback_query(F.data.startswith("shop:vip:"))
async def cb_vip(cb: CallbackQuery, db: Database):
    try:
        lvl = int(cb.data.split(":")[2])
    except ValueError:
        return await cb.answer()
    if lvl not in config.VIP_TIERS or lvl == 0:
        return await cb.answer()
    uid = cb.from_user.id
    u = await db.user(uid)
    cur = vip_level(u)
    if cur > lvl:
        return await cb.answer("Sizda bundan yuqori VIP faol!", show_alert=True)
    name, icon, mult, cost = config.VIP_TIERS[lvl]
    if not await db.charge(uid, gems=cost):
        return await cb.answer(f"❌ {cost} 💎 kerak. Kunlik sovg'a va do'stlar orqali toping!", show_alert=True)
    now = int(time.time())
    base = u["vip_until"] if cur == lvl else now
    await db.set_vip(uid, lvl, max(base, now) + config.VIP_DAYS * 86400)
    await safe_edit(
        cb,
        f"{icon} <b>{name} VIP faollashtirildi!</b>\n━━━━━━━━━━━━━━━━\n"
        f"Muddat: {config.VIP_DAYS} kun\nKunlik bonus: <b>x{mult}</b>\n\n👑 Rahmat!",
        kb([("💎 Do'konga qaytish", "shop")], [("🏠 Menyu", "menu")]),
    )
    await cb.answer("👑 VIP faol!")


@router.callback_query(F.data == "shop:ex")
async def cb_ex(cb: CallbackQuery, db: Database):
    u = await db.user(cb.from_user.id)
    text = (
        "💱 <b>VALYUTA ALMASHTIRISH</b>\n━━━━━━━━━━━━━━━━\n"
        f"Sotib olish: 1 💎 = <b>{fmt(config.COIN_TO_GEM)}</b> 🪙\n"
        f"Sotish: 1 💎 = <b>{fmt(config.GEM_TO_COIN)}</b> 🪙\n━━━━━━━━━━━━━━━━\n"
        f"💰 <b>{fmt(u['coins'])}</b> 🪙   💎 <b>{fmt(u['gems'])}</b>"
    )
    await safe_edit(
        cb, text,
        kb([(f"🪙→💎 {n}", f"ex:cg:{n}") for n in (1, 5, 25)],
           [(f"💎→🪙 {n}", f"ex:gc:{n}") for n in (1, 5, 25)],
           [("⬅️ Orqaga", "shop")]),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("ex:"))
async def cb_do_ex(cb: CallbackQuery, db: Database):
    try:
        _, mode, a = cb.data.split(":")
        n = int(a)
    except ValueError:
        return await cb.answer()
    if n not in (1, 5, 25):
        return await cb.answer()
    uid = cb.from_user.id
    if mode == "cg":
        if not await db.charge(uid, coins=config.COIN_TO_GEM * n):
            return await cb.answer("❌ Coin yetarli emas!", show_alert=True)
        await db.credit(uid, gems=n)
        await cb.answer(f"✅ +{n} 💎")
    elif mode == "gc":
        if not await db.charge(uid, gems=n):
            return await cb.answer("❌ Gem yetarli emas!", show_alert=True)
        await db.credit(uid, coins=config.GEM_TO_COIN * n)
        await cb.answer(f"✅ +{fmt(config.GEM_TO_COIN * n)} 🪙")
    else:
        return await cb.answer()
    await cb_ex(cb, db)
