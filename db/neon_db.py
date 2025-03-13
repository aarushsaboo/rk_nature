import asyncpg
from config import NEON_DB_USER, NEON_DB_PASSWORD, NEON_DB_HOST, NEON_DB_PORT, NEON_DB_NAME

async def connect_to_neon():
    conn = await asyncpg.connect(
        user=NEON_DB_USER,
        password=NEON_DB_PASSWORD,
        database=NEON_DB_NAME,
        host=NEON_DB_HOST,
        port=NEON_DB_PORT
    )
    return conn

async def fetch_neon_sessions():
    conn = await connect_to_neon()
    try:
        rows = await conn.fetch("SELECT session_id, log, summary FROM chat_logs")
        return [dict(row) for row in rows]
    finally:
        await conn.close()