import re
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY, LLM_MODEL
from prompt_builder import build_prompt

# Initialize LLM
llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)

async def process_user_query(user_query, bulk_content, chat_summary=None, name=None, phone=None):
    """
    Process user query and generate all needed data in a single API call
    
    Args:
        user_query (str): The user's query
        bulk_content (dict): Dictionary of all content with ID as key
        chat_summary (str, optional): Summary of the chat conversation so far
        name (str, optional): User's name if known
        phone (str, optional): User's phone if known
    
    Returns:
        tuple: (name, phone, summary, response)
    """
    # Get available templates
    template_choices = [
        "Hello", "Introduction", "AboutUs", "HealthIssueGeneral",
        "BackPain", "JointPain", "Stress", "Diabetes", "Location", 
        "OurContactDetails", "Directions", "TherapyOptions", "OnlineServices", 
        "Accommodation", "Appointment", "BookingProcess", "FirstVisitInfo", 
        "Pricing", "Insurance", "Packages", "TreatmentDuration", "ShortStay",
        "Follow-up", "HomeRemedies", "YogaPrograms", "Diet", "DietaryGuidance", 
        "DetoxPrograms", "SafetyProtocols", "Covid", "Hours", "Doctors", 
        "Consultation", "FirstVisit", "Wellness", "Treatment", "Emergency", 
        "Testimonials", "General", "Unknown"
    ]
    
    # Build prompt
    prompt = build_prompt(user_query, bulk_content, template_choices, chat_summary, name, phone)
    
    # Log prompt for debugging
    logging.debug(f"Prompt sent to LLM: {prompt}")
    
    # Make the API call
    ai_response = llm.invoke(prompt).content
    
    # Log response for debugging
    logging.debug(f"Raw LLM response: {ai_response}")
    
    # Extract all components
    name_match = re.search(r'Name: (.+)', ai_response)
    name_str = name_match.group(1).strip() if name_match else "Unknown"
    name = name_str if name_str != "Unknown" else None
    
    phone_match = re.search(r'Phone: (.+)', ai_response)
    phone_str = phone_match.group(1).strip() if phone_match else "Unknown"
    phone = phone_str if phone_str != "Unknown" else None
    
    template_match = re.search(r'Template: (.+)', ai_response)
    template_str = template_match.group(1).strip() if template_match else "General"
    
    summary_match = re.search(r'Summary: (.+?)(?=Response:|$)', ai_response, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""
    
    response_match = re.search(r'Response: (.+)', ai_response, re.DOTALL)
    response = response_match.group(1).strip() if response_match else "I'm here to help you with information about RK Nature Cure Home. How can I assist you today?"
    
    logging.info(f"Processed response - Name: {name}, Phone: {phone}, Template: {template_str}, Summary {summary}, Response length: {len(response)}")
    
    return name, phone, summary, response