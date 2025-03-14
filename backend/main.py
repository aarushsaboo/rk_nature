import asyncio
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import DEBUG, HOST, PORT
from database import log_chat, update_summary, get_chat_data, get_content_by_id
from llm_service import batch_process_queries, match_query_to_keyword, extract_name, generate_response_with_batch, generate_summary

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
        batch_results = await batch_process_queries(user_query)
        
        # Get matched keyword ID and content
        matched_id = batch_results.get("keyword_id")
        
        # Fallback to original method if batch processing fails
        if matched_id is None:
            matched_id = match_query_to_keyword(user_query)
            
        content = get_content_by_id(matched_id) if matched_id else ""
        
        # Generate response using batch results to avoid duplicate LLM calls
        response = await generate_response_with_batch(user_query, content, batch_results)
        
        # Log the conversation
        new_log_entry = f"User: {user_query} | Bot: {response}"
        await log_chat(session_id, new_log_entry)
        
        # Generate and update summary (using original method)
        summary = generate_summary(existing_summary, new_log_entry)
        await update_summary(session_id, summary)
        
        # Add prompts for missing information
        final_answer = response
        
        if "User: Unknown" in summary and "Phone: Unknown" in summary:
            final_answer += "\n\nCan you share your name and number to help us better?"
        elif "User: Unknown" in summary:
            final_answer += "\n\nCan you share your name to help us better?"
        elif "Phone: Unknown" in summary:
            final_answer += "\n\nCan you share your number to help us better?"
        
        return jsonify({"response": final_answer, "SessionId": session_id})
        
    except Exception as e:
        logging.error(f"Error processing query: {e}", exc_info=True)
        return jsonify({
            "response": "I'm experiencing technical difficulties. Please try again later or call R K Nature Cure Home directly.", 
            "SessionId": session_id
        })

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)