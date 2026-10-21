from urllib.parse import quote

from aiogram.types import InlineKeyboardButton as B
from aiogram.types import InlineKeyboardMarkup


def kb(*rows) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[B(text=t, callback_data=d) for t, d in row] for row in rows]
    )


def main_kb():
    return kb(
        [("🎮 O'yinlar", "games")],
        [("👤 Profil", "profile"), ("🎁 Kunlik sovg'a", "daily")],
        [("🏆 Reyting", "top"), ("💎 Premium do'kon", "shop")],
        [("👥 Do'stlarni taklif qilish", "friends")],
    )


def back_kb(to="menu", text="⬅️ Orqaga"):
    return kb([(text, to)])


def share_kb(link: str):
    text = "👑 Eng premium o'yin botiga qo'shil! Bonus olasan 🎁"
    url = f"https://t.me/share/url?url={quote(link)}&text={quote(text)}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [B(text="📤 Do'stlarga ulashish", url=url)],
            [B(text="⬅️ Orqaga", callback_data="menu")],
        ]
    )
