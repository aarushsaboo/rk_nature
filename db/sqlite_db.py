import sqlite3
import pandas as pd
from config import SQLITE_DB_FILE

def init_sqlite_db():
    conn = sqlite3.connect(SQLITE_DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_sessions (
        session_id TEXT PRIMARY KEY,
        log TEXT,
        summary TEXT,
        name TEXT,
        phone TEXT,
        product TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    return conn

def get_existing_session_ids():
    conn = sqlite3.connect(SQLITE_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id FROM chat_sessions")
    session_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return session_ids

def update_sqlite_with_sessions(sessions, extract_user_info_func):
    conn = sqlite3.connect(SQLITE_DB_FILE)
    cursor = conn.cursor()
    
    for session in sessions:
        session_id = session['session_id']
        log = session['log']
        summary = session['summary']
        
        name, phone, product = extract_user_info_func(summary)
        
        cursor.execute('''
        INSERT OR REPLACE INTO chat_sessions 
        (session_id, log, summary, name, phone, product, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (session_id, log, summary, name, phone, product))
    
    conn.commit()
    conn.close()

def display_sqlite_data():
    conn = sqlite3.connect(SQLITE_DB_FILE)
    df = pd.read_sql_query("""
        SELECT name AS Name, 
               phone AS Number, 
               product AS Product, 
               summary AS Summary, 
               log AS Log 
        FROM chat_sessions
    """, conn)
    conn.close()
    return df