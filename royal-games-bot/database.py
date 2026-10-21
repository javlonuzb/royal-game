import os
import time

import aiosqlite

import config
from utils import level_of

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    username TEXT, full_name TEXT,
    coins INTEGER NOT NULL DEFAULT 0,
    gems INTEGER NOT NULL DEFAULT 0,
    xp INTEGER NOT NULL DEFAULT 0,
    vip INTEGER NOT NULL DEFAULT 0,
    vip_until INTEGER NOT NULL DEFAULT 0,
    streak INTEGER NOT NULL DEFAULT 0,
    last_daily INTEGER NOT NULL DEFAULT 0,
    referrer INTEGER,
    refs INTEGER NOT NULL DEFAULT 0,
    games INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    total_won INTEGER NOT NULL DEFAULT 0,
    created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_coins ON users(coins DESC);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def ensure_user(self, uid, username, full_name) -> bool:
        cur = await self.conn.execute("SELECT 1 FROM users WHERE id=?", (uid,))
        if await cur.fetchone():
            await self.conn.execute(
                "UPDATE users SET username=?, full_name=? WHERE id=?", (username, full_name, uid)
            )
            await self.conn.commit()
            return False
        await self.conn.execute(
            "INSERT INTO users(id, username, full_name, coins, gems, created) VALUES(?,?,?,?,?,?)",
            (uid, username, full_name, config.START_COINS, config.START_GEMS, int(time.time())),
        )
        await self.conn.commit()
        return True

    async def user(self, uid) -> dict | None:
        cur = await self.conn.execute("SELECT * FROM users WHERE id=?", (uid,))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def charge(self, uid, coins=0, gems=0) -> bool:
        cur = await self.conn.execute(
            "UPDATE users SET coins=coins-?, gems=gems-? WHERE id=? AND coins>=? AND gems>=?",
            (coins, gems, uid, coins, gems),
        )
        await self.conn.commit()
        return cur.rowcount > 0

    async def credit(self, uid, coins=0, gems=0):
        await self.conn.execute(
            "UPDATE users SET coins=coins+?, gems=gems+? WHERE id=?", (coins, gems, uid)
        )
        await self.conn.commit()

    async def settle(self, uid, bet, payout, gems=0):
        """O'yin yakuni: yutuqni berish, XP, statistika, level-up."""
        u = await self.user(uid)
        old = level_of(u["xp"])
        won = payout > bet
        gain = 5 + (15 if won else 0)
        new = level_of(u["xp"] + gain)
        bonus_gems = gems + (new - old) * 3
        await self.conn.execute(
            "UPDATE users SET coins=coins+?, gems=gems+?, xp=xp+?, games=games+1, "
            "wins=wins+?, total_won=total_won+? WHERE id=?",
            (payout, bonus_gems, gain, 1 if won else 0, max(payout - bet, 0), uid),
        )
        await self.conn.commit()
        return old, new

    async def set_referrer(self, uid, ref) -> bool:
        cur = await self.conn.execute(
            "UPDATE users SET referrer=? WHERE id=? AND referrer IS NULL", (ref, uid)
        )
        if cur.rowcount == 0:
            await self.conn.commit()
            return False
        await self.conn.execute(
            "UPDATE users SET coins=coins+?, gems=gems+?, refs=refs+1 WHERE id=?",
            (config.REF_INVITER_COINS, config.REF_INVITER_GEMS, ref),
        )
        await self.conn.execute(
            "UPDATE users SET coins=coins+? WHERE id=?", (config.REF_INVITEE_COINS, uid)
        )
        await self.conn.commit()
        return True

    async def set_daily(self, uid, streak, ts):
        await self.conn.execute(
            "UPDATE users SET streak=?, last_daily=? WHERE id=?", (streak, ts, uid)
        )
        await self.conn.commit()

    async def set_vip(self, uid, level, until):
        await self.conn.execute(
            "UPDATE users SET vip=?, vip_until=? WHERE id=?", (level, until, uid)
        )
        await self.conn.commit()

    async def top(self, limit=10):
        cur = await self.conn.execute(
            "SELECT id, full_name, coins, vip, vip_until FROM users ORDER BY coins DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in await cur.fetchall()]

    async def rank(self, uid) -> int:
        cur = await self.conn.execute(
            "SELECT COUNT(*)+1 FROM users WHERE coins > (SELECT coins FROM users WHERE id=?)", (uid,)
        )
        return (await cur.fetchone())[0]

    async def stats(self):
        cur = await self.conn.execute("SELECT COUNT(*), COALESCE(SUM(coins),0), COALESCE(SUM(games),0) FROM users")
        return tuple(await cur.fetchone())

    async def all_ids(self):
        cur = await self.conn.execute("SELECT id FROM users")
        return [r[0] for r in await cur.fetchall()]
