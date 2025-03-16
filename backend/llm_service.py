import re
import logging
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
    # Prepare name for greeting
    name_slot = f" {name}" if name else ""
    
    # Define templates for various user queries and intents
    templates = {
        # Basic greeting templates
        "Hello": "Hello{name_slot}! Welcome to RK Nature Cure Home. How can we assist you with your wellness journey today? {content}",
        
        "Introduction": "Greetings{name_slot}! RK Nature Cure Home is a premier naturopathy center in Coimbatore. {content} Would you like to know more about our healing approach?",
        
        "AboutUs": "Welcome to RK Nature Cure Home{name_slot}! {content} Our center focuses on natural healing through scientifically-backed naturopathic methods.",
        
        # Health concern templates
        "HealthIssueGeneral": "We understand your health concerns{name_slot}. {content} At RK Nature Cure, we offer holistic solutions to address both symptoms and root causes.",
        
        "BackPain": "I'm sorry to hear about your back pain{name_slot}. {content} Our specialized treatments including hydrotherapy, therapeutic massage, and yoga have helped many find relief. Would you like to know more?",
        
        "JointPain": "Joint pain can be quite debilitating{name_slot}. {content} Our mud therapy, physiotherapy sessions, and specialized exercises are designed to provide relief and improve mobility.",
        
        "Stress": "Dealing with stress requires a holistic approach{name_slot}. {content} Our stress management programs combine meditation, pranayama, and natural therapies to restore balance.",
        
        "Diabetes": "For managing diabetes naturally{name_slot}, {content} our approach includes customized diet plans, therapeutic exercises, and specialized naturopathic treatments.",
        
        # Location and contact templates
        "Location": "You can find us at Krishna Layout, Ganapathy, Coimbatore - 641006{name_slot}. {content} We're conveniently located with ample parking facilities.",
        
        "ContactInfo": "You can reach us at +91 88700-66622{name_slot}. {content} Our reception is open from 6 AM to 8 PM daily to answer your queries.",
        
        "Directions": "Here's how to reach RK Nature Cure Home{name_slot}: {content} If you need more specific directions, please let us know your starting point.",
        
        # Service inquiry templates
        "TherapyOptions": "We offer a wide range of therapies{name_slot}. {content} Our treatments are personalized based on your specific health needs and constitution.",
        
        "OnlineServices": "Yes{name_slot}, we do offer online consultations! {content} Many of our dietary guidance and yoga sessions can be conducted virtually. Would you like to book an online appointment?",
        
        "Accommodation": "Regarding accommodation{name_slot}, {content} we offer comfortable stay options for patients undergoing extended treatment programs. Would you like details about our room types?",
        
        # Appointment and booking templates
        "Appointment": "We'd be happy to schedule an appointment for you{name_slot}. {content} Would you prefer a morning or evening slot?",
        
        "BookingProcess": "Booking a consultation is simple{name_slot}. {content} You can call us at +91 88700-66622 or reply with your preferred date and time, and we'll check availability.",
        
        "FirstVisitInfo": "For your first visit{name_slot}, {content} please bring any recent medical reports you have. Your initial consultation will take about 45-60 minutes.",
        
        # Pricing and payment templates
        "Pricing": "Regarding our pricing{name_slot}, {content} our treatment packages are customized based on your needs. We offer flexible payment options including card payments and installments.",
        
        "Insurance": "About insurance{name_slot}, {content} we provide detailed receipts and documentation that can be submitted for reimbursement to insurance providers that cover alternative treatments.",
        
        "Packages": "Our wellness packages{name_slot} are designed for comprehensive care. {content} Would you like information about our popular 7-day or 14-day residential programs?",
        
        # Treatment duration templates
        "TreatmentDuration": "The duration of treatment{name_slot} varies based on your condition. {content} Typically, we recommend a minimum of 7-14 days for noticeable improvement in chronic conditions.",
        
        "ShortStay": "If you're looking for a short rejuvenation program{name_slot}, {content} our weekend wellness retreats might be perfect for you. These focus on stress relief and energy restoration.",
        
        # Follow-up templates
        "FollowUp": "Follow-up care is essential for lasting results{name_slot}. {content} We recommend periodic check-ins to adjust your treatment plan as you progress.",
        
        "HomeRemedies": "Here are some home-based practices you can follow{name_slot}: {content} These complement your in-center treatments and accelerate your healing process.",
        
        # Specialty templates
        "YogaPrograms": "Our yoga programs{name_slot} are designed for therapeutic benefits. {content} We offer both group and individual sessions tailored to your physical condition.",
        
        "DietaryGuidance": "Nutrition plays a crucial role in healing{name_slot}. {content} Our dietary experts create personalized meal plans based on your body constitution and health goals.",
        
        "DetoxPrograms": "Our specialized detox programs{name_slot} help eliminate toxins and rejuvenate your system. {content} These are particularly beneficial for those with chronic conditions or lifestyle disorders.",
        
        # Reassurance templates
        "SafetyProtocols": "Your safety is our priority{name_slot}. {content} We follow strict hygiene protocols and all our therapists are certified professionals.",
        
        "CovidMeasures": "Regarding COVID safety{name_slot}, {content} we maintain thorough sanitization, temperature checks, and appropriate distancing during all treatments.",
        
        # Fallback templates
        "General": "Hello{name_slot}! {content} How else can we assist you with your wellness needs?",
        
        "Emergency": "For emergencies{name_slot}, please call us immediately at +91 88700-66622. {content} Our medical team is available to provide guidance.",
        
        "Testimonials": "Our patients have experienced remarkable improvements{name_slot}. {content} Would you like to hear some success stories related to your condition?"
    }
    
    # Default to General if template not provided or invalid
    if not template or template not in templates:
        template = "General"
    
    # Format response using the selected template
    response = templates[template].format(name_slot=name_slot, content=content)
    
    return response