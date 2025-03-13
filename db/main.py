import streamlit as st
import asyncio
import asyncpg
import sqlite3
import pandas as pd
import os
import re
import json
from dotenv import load_dotenv
from llama_index.llms.groq import Groq

# Load environment variables
load_dotenv()

# Neon DB connection parameters
NEON_DB_USER = os.getenv("NEON_DB_USER")
NEON_DB_PASSWORD = os.getenv("NEON_DB_PASSWORD")
NEON_DB_HOST = os.getenv("NEON_DB_HOST")
NEON_DB_PORT = os.getenv("NEON_DB_PORT")
NEON_DB_NAME = os.getenv("NEON_DB_NAME")

# Groq API key for LLM
API_KEY = os.getenv("API_KEY")
llm = Groq(model="llama3-70b-8192", api_key=API_KEY)

# SQLite database file
SQLITE_DB_FILE = "chat_sessions.db"

# Function to connect to Neon DB
async def connect_to_neon():
    conn = await asyncpg.connect(
        user=NEON_DB_USER,
        password=NEON_DB_PASSWORD,
        database=NEON_DB_NAME,
        host=NEON_DB_HOST,
        port=NEON_DB_PORT
    )
    return conn

# Function to initialize SQLite database
def init_sqlite_db():
    conn = sqlite3.connect(SQLITE_DB_FILE)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
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

# Function to extract user info from summary using LLM
def extract_user_info_llm(summary):
    prompt = f"""
    Extract the following information from this summary:
    1. User's name
    2. User's phone number
    3. What product or service the user is interested in

    Summary: "{summary}"

    Format your response as a valid JSON with these keys: "name", "phone", "product"
    If any information is not available, use "Unknown" as the value.
    
    Example output:
    {{
        "name": "John Doe",
        "phone": "1234567890",
        "product": "Massage therapy"
    }}
    """
    
    try:
        response = llm.complete(prompt).text.strip()
        # Extract the JSON part if there's any extra text
        json_match = re.search(r'({.*})', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            data = json.loads(json_str)
            return data.get("name", "Unknown"), data.get("phone", "Unknown"), data.get("product", "Unknown")
        else:
            # Fallback to old method if LLM doesn't return valid JSON
            return extract_user_info_regex(summary)
    except Exception as e:
        st.error(f"Error extracting info using LLM: {e}")
        # Fallback to regex extraction in case of error
        return extract_user_info_regex(summary)

# Fallback regex extraction function
def extract_user_info_regex(summary):
    # Default values
    name = "Unknown"
    phone = "Unknown"
    product = "Unknown"
    
    # Extract name
    name_match = re.search(r'User: ([^,]+)', summary)
    if name_match and name_match.group(1).strip() != "Unknown":
        name = name_match.group(1).strip()
        
    # Extract phone
    phone_match = re.search(r'Phone: ([^,]+)', summary)
    if phone_match and phone_match.group(1).strip() != "Unknown":
        phone = phone_match.group(1).strip()
        
    # Extract product - make this more flexible
    product_match = re.search(r'Interested in: (.+?)(?:\.|\n|$)', summary)
    if product_match and product_match.group(1).strip() != "Unknown":
        product = product_match.group(1).strip()
    
    return name, phone, product

# Function to fetch sessions from Neon DB
async def fetch_neon_sessions():
    conn = await connect_to_neon()
    try:
        rows = await conn.fetch("SELECT session_id, log, summary FROM chat_logs")
        return [dict(row) for row in rows]
    finally:
        await conn.close()

# Function to get existing session IDs from SQLite
def get_existing_session_ids():
    conn = sqlite3.connect(SQLITE_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id FROM chat_sessions")
    session_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return session_ids

# Function to update SQLite with new sessions
def update_sqlite_with_sessions(sessions):
    conn = sqlite3.connect(SQLITE_DB_FILE)
    cursor = conn.cursor()
    
    for session in sessions:
        session_id = session['session_id']
        log = session['log']
        summary = session['summary']
        
        # Extract user info from summary using LLM
        name, phone, product = extract_user_info_llm(summary)
        
        # Insert or update the session in SQLite
        cursor.execute('''
        INSERT OR REPLACE INTO chat_sessions 
        (session_id, log, summary, name, phone, product, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (session_id, log, summary, name, phone, product))
    
    conn.commit()
    conn.close()

# Function to sync data between Neon and SQLite
async def sync_data():
    # Initialize SQLite DB
    init_sqlite_db()
    
    # Get existing session IDs from SQLite
    existing_session_ids = get_existing_session_ids()
    
    # Fetch all sessions from Neon DB
    neon_sessions = await fetch_neon_sessions()
    
    # Filter out new sessions
    new_sessions = [session for session in neon_sessions if session['session_id'] not in existing_session_ids]
    
    # Update SQLite with new sessions
    if new_sessions:
        update_sqlite_with_sessions(new_sessions)
        
    return len(new_sessions)

# Function to display data from SQLite
def display_sqlite_data():
    conn = sqlite3.connect(SQLITE_DB_FILE)
    # Select specific columns in desired order
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

# Streamlit App
st.title("RK Nature Dashboard")

# Initialize SQLite DB
init_sqlite_db()

# Add a refresh button at the top
if st.button("Refresh Data"):
    with st.spinner("Syncing data from Neon DB to SQLite..."):
        new_sessions_count = asyncio.run(sync_data())
        if new_sessions_count > 0:
            st.success(f"✅ Synced {new_sessions_count} new sessions!")
        else:
            st.info("No new sessions to sync.")

# Display current data
st.subheader("Total Number of Chats")
df = display_sqlite_data()

# Display count of sessions
st.write(f"Total Sessions: {len(df)}")

# Add filter options
st.subheader("Filter Options")
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    name_filter = st.text_input("Filter by Name")
    
with filter_col2:
    product_filter = st.text_input("Filter by Product Interest")

# Apply filters
filtered_df = df
if name_filter:
    filtered_df = filtered_df[filtered_df['Name'].str.contains(name_filter, case=False, na=False)]
if product_filter:
    filtered_df = filtered_df[filtered_df['Product'].str.contains(product_filter, case=False, na=False)]

# Display filtered data
st.dataframe(filtered_df)

# Export option
if st.button("Export to CSV"):
    filtered_df.to_csv("chat_sessions_export.csv", index=False)
    st.success("Data exported to chat_sessions_export.csv!")
