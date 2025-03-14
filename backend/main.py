import asyncio
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import DEBUG, HOST, PORT
from database import log_chat, update_summary, get_chat_data, get_content_by_id
from llm_service import process_query_batch, generate_response_and_summary

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

@app.route('/submit_query', methods=['POST'])
def submit_query():
    data = request.get_json()
    user_query = data.get('Query')
    session_id = data.get('SessionId')
    
    # Validate inputs
    if not user_query:
        return jsonify({"error": "Missing Query!"}), 400
    if not session_id:
        return jsonify({"error": "Missing SessionId!"}), 400
    
    logging.info(f"Received SessionId: {session_id} for query: {user_query}")
    
    # Core processing logic
    return asyncio.run(process_query(session_id, user_query))

async def process_query(session_id, user_query):
    try:
        # Get existing chat data first to avoid delays later
        chat_data = await get_chat_data(session_id)
        existing_summary = chat_data['summary'] if chat_data and 'summary' in chat_data else None
        
        # Process the query in a batch to reduce LLM calls
        analysis_results = await process_query_batch(user_query)
        
        # Get content based on matched keyword
        matched_id = analysis_results["keyword_id"]
        content = get_content_by_id(matched_id) if matched_id else ""
        
        # Generate response and summary in a single call
        result = await generate_response_and_summary(
            user_query, 
            analysis_results, 
            content, 
            session_id, 
            existing_summary
        )
        
        # Log the conversation
        new_log_entry = f"User: {user_query} | Bot: {result['response']}"
        await log_chat(session_id, new_log_entry)
        
        # Update summary
        await update_summary(session_id, result['summary'])
        
        return jsonify({"response": result['response'], "SessionId": session_id})
        
    except Exception as e:
        logging.error(f"Error processing query: {e}", exc_info=True)
        return jsonify({
            "response": "I'm experiencing technical difficulties. Please try again later or call R K Nature Cure Home directly.", 
            "SessionId": session_id
        })

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)