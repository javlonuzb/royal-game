import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.lstrip("-").isdigit()
}
DB_PATH = os.getenv("DB_PATH", "data/royal.db")
BRAND = os.getenv("BRAND", "ROYAL GAMES")

# Iqtisod
START_COINS = 10_000
START_GEMS = 10
REF_INVITER_COINS = 5_000
REF_INVITER_GEMS = 5
REF_INVITEE_COINS = 2_500
BETS = [100, 500, 1_000, 5_000, 10_000, 50_000]
COIN_TO_GEM = 20_000   # 1 💎 = 20 000 🪙 (sotib olish)
GEM_TO_COIN = 5_000    # 1 💎 = 5 000 🪙 (sotish)
VIP_DAYS = 30

# daraja: (nomi, belgi, kunlik bonus koeffitsiyenti, narxi 💎)
VIP_TIERS = {
    0: ("Oddiy", "👤", 1.0, 0),
    1: ("Silver", "🥈", 1.25, 30),
    2: ("Gold", "🥇", 1.5, 100),
    3: ("Platinum", "💠", 2.0, 300),
    4: ("Diamond", "💎", 3.0, 800),
}
