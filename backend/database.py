# database.py
import sqlite3
import asyncpg
import logging
from config import NEON_DB_USER, NEON_DB_PASSWORD, NEON_DB_HOST, NEON_DB_PORT, NEON_DB_NAME, SQLITE_DB_PATH

# PostgreSQL (Neon) Connection
async def connect_to_neon():
    conn = await asyncpg.connect(
        user=NEON_DB_USER,
        password=NEON_DB_PASSWORD,
        database=NEON_DB_NAME,
        host=NEON_DB_HOST,
        port=NEON_DB_PORT
    )
    return conn

# Chat Logging Functions
async def log_chat(session_id, log_entry):
    conn = await connect_to_neon()
    try:
        existing_row = await conn.fetchrow(
            "SELECT log FROM chat_logs WHERE session_id = $1", session_id
        )
        
        if existing_row:
            existing_log = existing_row['log']
            updated_log = f"{existing_log} | {log_entry}"
            await conn.execute(
                "UPDATE chat_logs SET log = $1 WHERE session_id = $2",
                updated_log, session_id
            )
        else:
            await conn.execute(
                "INSERT INTO chat_logs (session_id, log, summary) VALUES ($1, $2, $3)",
                session_id, log_entry, ""
            )
    finally:
        await conn.close()

async def update_summary(session_id, summary):
    conn = await connect_to_neon()
    try:
        await conn.execute(
            "UPDATE chat_logs SET summary = $1 WHERE session_id = $2",
            summary, session_id
        )
    finally:
        await conn.close()

async def get_chat_data(session_id):
    conn = await connect_to_neon()
    try:
        row = await conn.fetchrow(
            "SELECT log, summary FROM chat_logs WHERE session_id = $1", session_id
        )
        return row
    finally:
        await conn.close()

# SQLite Content Database Functions
def fetch_keywords_data():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, keywords, content FROM extracted_data")
    records = cursor.fetchall()
    conn.close()
    return {record[0]: {"keyword": record[1], "content": record[2]} for record in records}

def get_content_by_id(content_id):
    data_dict = fetch_keywords_data()
    return data_dict.get(content_id, {}).get("content", "")