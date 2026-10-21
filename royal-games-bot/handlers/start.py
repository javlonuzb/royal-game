import html
import time

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

import config
from database import Database
from keyboards import back_kb, main_kb, share_kb
from utils import (bar, esc, fmt, human_td, level_bounds, level_of, menu_text,
                   safe_edit, vip_level)

router = Router()


@router.message(CommandStart())
async def cmd_start(m: Message, db: Database, bot: Bot, command: CommandObject, is_new: bool):
    uid = m.from_user.id
    note = ""
    if is_new and command.args and command.args.startswith("ref_"):
        try:
            ref = int(command.args[4:])
        except ValueError:
            ref = 0
        if ref and ref != uid and await db.user(ref) and await db.set_referrer(uid, ref):
            note = f"\n\n🎁 <b>Taklif bonusi:</b> +{fmt(config.REF_INVITEE_COINS)} 🪙"
            try:
                await bot.send_message(
                    ref,
                    f"👥 <b>{esc(m.from_user.full_name)}</b> sizning havolangiz orqali qo'shildi!\n"
                    f"🎁 +{fmt(config.REF_INVITER_COINS)} 🪙  +{config.REF_INVITER_GEMS} 💎",
                )
            except Exception:
                pass
    u = await db.user(uid)
    welcome = ""
    if is_new:
        welcome = (
            f"\n\n🎉 Xush kelibsiz! Sizga start bonusi berildi: "
            f"<b>{fmt(config.START_COINS)} 🪙</b> va <b>{config.START_GEMS} 💎</b>"
        )
    await m.answer(menu_text(u) + welcome + note, reply_markup=main_kb())


@router.message(Command("menu"))
async def cmd_menu(m: Message, db: Database):
    await m.answer(menu_text(await db.user(m.from_user.id)), reply_markup=main_kb())


@router.callback_query(F.data == "menu")
async def cb_menu(cb: CallbackQuery, db: Database):
    await safe_edit(cb, menu_text(await db.user(cb.from_user.id)), main_kb())
    await cb.answer()


@router.callback_query(F.data == "profile")
async def cb_profile(cb: CallbackQuery, db: Database):
    u = await db.user(cb.from_user.id)
    lvl = level_of(u["xp"])
    lo, hi = level_bounds(lvl)
    v = vip_level(u)
    name, icon, mult, _ = config.VIP_TIERS[v]
    vip_line = f"{icon} VIP: <b>{name}</b>"
    if v:
        vip_line += f" · {max((u['vip_until'] - int(time.time())) // 86400, 0)} kun qoldi (bonus x{mult})"
    winrate = round(u["wins"] / u["games"] * 100) if u["games"] else 0
    text = (
        f"👤 <b>{esc(u['full_name'])}</b>\n"
        f"🆔 <code>{u['id']}</code>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 Coins: <b>{fmt(u['coins'])}</b>\n"
        f"💎 Gems: <b>{fmt(u['gems'])}</b>\n"
        f"{vip_line}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⭐ Level <b>{lvl}</b>\n"
        f"{bar(u['xp'] - lo, hi - lo)}  {fmt(u['xp'] - lo)}/{fmt(hi - lo)} XP\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎮 O'yinlar: <b>{fmt(u['games'])}</b>\n"
        f"🏆 G'alabalar: <b>{fmt(u['wins'])}</b> ({winrate}%)\n"
        f"📈 Jami sof yutuq: <b>{fmt(u['total_won'])}</b> 🪙\n"
        f"👥 Do'stlar: <b>{u['refs']}</b>"
    )
    await safe_edit(cb, text, back_kb())
    await cb.answer()


@router.callback_query(F.data == "daily")
async def cb_daily(cb: CallbackQuery, db: Database):
    uid = cb.from_user.id
    u = await db.user(uid)
    now = int(time.time())
    left = 86400 - (now - u["last_daily"])
    if u["last_daily"] and left > 0:
        await cb.answer(f"⏳ Keyingi sovg'a: {human_td(left)} dan keyin", show_alert=True)
        return
    streak = u["streak"] + 1 if u["last_daily"] and now - u["last_daily"] < 172800 else 1
    day = (streak - 1) % 7 + 1
    mult = config.VIP_TIERS[vip_level(u)][2]
    coins = int((1000 + 500 * (day - 1)) * mult)
    gems = 5 if day == 7 else 0
    await db.credit(uid, coins=coins, gems=gems)
    await db.set_daily(uid, streak, now)
    track = "".join("✅" if i < day else ("🎁" if i == 6 else "⬜") for i in range(7))
    text = (
        f"🎁 <b>KUNLIK SOVG'A</b>\n━━━━━━━━━━━━━━━━\n"
        f"{track}\n"
        f"🔥 Ketma-ket kun: <b>{streak}</b>\n\n"
        f"💰 +<b>{fmt(coins)}</b> 🪙" + (f"\n💎 +<b>{gems}</b> (7-kun bonusi!)" if gems else "") +
        "\n\n<i>Ertaga qaytib keling — bonus oshib boradi!</i>"
    )
    await safe_edit(cb, text, back_kb())
    await cb.answer("🎁 Sovg'a olindi!")


@router.callback_query(F.data == "top")
async def cb_top(cb: CallbackQuery, db: Database):
    rows = await db.top(10)
    medals = ["🥇", "🥈", "🥉"] + [f"{i}." for i in range(4, 11)]
    lines = []
    for i, r in enumerate(rows):
        icon = config.VIP_TIERS[vip_level(r)][1] if vip_level(r) else ""
        lines.append(f"{medals[i]} {icon}{esc(r['full_name'])[:18]} — <b>{fmt(r['coins'])}</b> 🪙")
    rank = await db.rank(cb.from_user.id)
    text = (
        "🏆 <b>TOP 10 — ENG BOYLAR</b>\n━━━━━━━━━━━━━━━━\n"
        + "\n".join(lines)
        + f"\n━━━━━━━━━━━━━━━━\n📍 Sizning o'rningiz: <b>#{rank}</b>"
    )
    await safe_edit(cb, text, back_kb())
    await cb.answer()


@router.callback_query(F.data == "friends")
async def cb_friends(cb: CallbackQuery, db: Database, bot: Bot):
    me = await bot.me()
    u = await db.user(cb.from_user.id)
    link = f"https://t.me/{me.username}?start=ref_{u['id']}"
    text = (
        "👥 <b>DO'STLARNI TAKLIF QILING</b>\n━━━━━━━━━━━━━━━━\n"
        f"Har bir do'st uchun:\n🎁 <b>+{fmt(config.REF_INVITER_COINS)}</b> 🪙 va <b>+{config.REF_INVITER_GEMS}</b> 💎\n"
        f"Do'stingiz ham <b>+{fmt(config.REF_INVITEE_COINS)}</b> 🪙 oladi.\n\n"
        f"📊 Taklif qilinganlar: <b>{u['refs']}</b>\n\n"
        f"🔗 Sizning havolangiz:\n<code>{html.escape(link)}</code>"
    )
    await safe_edit(cb, text, share_kb(link))
    await cb.answer()
