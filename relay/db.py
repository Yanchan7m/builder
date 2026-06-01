"""Stockage des signaux (journal) dans Postgres.

Optionnel : si DATABASE_URL n'est pas défini, les fonctions sont inertes
(le bot continue de marcher, simplement sans journal/dashboard).
"""
from __future__ import annotations

import os
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "")
ENABLED = bool(DATABASE_URL)

if ENABLED:
    import psycopg2
    import psycopg2.extras


@contextmanager
def _conn():
    c = psycopg2.connect(DATABASE_URL)
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db() -> None:
    if not ENABLED:
        return
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                market TEXT, strat TEXT, sym TEXT, side TEXT,
                entry DOUBLE PRECISION, sl DOUBLE PRECISION, tp DOUBLE PRECISION,
                score INT, size TEXT, rr DOUBLE PRECISION,
                result TEXT NOT NULL DEFAULT '',
                note   TEXT NOT NULL DEFAULT ''
            )
        """)


def insert_signal(sig, rr) -> None:
    if not ENABLED:
        return None
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "INSERT INTO signals (market,strat,sym,side,entry,sl,tp,score,size,rr) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (sig.market, sig.strat, sig.sym, sig.side, sig.entry, sig.sl, sig.tp,
             sig.score, sig.size, rr),
        )
        return cur.fetchone()[0]


def list_signals(limit: int = 300) -> list[dict]:
    if not ENABLED:
        return []
    with _conn() as c, c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM signals ORDER BY created_at DESC LIMIT %s", (limit,))
        rows = cur.fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["created_at"] = d["created_at"].isoformat()
        out.append(d)
    return out


def update_signal(sid: int, result=None, note=None) -> None:
    if not ENABLED:
        return
    sets, vals = [], []
    if result is not None:
        sets.append("result=%s")
        vals.append(result)
    if note is not None:
        sets.append("note=%s")
        vals.append(note)
    if not sets:
        return
    vals.append(sid)
    with _conn() as c, c.cursor() as cur:
        cur.execute(f"UPDATE signals SET {', '.join(sets)} WHERE id=%s", vals)


def delete_signal(sid: int) -> None:
    if not ENABLED:
        return
    with _conn() as c, c.cursor() as cur:
        cur.execute("DELETE FROM signals WHERE id=%s", (sid,))
