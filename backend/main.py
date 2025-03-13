import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from llama_index.llms.openai import OpenAI  # Changed from Groq
import logging
import re
from dotenv import load_dotenv
import asyncpg
import asyncio
import sqlite3

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set up the OpenAI LLM with gpt-4o-mini
api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAI(model="gpt-3.5-turbo", api_key=api_key)  # Changed to OpenAI

# Neon DB connection parameters
NEON_DB_USER = os.getenv("NEON_DB_USER")
NEON_DB_PASSWORD = os.getenv("NEON_DB_PASSWORD")
NEON_DB_HOST = os.getenv("NEON_DB_HOST")
NEON_DB_PORT = os.getenv("NEON_DB_PORT")
NEON_DB_NAME = os.getenv("NEON_DB_NAME")

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

# Function to log chat and update summary
async def log_chat_and_update_summary(session_id, new_log_entry, user_query):
    conn = await connect_to_neon()
    try:
        existing_row = await conn.fetchrow(
            "SELECT log, summary FROM chat_logs WHERE session_id = $1", session_id
        )
        
        existing_log = None
        existing_summary = None
        
        if existing_row:
            existing_log = existing_row['log']
            existing_summary = existing_row['summary']
            updated_log = f"{existing_log} | {new_log_entry}"
            await conn.execute(
                "UPDATE chat_logs SET log = $1 WHERE session_id = $2",
                updated_log, session_id
            )
        else:
            updated_log = new_log_entry
            await conn.execute(
                "INSERT INTO chat_logs (session_id, log, summary) VALUES ($1, $2, $3)",
                session_id, new_log_entry, ""
            )

        prompt = ""
        if existing_summary:
            prompt = (
                f"Previous summary: '{existing_summary}'. "
                f"New chat entry: '{new_log_entry}'. "
                f"Update the previous summary to include any new information about the user. "
                f"If new information conflicts with old information, use the new information. "
                f"Provide a concise two-line summary of what has happened so far. "
                f"Include a second line in this format: 'User: [name], Phone: [phone], Interested in: [product]' "
                f"where [name], [phone], and [product] are extracted from both the previous summary and new chat. "
                f"Use 'Unknown' only if the information is still not available."
            )
        else:
            prompt = (
                f"Based on this chat log: '{new_log_entry}', provide a concise two-line summary of what has happened so far. "
                f"Include a second line in this format: 'User: [name], Phone: [phone], Interested in: [product]' "
                f"where [name], [phone], and [product] are extracted from the log or 'Unknown' if not found."
            )
            
        summary_response = llm.complete(prompt).text.strip()
        logging.info(f"Generated summary: {summary_response}")

        await conn.execute(
            "UPDATE chat_logs SET summary = $1 WHERE session_id = $2",
            summary_response, session_id
        )

        return summary_response
    finally:
        await conn.close()

# Function to fetch keywords, their IDs, and associated content from the database
def fetch_data():
    conn = sqlite3.connect('extracted_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, keywords, content FROM extracted_data")
    records = cursor.fetchall()
    conn.close()
    logging.info("Fetched data from database")
    return {record[0]: {"keyword": record[1], "content": record[2]} for record in records}

# Function to match user query with available keywords using LLM
def match_query_to_keyword(query):
    data_dict = fetch_data()
    keyword_options = [f"ID: {id} - Keyword: {info['keyword']}" for id, info in data_dict.items()]
    prompt = f"Based on the following user query, choose the most suitable keyword ID from this list: {', '.join(keyword_options)}. User query: {query}"
    response = llm.complete(prompt).text.strip()
    match = re.search(r'ID: (\d+)', response)
    return int(match.group(1)) if match and int(match.group(1)) in data_dict else None

# Function to get content for a given keyword
def get_content_for_keyword(id):
    data_dict = fetch_data()
    return data_dict.get(id, {}).get("content", "")

# Function to extract name from query using LLM
def extract_name_from_query(query):
    prompt = (
        f"Extract the user's name from this query if provided: '{query}'. "
        f"Return the name as a single word or phrase (e.g., 'John') or 'Unknown' if no name is found."
    )
    response = llm.complete(prompt).text.strip()
    return response if response != "Unknown" else None

# Function to generate a response
def generate_representative_response(query, content, name=None):
    greeting = f"Hi {name}!" if name and name != "Unknown" else "Hello!"
    
    prompt = (
        f"You are a friendly receptionist at R K Nature Cure Home, a naturopathy hospital. "
        f"We are asking user to provide name and number through other function, incase they reply with name or number, just say thank you and ask how can we help you"
        f"Answer the user's question in a warm, concise tone (max 2 lines total, including greeting), using this info: '{content}'. "
        f"Keep it extremely concise and avoid technical terms. If the info isn't enough, briefly suggest contacting us. User query: '{query}'"
    )
    try:
        response = llm.complete(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return f"{greeting} Oops, something went wrong! Please call R K Nature Cure Home for help."

# API endpoint for chatbot widget
@app.route('/submit_query', methods=['POST'])
def submit_query():
    data = request.get_json()
    user_query = data.get('Query') if data else None
    session_id = data.get('SessionId') if data else None
    
    if not user_query:
        return jsonify({"error": "Missing Query!"}), 400
    if not session_id:
        return jsonify({"error": "Missing SessionId!"}), 400
    
    logging.info(f"Received SessionId: {session_id} for query: {user_query}")
    
    new_log_entry = f"User: {user_query}"

    name = extract_name_from_query(user_query)

    matched_id = match_query_to_keyword(user_query)
    content = get_content_for_keyword(matched_id) if matched_id else ""
    initial_answer = generate_representative_response(user_query, content, name)
    
    new_log_entry += f" | Bot: {initial_answer}"
    
    summary = asyncio.run(log_chat_and_update_summary(session_id, new_log_entry, user_query))
    
    final_answer = initial_answer
    
    missing_info_prompt = ""
    if "User: Unknown" in summary and "Phone: Unknown" in summary:
        missing_info_prompt = "\n\nCan you share your name and number to help us better?"
    elif "User: Unknown" in summary:
        missing_info_prompt = "\n\nCan you share your name to help us better?"
    elif "Phone: Unknown" in summary:
        missing_info_prompt = "\n\nCan you share your number to help us better?"
    
    if missing_info_prompt:
        final_answer += missing_info_prompt
    
    return jsonify({"response": final_answer, "SessionId": session_id})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
