import sqlite3
import asyncpg
import logging
from config import NEON_DB_USER, NEON_DB_PASSWORD, NEON_DB_HOST, NEON_DB_PORT, NEON_DB_NAME, SQLITE_DB_PATH
from functools import lru_cache


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

# User Information Functions
async def get_user_info(session_id):
    conn = await connect_to_neon()
    try:
        # Check if user_info table exists
        table_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_info')"
        )
        
        if not table_exists:
            # Create the table if it doesn't exist
            await conn.execute("""
                CREATE TABLE user_info (
                    session_id TEXT PRIMARY KEY,
                    keyword_id INTEGER,
                    name TEXT,
                    phone TEXT,
                    template TEXT
                )
            """)
            return {}
        
        # Get user info
        row = await conn.fetchrow(
            "SELECT keyword_id, name, phone, template FROM user_info WHERE session_id = $1", 
            session_id
        )
        
        if row:
            return {
                'keyword_id': row['keyword_id'],
                'name': row['name'],
                'phone': row['phone'],
                'template': row['template']
            }
        return {}
    except Exception as e:
        logging.error(f"Error getting user info: {e}")
        return {}
    finally:
        await conn.close()

async def update_user_info(session_id, user_info):
    conn = await connect_to_neon()
    try:
        # Check if user_info table exists
        table_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_info')"
        )
        
        if not table_exists:
            # Create the table if it doesn't exist
            await conn.execute("""
                CREATE TABLE user_info (
                    session_id TEXT PRIMARY KEY,
                    keyword_id INTEGER,
                    name TEXT,
                    phone TEXT,
                    template TEXT
                )
            """)
        
        # Check if record exists
        existing = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM user_info WHERE session_id = $1)",
            session_id
        )
        
        if existing:
            # Update existing record
            await conn.execute("""
                UPDATE user_info 
                SET keyword_id = $1, name = $2, phone = $3, template = $4
                WHERE session_id = $5
            """, 
            user_info.get('keyword_id'), 
            user_info.get('name'), 
            user_info.get('phone'), 
            user_info.get('template'), 
            session_id)
        else:
            # Insert new record
            await conn.execute("""
                INSERT INTO user_info (session_id, keyword_id, name, phone, template)
                VALUES ($1, $2, $3, $4, $5)
            """, 
            session_id,
            user_info.get('keyword_id'), 
            user_info.get('name'), 
            user_info.get('phone'), 
            user_info.get('template'))
        
        # logging.info(f"User info updated for session {session_id}")
    except Exception as e:
        logging.error(f"Error updating user info: {e}")
    finally:
        await conn.close()
        
# SQLite Content Database Functions
@lru_cache(maxsize=1)  # Cache only the most recent result
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