# 👑 ROYAL GAMES — Telegram premium o'yin boti

Slot, Dice dueli, Tanga, Xazina · Kunlik sovg'a · Level/XP · VIP (Silver→Diamond) · Reyting · Referal · Admin panel.

## GitHub Codespaces'da sinash (eng oson)
1. Repo'ni GitHub'ga yuklang → **Code → Codespaces → Create codespace**.
2. Terminalda: `.env` faylni oching, `BOT_TOKEN` (@BotFather) va `ADMIN_IDS` (o'z ID'ingiz) ni yozing.
3. `python main.py`

## GitHub Actions orqali ishga tushirish
1. Repo → **Settings → Secrets and variables → Actions** → `BOT_TOKEN` va `ADMIN_IDS` qo'shing.
2. **Actions → Run Bot → Run workflow**. Bot ~6 soat ishlaydi va har 6 soatda qayta ishga tushadi.
> ⚠️ Actions'da baza (SQLite) har qayta ishga tushganda tozalanadi. Doimiy ishlash uchun VPS/Railway/Fly.io ga o'ting (`DB_PATH` ni doimiy diskka qo'ying).

## Admin buyruqlari
`/stats` · `/give <id> <coins> [gems]` · `/broadcast <matn>`
