import re
import logging
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY, LLM_MODEL

llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)
def ai_clubbed(user_query, keyword_choices, template_choices):
    # Combine prompts from the original functions to create a comprehensive batch request
    prompt = (
        f"Analyze this user query carefully: '{user_query}'\n\n"
        
        # Modified to ensure one of the provided keyword IDs is always chosen
        f"Task 1: Choose the most suitable keyword ID from this list: {', '.join(keyword_choices)}.\n"
        f"You MUST select one of the provided keyword IDs even if the match is not perfect. "
        f"Choose the best available option.\n\n"
        
        # From extract_name function
        f"Task 2: Extract the user's name from this query if provided. "
        f"Return the name as a single word or phrase (e.g., 'John') or 'Unknown' if no name is found.\n\n"
        
        # New phone extraction (similar to how name extraction was done)
        f"Task 3: Extract the user's phone number from this query if provided. "
        f"Return just the digits of the phone number or 'Unknown' if no phone number is found.\n\n"
        
        # Template selection
        f"Task 4: Choose the most suitable template out of the following options: {', '.join(template_choices)}. "
        f"If no template is appropriate, use 'Default'.\n\n"
        
        # From generate_summary function
        f"Task 5: Provide a concise two-line summary of what your response is going to be."
        f"Include a second line in this format: 'User: [name], Phone: [phone], Interested in: [product]' "
        f"where [name], [phone], and [product] are extracted from the query or 'Unknown' if not found.\n\n"
        
        f"Format your response exactly like this:\n"
        f"Keyword ID: [ID - must be 1, 2, or 3]\n"
        f"Name: [Name or Unknown]\n"
        f"Phone: [Phone or Unknown]\n"
        f"Template: [Template or Default]\n"
        f"Summary: [Summary]"
    )
    
    response = llm.invoke(prompt).content
    
    # Extract keyword ID with fallback to ID 1 if extraction fails
    keyword_match = re.search(r'Keyword ID: (\d+)', response)
    if keyword_match:
        keyword_id_str = keyword_match.group(1).strip()
        keyword_id = int(keyword_id_str) if keyword_id_str.isdigit() else 1
    else:
        keyword_id = 2  # Default to first keyword if extraction fails
    
    # Ensure keyword_id is valid (1, 2, or 3)
    if keyword_id not in [1, 2, 3]:
        keyword_id = 2
    
    # Extract name
    name_match = re.search(r'Name: (.+)', response)
    name_str = name_match.group(1).strip() if name_match else "Unknown"
    name = name_str if name_str != "Unknown" else None
    
    # Extract phone
    phone_match = re.search(r'Phone: (.+)', response)
    phone_str = phone_match.group(1).strip() if phone_match else "Unknown"
    phone = phone_str if phone_str != "Unknown" else None
    
    # Extract template
    template_match = re.search(r'Template: (.+)', response)
    template_str = template_match.group(1).strip() if template_match else "Default"
    template = template_str if template_str != "Default" else None
    
    # Extract summary
    summary_match = re.search(r'Summary: (.+)', response, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""

    logging.info(f"AI Clubbed Response: Keyword ID: {keyword_id}, Name: {name}, Phone: {phone}, Template: {template}, Summary: {summary}")
    
    return [keyword_id, name, phone, template, summary]

def generate_response(user_query, content, name=None, phone=None, template=None, chat_summary=None):
    """
    Generate a response based on user query, content, and user information
    
    Args:
        user_query (str): The user's query
        content (str): Content retrieved from the database for the matched keyword
        name (str, optional): User's name if available
        phone (str, optional): User's phone number if available
        template (str, optional): Template type to use for the response
        chat_summary (str, optional): Summary of the chat conversation so far
    
    Returns:
        str: Generated response
    """
    # Prepare name for greeting if available
    name_slot = f" {name}" if name else ""
    
    # Include chat summary in context if available
    context = ""
    if chat_summary:
        context = f"Chat history summary: {chat_summary}\n"
    
    # Basic assistant prompt
    base_prompt = (
        f"You are a friendly receptionist at R K Nature Cure Home, a naturopathy hospital. "
        f"We are asking user to provide name and number through other function, incase they reply with name or number, just say thank you and ask how can we help you. "
        f"Answer the user's question in a warm, concise tone (max 2 lines total, including greeting), using this info: '{content}'. "
        f"Keep it extremely concise and avoid technical terms. If the info isn't enough, briefly suggest contacting us. User query: '{user_query}'"

        f" Proactively list the therapies offered if the user query is about a specific health issue, and be sympathetic & conscious of the other person's pain. "
    )
    
    # Template-specific guidance based on template type
    template_guidance = {
        "Hello": "Provide a friendly greeting and welcome them to RK Nature Cure Home.",
        
        "Introduction": "Briefly introduce RK Nature Cure Home as a premier naturopathy center in Coimbatore.",
        
        "AboutUs": "Focus on our center's natural healing approach using scientifically-backed naturopathic methods.",
        
        "HealthIssueGeneral": "Acknowledge their health concerns and mention all the holistic solutions offered.",
        
        "BackPain": "Express sympathy for their back pain and mention all the different therapies offered.",
        
        "JointPain": "Acknowledge that joint pain can be debilitating and mention our mud therapy and physiotherapy.",
        
        "Stress": "Emphasize our holistic approach to stress management including meditation and pranayama.",
        
        "Diabetes": "Mention our natural approach to diabetes management with diet plans and exercises.",
        
        "Location": "Share our address: Krishna Layout, Ganapathy, Coimbatore - 641006.",
        
        "OurContactDetails": "Provide our contact number +91 88700-66622 and mention reception hours (6 AM to 8 PM).",

        "YourContactDetails": f"Provided the {name} and {phone} are already collected, just say thank you and tell them you will contact them. If not, ask for further details.",
        
        "Directions": "Offer simple directions to our facility.",
        
        "TherapyOptions": "Mention we offer personalized treatments based on specific health needs.",
        
        "OnlineServices": "Confirm we offer online consultations for dietary guidance and yoga sessions.",
        
        "Accommodation": "Mention our comfortable stay options for extended treatment programs.",
        
        "Appointment": "Offer to schedule an appointment and ask for preferred timing.",
        
        "BookingProcess": "Explain our simple booking process via phone (+91 88700-66622).",
        
        "FirstVisitInfo": "Advise them to bring medical reports and expect a 45-60 minute consultation.",
        
        "Pricing": "Mention our customized packages and flexible payment options.",
        
        "Insurance": "Explain we provide documentation for insurance reimbursement claims.",
        
        "Packages": "Briefly mention our 7-day and 14-day residential programs.",
        
        "TreatmentDuration": "Explain treatment duration varies based on condition (typically 7-14 days minimum).",
        
        "ShortStay": "Mention our weekend wellness retreats for short rejuvenation.",
        
        "Follow-up": "Emphasize the importance of follow-up care for lasting results.",
        
        "HomeRemedies": "Suggest some simple home practices that complement in-center treatments.",
        
        "YogaPrograms": "Highlight our therapeutic yoga programs for various conditions.",
        
        "Diet": "Stress the importance of nutrition in healing and our personalized meal plans.",
        
        "DietaryGuidance": "Mention our approach combining ancient wisdom with modern nutritional science.",
        
        "DetoxPrograms": "Describe our detox programs for eliminating toxins and system rejuvenation.",
        
        "SafetyProtocols": "Reassure about our strict hygiene protocols and certified professionals.",
        
        "Covid": "Explain our COVID safety measures including sanitization and distancing.",
        
        "Hours": "Share our opening hours (6 AM to 8 PM) and treatment/consultation timings.",
        
        "Doctors": "Mention our team of experienced naturopaths and wellness specialists.",
        
        "Consultation": "Describe our comprehensive consultations and offer online/in-person options.",
        
        "FirstVisit": "Explain what to expect during their first visit and assessment.",
        
        "Wellness": "Mention our five pillars approach: diet, exercise, stress management, rest, and positive thinking.",
        
        "Treatment": "Emphasize our natural, non-invasive treatment approach.",
        
        "Emergency": "Provide emergency contact information (+91 88700-66622) and mention medical team availability.",
        
        "Testimonials": "Mention patient success stories and improvements.",
        
        "General": "Provide a general helpful response and ask how else we can assist."
    }
    
    # Default to General if template not provided or invalid
    if not template or template not in template_guidance:
        template = "General"
    
    # Create the final prompt with template-specific guidance
    assistant_prompt = f"{base_prompt}\n\nSpecific guidance: {template_guidance[template]}"
    
    # In a real implementation, you would send this prompt to the AI service
    
    response = llm.invoke(assistant_prompt).content
    
    return response  