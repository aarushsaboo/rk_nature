import re
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY, LLM_MODEL

llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)

def ai_clubbed(user_query, bulk_content, template_choices, chat_summary=None, name=None, phone=None):
    """
    Process user query and generate all needed data in a single API call
    
    Args:
        user_query (str): The user's query
        bulk_content (dict): Dictionary of all content with ID as key
        template_choices (list): List of available templates
        chat_summary (str, optional): Summary of the chat conversation so far
        name
        phone
    
    Returns:
        tuple: (name, phone, summary, response)
    """
    # Include chat summary in context if available
    context = ""
    if chat_summary:
        context = f"Chat history summary: {chat_summary}\n\n"
    print("Name: ", name)
    print("Phone: ", phone)

    # Basic assistant prompt
    base_prompt = (
        f"You are a friendly receptionist at R K Nature Cure Home, a naturopathy hospital. "
        f"We are asking user to provide name and number through other function, incase they reply with name or number, just say thank you and ask how can we help you. "
        f"Answer the user's question in a warm, concise tone (max 2 lines total, including greeting). "
        f"Keep it extremely concise and avoid technical terms. If the info isn't enough, briefly suggest contacting us. User query: '{user_query}'"

        f" Proactively list the therapies offered if the user query is about a specific health issue, and be sympathetic & conscious of the other person's pain. "
    )
    
    # Template-specific guidance based on template type
    template_guidance = {
        "Hello": "Provide a friendly greeting and welcome them to RK Nature Cure Home.",
        
        "Introduction": "Briefly introduce RK Nature Cure Home as a premier naturopathy center in Coimbatore.",
        
        "AboutUs": "Focus on our center's natural healing approach using scientifically-backed naturopathic methods.",
        
        "HealthIssueGeneral": "Acknowledge their health concerns and mention all the holistic solutions offered.",
        
        "BackPain": "Acknowledge their back pain and mention all the different therapies offered.",
        
        "JointPain": "Acknowledge that joint pain can be debilitating and mention our mud therapy and physiotherapy.",
        
        "Stress": "Emphasize our holistic approach to stress management including meditation and pranayama.",
        
        "Diabetes": "Mention our natural approach to diabetes management with diet plans and exercises.",
        
        "Location": "Share our address: Krishna Layout, Ganapathy, Coimbatore - 641006.",
        
        "OurContactDetails": "Provide our contact number +91 88700-66622 and mention reception hours (6 AM to 8 PM).",
        
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
        
        "General": "Provide a general helpful response and ask how else we can assist.",

        "Unknown": "Answer in the way you think will help the user, provide our phone (+91 88700-66622) "
    }
    
    # Format all template guidance for the prompt
    template_guidance_str = "\n".join([f"- {template}: {guidance}" for template, guidance in template_guidance.items()])
    
    # Format content for the prompt
    content_section = "\n".join([f"Content ID {id}:\n{content}" for id, content in bulk_content.items()])
    
    # Combined prompt that handles all tasks
    prompt = (
        f"{context}"
        f"Analyze this user query carefully: '{user_query}'\n\n"
        
        f"AVAILABLE CONTENT:\n{content_section}\n\n"
        
        f"Task 1: The user's name is already known to be '{name}' if not None. If the user asks about their name, tell them their name is '{name}'. Only look for a new name in the query if it appears to be different from the existing known name.\n\n"
        f"Return the name as a single word or phrase (e.g., 'John') or 'Unknown' if no name is found. The name might be {name}. If the user asks his name, tell it to him if you have the information.\n\n"
        
        f"Task 2: Extract the user's phone number from this query if provided. "
        f"Return just the digits of the phone number or 'Unknown' if no phone number is found. The number might be {phone}\n\n"
        
        f"Task 3: Choose the most suitable template out of the following options: {', '.join(template_choices)}. "
        f"If no template is appropriate, use 'Unknown'. Just follow the template's specific instructions & write the name of the template here ( write Unknown if no template exists)\n\n"
        
        f"Task 4: Provide a concise two-line summary of any important details, and the conversation history. "
        # f"Include a second line in this format: 'User: [name], Phone: [phone], Interested in: [topic]' "
        # f"where [name], [phone], and [topic] are extracted from the query or 'Unknown' if not found.\n\n"
        
        f"Task 5: {base_prompt}"
        f"Use the template guidance to shape your response:\n\n{template_guidance_str}\n\n"
        
        f"Format your response exactly like this:\n"
        f"Name: [Name or Unknown]\n"
        f"Phone: [Phone or Unknown]\n"
        f"Template: [Template or General]\n"
        f"Summary: [Summary]\n"
        f"Response: [Your actual response to the user]"
    )
    
    # Make the API call
    ai_response = llm.invoke(prompt).content
    
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
    
    logging.info(f"Processed response - Name: {name}, Phone: {phone}, Template: {template_str}, Summary length: {len(summary)}, Response length: {len(response)}")
    
    return name, phone, summary, response