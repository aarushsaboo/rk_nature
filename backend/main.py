import asyncio
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import DEBUG, HOST, PORT
from database import log_chat, update_summary, get_chat_data, get_content_by_id
from llm_service import match_query_to_keyword, extract_name, generate_response, generate_summary

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

@app.route('/submit_query', methods=['POST'])
def submit_query():
    data = request.get_json()
    user_query = data.get('Query')
    session_id = data.get('SessionId')
    
    if not user_query:
        return jsonify({"error": "Missing Query!"}), 400
    if not session_id:
        return jsonify({"error": "Missing SessionId!"}), 400
    
    logging.info(f"Received SessionId: {session_id} for query: {user_query}")
    
    return asyncio.run(process_query(session_id, user_query))

async def process_query(session_id, user_query):
    name = extract_name(user_query)  # ai call
    matched_id = match_query_to_keyword(user_query) #ai call

    content = get_content_by_id(matched_id) if matched_id else ""
    initial_answer = generate_response(user_query, content, name)
    new_log_entry = f"User: {user_query} | Bot: {initial_answer}"
    await log_chat(session_id, new_log_entry)

    chat_data = await get_chat_data(session_id)
    existing_summary = chat_data['summary'] if chat_data else None

    summary = generate_summary(existing_summary, new_log_entry) #ai call
    await update_summary(session_id, summary)
    final_answer = initial_answer
    
    if "User: Unknown" in summary and "Phone: Unknown" in summary:
        final_answer += "\n\nCan you share your name and number to help us better?"
    elif "User: Unknown" in summary:
        final_answer += "\n\nCan you share your name to help us better?"
    elif "Phone: Unknown" in summary:
        final_answer += "\n\nCan you share your number to help us better?"
    
    return jsonify({"response": final_answer, "SessionId": session_id})

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)