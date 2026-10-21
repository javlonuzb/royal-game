import html
import math
import time

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from config import BRAND, VIP_TIERS


def fmt(n) -> str:
    return f"{int(n):,}".replace(",", " ")


def esc(s: str) -> str:
    return html.escape(s or "Foydalanuvchi")


def level_of(xp: int) -> int:
    return int(math.sqrt(max(xp, 0) / 100)) + 1


def level_bounds(level: int):
    return (level - 1) ** 2 * 100, level ** 2 * 100


def bar(cur: int, total: int, n: int = 10) -> str:
    filled = int(n * cur / total) if total else 0
    return "▰" * filled + "▱" * (n - filled)


def vip_level(u: dict) -> int:
    return u["vip"] if u["vip"] and u["vip_until"] > time.time() else 0


def human_td(sec: int) -> str:
    sec = max(int(sec), 0)
    h, r = divmod(sec, 3600)
    m = r // 60
    return f"{h} soat {m} daqiqa" if h else f"{m} daqiqa"


def menu_text(u: dict) -> str:
    name, icon, _, _ = VIP_TIERS[vip_level(u)]
    return (
        f"👑 <b>{html.escape(BRAND)}</b>\n"
        f"<i>Premium o'yin olami</i>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"{icon} <b>{esc(u['full_name'])}</b> · {name}\n"
        f"💰 <b>{fmt(u['coins'])}</b>   💎 <b>{fmt(u['gems'])}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Bo'limni tanlang 👇"
    )


def levelup_text(old: int, new: int) -> str:
    if new > old:
        return f"\n\n🎊 <b>LEVEL UP!</b> Endi siz {new}-darajasiz · +{(new - old) * 3} 💎"
    return ""


async def safe_edit(cb: CallbackQuery, text: str, markup=None):
    try:
        await cb.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "not modified" not in str(e):
            raise
