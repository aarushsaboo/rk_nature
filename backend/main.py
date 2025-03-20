import asyncio
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import DEBUG, HOST, PORT
from database import log_chat, update_summary, get_chat_data, get_content_by_id, update_user_info
from llm_service import ai_clubbed
from database import fetch_keywords_data, get_user_info

# Set up logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

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
    
    # logging.info(f"Received SessionId: {session_id} for query: {user_query}")
    
    return asyncio.run(process_query(session_id, user_query))

async def process_query(session_id, user_query):
    # Fetch existing user info from database (if any)
    existing_info = await get_user_info(session_id)
    existing_name = existing_info.get('name')
    existing_phone = existing_info.get('phone')
    
    # Fetch all content data for sending to AI model
    data_dict = fetch_keywords_data()
    bulk_content = {id: info['content'] for id, info in data_dict.items()}
    
    # Get existing summary if available
    existing_summary = await get_chat_data(session_id)
    
    # Call the AI function with all content
    new_name, new_phone, summary, response = ai_clubbed(
        user_query, 
        bulk_content, 
        # template_options, 
        existing_summary,
        existing_name,
        existing_phone
    )

    # Use existing values if new ones aren't found
    name = new_name if new_name is not None else existing_name
    phone = new_phone if new_phone is not None else existing_phone

    logging.info(f"Name: {name}, Phone number: {phone}")
    
    # Store or update user info in database
    new_user_info = {
        'name': name,
        'phone': phone
    }
    await update_user_info(session_id, new_user_info)
    
    # Update chat summary
    await update_summary(session_id, summary)
    
    # Log the conversation
    new_log_entry = f"User: {user_query} | Bot: {response}"
    await log_chat(session_id, new_log_entry)
    
    # Add prompts for missing information if needed
    final_answer = response
    
    # Only ask for missing info if we haven't stored it already
    if name is None and phone is None:
        final_answer += "\n\nCan you share your name and number to help us better?"
    elif name is None:
        final_answer += "\n\nCan you share your name to help us better?"
    elif phone is None:
        final_answer += "\n\nCan you share your number to help us better?"
    
    response_data = {
        "response": final_answer, 
        "SessionId": session_id,
        "name": name,
        "phone": phone
    }
    logging.info(f"Response to the user: {response_data}")
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)