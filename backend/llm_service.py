import re
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY, LLM_MODEL

llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)

def ai_clubbed(user_query, keyword_choices, template_choices):
    # Combine prompts from the original functions to create a comprehensive batch request
    prompt = (
        f"Analyze this user query carefully: '{user_query}'\n\n"
        
        # From match_query_to_keyword function
        f"Task 1: Based on the following user query, choose the most suitable keyword ID from this list: {', '.join(keyword_choices)}.\n"
        f"If no suitable keyword ID is found, respond with 'None'.\n\n"
        
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
        f"Keyword ID: [ID or None]\n"
        f"Name: [Name or Unknown]\n"
        f"Phone: [Phone or Unknown]\n"
        f"Template: [Template or Default]\n"
        f"Summary: [Summary]"
    )
    
    response = llm.invoke(prompt).content
    
    # Extract keyword ID
    keyword_match = re.search(r'Keyword ID: (.+)', response)
    keyword_id_str = keyword_match.group(1).strip() if keyword_match else "None"
    keyword_id = int(keyword_id_str) if keyword_id_str.isdigit() else None
    
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
    
    # Check if message is only providing personal info
    if is_only_personal_info(user_query):
        return f"Hello{name_slot}! Thank you for that information. How can we help you today?"
    
    # Extract health conditions mentioned in the query and chat summary
    health_conditions = extract_health_conditions(user_query)
    
    # If we have a chat summary, use it to provide context
    if chat_summary:
        # Extract additional health conditions from the chat summary
        summary_conditions = extract_health_conditions(chat_summary)
        # Add any new conditions not already in the list
        for condition in summary_conditions:
            if condition not in health_conditions:
                health_conditions.append(condition)
    
    # Define templates
    templates = {
    "General": "Hello{name_slot}! {response_content}",
    
    "Appointment": "Hello{name_slot}! {response_content} Would you like to schedule a consultation with our experts?",
    
    "Treatment": "Hello{name_slot}! For {conditions}, we recommend {treatments}. {response_content}",
    
    "Pricing": "Hello{name_slot}! {response_content} Would you like details on our wellness packages?",
    
    "Location": "Hello{name_slot}! {response_content} Find us at Krishna Layout, Ganapathy, Coimbatore - 641006.",
    
    "Hours": "Hello{name_slot}! {response_content} We're open daily from 6 AM to 8 PM.",
    
    "Insurance": "Hello{name_slot}! {response_content} We provide detailed receipts for insurance claims.",
    
    "Wellness": "Hello{name_slot}! {response_content} Our holistic approach addresses both symptoms and root causes.",
    
    "FirstVisit": "Hello{name_slot}! {response_content} Your first visit includes a thorough assessment and personalized plan.",
    
    "Diet": "Hello{name_slot}! {response_content} Nutrition is central to our healing approach. Would you like dietary guidance?",
    
    "Covid": "Hello{name_slot}! {response_content} We follow all safety protocols for your wellbeing.",
    
    "Emergency": "Hello{name_slot}! For emergencies, please call us at +91 88700-66622 right away.",
    
    "Testimonials": "Hello{name_slot}! {response_content} Our success stories reflect our commitment to natural healing.",
    
    "Doctors": "Hello{name_slot}! {response_content} Our certified naturopaths have years of specialized training.",
    
    "Consultation": "Hello{name_slot}! {response_content} Would you prefer an online or in-person consultation?",
    
    "Follow-up": "Hello{name_slot}! {response_content} We recommend regular follow-ups for optimal results."
    }
    
    # Default to General if template not provided or invalid
    if not template or template not in templates:
        template = "General"
    
    # Prepare response content based on template and health conditions
    if template == "Treatment" and health_conditions:
        treatments = get_treatments_for_conditions(health_conditions, content)
        
        # Use chat summary to provide a more personalized response if available
        if chat_summary:
            response_content = "Based on our conversation, we offer specialized treatments for your health concerns. "
        else:
            response_content = "We offer specialized treatments for your health concerns. "
        
        return templates[template].format(
            name_slot=name_slot,
            conditions=", ".join(health_conditions),
            treatments=treatments,
            response_content=response_content
        )
    else:
        # For other templates, process the content to create a concise response
        response_content = process_content_for_template(user_query, content, template, chat_summary)
        return templates[template].format(
            name_slot=name_slot,
            response_content=response_content
        )


# util functions
def is_only_personal_info(query):
    """Check if the query only contains personal information like name or number"""
    # Simple pattern matching for common name/number patterns
    name_pattern = r'^[A-Z][a-z]+ [A-Z][a-z]+$'
    phone_pattern = r'^\d{10}$|^\+\d{1,3}\d{10}$'
    
    query = query.strip()
    return bool(re.match(name_pattern, query) or re.match(phone_pattern, query))

def extract_health_conditions(query):
    """Extract mentioned health conditions from the query"""
    common_conditions = [
        "back pain", "headache", "stress", "anxiety", "weight", "kidney", 
        "blood pressure", "asthma", "digestion", "sleep", "joint pain"
    ]
    
    mentioned = []
    for condition in common_conditions:
        if condition in query.lower():
            mentioned.append(condition)
    
    return mentioned

def get_treatments_for_conditions(conditions, content):
    """Extract relevant treatments for the mentioned health conditions"""
    if not conditions or not content:
        return "various holistic treatments"
    
    # Simple extraction of treatments from the content
    # In a real implementation, this could be more sophisticated
    treatments = []
    
    if "back pain" in conditions and "yoga" in content.lower():
        treatments.append("yoga therapy")
    if any(c in conditions for c in ["stress", "anxiety"]) and "meditation" in content.lower():
        treatments.append("meditation sessions")
    if "weight" in conditions and "diet" in content.lower():
        treatments.append("personalized diet plans")
    if any(c in conditions for c in ["joint pain", "back pain"]) and "massage" in content.lower():
        treatments.append("therapeutic massage")
    if any(c in conditions for c in ["digestion", "kidney"]) and "detox" in content.lower():
        treatments.append("detoxification treatments")
    
    # Default treatments if nothing specific was found
    if not treatments:
        treatments = ["hydrotherapy", "naturopathy consultations", "holistic wellness programs"]
    
    # Format the list of treatments in a grammatically correct way
    if len(treatments) == 1:
        return treatments[0]
    elif len(treatments) == 2:
        return f"{treatments[0]} and {treatments[1]}"
    else:
        return f"{', '.join(treatments[:-1])}, and {treatments[-1]}"

# Update the process_content_for_template function to use chat_summary
def process_content_for_template(query, content, template, chat_summary=None):
    """Process the content based on the query, template type, and chat summary to create a concise response"""
    if not content:
        return "Thank you for reaching out. We offer natural healing therapies at R K Nature Cure Home. Please call us for more details."
    
    # Length constraints based on template type
    max_lengths = {
        "General": 100,
        "Appointment": 80,
        "Treatment": 120,
        "Pricing": 90,
        "Location": 70,
        "Hours": 60,
        "Insurance": 100
    }
    
    max_length = max_lengths.get(template, 100)
    
    # Incorporate chat summary if available
    if chat_summary:
        # Analyze the chat summary to determine if this is a follow-up question
        if is_follow_up_question(query, chat_summary):
            # Reference the previous conversation
            content = f"As we were discussing, {content}"
        
        # Check if the user has shown interest in specific aspects
        if "price" in chat_summary.lower() or "cost" in chat_summary.lower():
            if template != "Pricing" and "price" not in content.lower() and "cost" not in content.lower():
                content += " Our pricing is competitive and transparent."
        
        if "doctor" in chat_summary.lower() or "specialist" in chat_summary.lower():
            if template != "Doctors" and "doctor" not in content.lower():
                content += " Our specialists are highly qualified in natural healing practices."
    
    # Shorten content if needed
    if len(content) > max_length:
        # Find a good cut-off point at the end of a sentence
        cut_point = content[:max_length].rfind('.')
        if cut_point > 0:
            content = content[:cut_point + 1]
        else:
            content = content[:max_length] + "..."
    
    # Add template-specific endings
    template_endings = {
        "Appointment": "Would you like to book a time?",
        "Pricing": "Our staff can provide more details on request.",
        "Location": "We're conveniently located for your visit.",
        "Hours": "Does our schedule work for you?",
    }
    
    if template in template_endings and not content.endswith(template_endings[template]):
        content = f"{content} {template_endings[template]}"
    
    return content

# Add a new helper function to determine if a question is a follow-up
def is_follow_up_question(query, chat_summary):
    """Determine if the current query is a follow-up to the previous conversation"""
    # Look for phrases indicating a follow-up question
    follow_up_indicators = [
        "what about", "how about", "and", "also", "additionally",
        "further", "more", "another", "else", "other"
    ]
    
    # Check if the query contains any follow-up indicators
    for indicator in follow_up_indicators:
        if indicator in query.lower():
            return True
    
    # Check if the query is very short (likely a follow-up)
    if len(query.split()) <= 3 and not is_only_personal_info(query):
        return True
    
    # Check if the query references something from the chat summary
    # This is a simplified approach - in a real implementation, you might use
    # more sophisticated NLP techniques
    query_words = set(query.lower().split())
    summary_words = set(chat_summary.lower().split())
    common_words = query_words.intersection(summary_words)
    
    # If there are significant common words (excluding stopwords), it's likely a follow-up
    stopwords = {"i", "me", "my", "myself", "we", "our", "ours", "ourselves", 
                "you", "your", "yours", "yourself", "yourselves", "he", "him", 
                "his", "himself", "she", "her", "hers", "herself", "it", "its", 
                "itself", "they", "them", "their", "theirs", "themselves", 
                "what", "which", "who", "whom", "this", "that", "these", "those", 
                "am", "is", "are", "was", "were", "be", "been", "being", "have", 
                "has", "had", "having", "do", "does", "did", "doing", "a", "an", 
                "the", "and", "but", "if", "or", "because", "as", "until", "while", 
                "of", "at", "by", "for", "with", "about", "against", "between", 
                "into", "through", "during", "before", "after", "above", "below", 
                "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", 
                "again", "further", "then", "once", "here", "there", "when", "where", 
                "why", "how", "all", "any", "both", "each", "few", "more", "most", 
                "other", "some", "such", "no", "nor", "not", "only", "own", "same", 
                "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", 
                "should", "now"}
    
    meaningful_common_words = common_words - stopwords
    return len(meaningful_common_words) >= 2