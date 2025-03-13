import streamlit as st
import asyncio
import pandas as pd

from sqlite_db import init_sqlite_db, get_existing_session_ids, update_sqlite_with_sessions, display_sqlite_data
from neon_db import fetch_neon_sessions
from info_extractor import extract_user_info_llm

async def sync_data():
    init_sqlite_db()
    existing_session_ids = get_existing_session_ids()
    neon_sessions = await fetch_neon_sessions()
    
    new_sessions = [session for session in neon_sessions if session['session_id'] not in existing_session_ids]
    
    if new_sessions:
        update_sqlite_with_sessions(new_sessions, extract_user_info_llm)
        
    return len(new_sessions)

def main():
    st.title("RK Nature Dashboard")
    
    init_sqlite_db()
    
    if st.button("Refresh Data"):
        with st.spinner("Syncing data from Neon DB to SQLite..."):
            new_sessions_count = asyncio.run(sync_data())
            if new_sessions_count > 0:
                st.success(f"✅ Synced {new_sessions_count} new sessions!")
            else:
                st.info("No new sessions to sync.")
    
    st.subheader("Total Number of Chats")
    df = display_sqlite_data()
    
    st.write(f"Total Sessions: {len(df)}")
    
    st.subheader("Filter Options")
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        name_filter = st.text_input("Filter by Name")
        
    with filter_col2:
        product_filter = st.text_input("Filter by Product Interest")
    
    filtered_df = df
    if name_filter:
        filtered_df = filtered_df[filtered_df['Name'].str.contains(name_filter, case=False, na=False)]
    if product_filter:
        filtered_df = filtered_df[filtered_df['Product'].str.contains(product_filter, case=False, na=False)]
    
    st.dataframe(filtered_df)
    
    if st.button("Export to CSV"):
        filtered_df.to_csv("chat_sessions_export.csv", index=False)
        st.success("Data exported to chat_sessions_export.csv!")

if __name__ == "__main__":
    main()