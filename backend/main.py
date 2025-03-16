import asyncio
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import DEBUG, HOST, PORT
from database import log_chat, update_summary, get_chat_data, get_content_by_id, update_user_info
from llm_service import generate_response, ai_clubbed
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
    
    logging.info(f"Received SessionId: {session_id} for query: {user_query}")
    
    return asyncio.run(process_query(session_id, user_query))

async def process_query(session_id, user_query):
    # Fetch existing user info from database (if any)
    existing_info = await get_user_info(session_id)
    existing_keyword_id = existing_info.get('keyword_id')
    existing_name = existing_info.get('name')
    existing_phone = existing_info.get('phone')
    existing_template = existing_info.get('template')
    
    # Fetch keyword options for AI prompt
    data_dict = fetch_keywords_data()
    keyword_options = [f"ID: {id} - Keyword: {info['keyword']}" for id, info in data_dict.items()]
    # 'ID: 1 - Keyword: Information about company RK Nature Cure Home, its founders, vision, mission etc', 'ID: 2 - Keyword: Select this for information about the Treatments , Therapies and Facilities provided by RK Nature ', 'ID: 3 - Keyword: Select this for information about the details related to accomodation, rates, charges, price of different services at RK Nature'
    
    # Define template options
    template_options = [
    "General", "Hello", "Introduction", "AboutUs", 
    "Appointment", "BookingProcess", "FirstVisitInfo", 
    "Treatment", "TherapyOptions", "BackPain", "JointPain", "Stress", "Diabetes", 
    "Pricing", "Packages", "Insurance",
    "Location", "ContactInfo", "Directions", 
    "Hours", "OnlineServices", "Accommodation",
    "Wellness", "YogaPrograms", "DetoxPrograms", 
    "FirstVisit", 
    "Diet", "DietaryGuidance", 
    "Covid", "SafetyProtocols", 
    "Emergency", 
    "Testimonials", 
    "Doctors", 
    "Consultation", 
    "Follow-up", "HomeRemedies", 
    "TreatmentDuration", "ShortStay",
    "HealthIssueGeneral"
]
    
    # Call the combined AI function
    keyword_id, name, phone, template, summary = ai_clubbed(user_query, keyword_options, template_options)
    
    # Use existing values if new ones aren't found
    keyword_id = keyword_id if keyword_id is not None else existing_keyword_id
    name = name if name is not None else existing_name
    phone = phone if phone is not None else existing_phone
    template = template if template is not None else (existing_template or "General")
    
    # Store or update user info in database
    new_user_info = {
        'keyword_id': keyword_id,
        'name': name,
        'phone': phone,
        'template': template
    }
    await update_user_info(session_id, new_user_info)
    
    # Get content based on matched keyword
    content = get_content_by_id(keyword_id) if keyword_id else ""
    
    # Update chat summary
    await update_summary(session_id, summary)
    
    # Generate response - pass new_summary to generate_response
    answer = generate_response(user_query, content, name, template, summary)
    
    # Log the conversation
    new_log_entry = f"User: {user_query} | Bot: {answer}"
    await log_chat(session_id, new_log_entry)
    
    # Get chat history
    chat_data = await get_chat_data(session_id)
    
    # Add prompts for missing information if needed
    final_answer = answer
    
    # Only ask for missing info if we haven't stored it already
    # if name is None and phone is None:
    #     final_answer += "\n\nCan you share your name and number to help us better?"
    # elif name is None:
    #     final_answer += "\n\nCan you share your name to help us better?"
    # elif phone is None:
    #     final_answer += "\n\nCan you share your number to help us better?"
    
    response_data = {
    "response": final_answer, 
    "SessionId": session_id,
    "name": name,
    "phone": phone,
    "keyword_id": keyword_id,
    "template": template
    }
    logging.info(f"Sending response: {response_data}")
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)