import re
import logging
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY, LLM_MODEL
from database import fetch_keywords_data
from functools import lru_cache

# Initialize LLM with Gemini
llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)

# Cache for keyword data to avoid repeated database calls
@lru_cache(maxsize=1)
def get_keywords_data():
    return fetch_keywords_data()

async def batch_process_queries(query):
    """Process multiple analyses in a single call while preserving original prompt structures"""
    
    # Get keyword data
    data_dict = get_keywords_data()
    keyword_options = [f"ID: {id} - Keyword: {info['keyword']}" for id, info in data_dict.items()]
    
    # Create a batch prompt that maintains original prompt structures
    batch_prompt = f"""Please answer the following questions about this user query: '{query}'

Question 1: Extract the user's name from this query if provided. Return the name as a single word or phrase (e.g., 'John') or 'Unknown' if no name is found.

Question 2: Analyze this message carefully: '{query}'. Is this ONLY providing personal information like a name or phone number, with NO question, request, or health issue? For example, 'John Smith' or '9876543210' would be a 'yes', but 'What payment methods do you accept?' would be a 'no'. Answer with just 'yes' or 'no'.

Question 3: Based on the following user query, choose the most suitable keyword ID from this list: {', '.join(keyword_options)}. User query: {query}

Question 4: List any health conditions from these options that are mentioned in the query: back pain, headache, stress, anxiety, weight, kidney, blood pressure, asthma, digestion, sleep, joint pain. If none are mentioned, respond with "None".

Format your response exactly as follows:
Name: [extracted name or Unknown]
Info_Only: [yes or no]
Keyword_ID: [ID number]
Health_Conditions: [comma-separated conditions or None]"""

    # Make a single LLM call
    response = llm.invoke(batch_prompt).content
    
    # Parse the response
    name_match = re.search(r'Name: (.+)', response)
    info_only_match = re.search(r'Info_Only: (.+)', response)
    keyword_id_match = re.search(r'Keyword_ID: (\d+)', response)
    health_match = re.search(r'Health_Conditions: (.+)', response)
    
    # Extract values with original processing logic
    name = name_match.group(1).strip() if name_match else "Unknown"
    name = None if name == "Unknown" else name
    
    is_just_info = info_only_match.group(1).strip().lower() == "yes" if info_only_match else False
    
    keyword_id = int(keyword_id_match.group(1)) if keyword_id_match else None
    keyword_id = keyword_id if keyword_id and keyword_id in data_dict else None
    
    health_conditions = health_match.group(1).strip() if health_match else "None"
    health_conditions = [] if health_conditions == "None" else [c.strip() for c in health_conditions.split(',')]
    
    return {
        "name": name,
        "is_just_info": is_just_info,
        "keyword_id": keyword_id,
        "health_conditions": health_conditions
    }

# Original function preserved for reference, now using cached results from batch process
def match_query_to_keyword(query, batch_results=None):
    if batch_results and "keyword_id" in batch_results:
        return batch_results["keyword_id"]
    
    data_dict = get_keywords_data()
    keyword_options = [f"ID: {id} - Keyword: {info['keyword']}" for id, info in data_dict.items()]
    
    prompt = f"Based on the following user query, choose the most suitable keyword ID from this list: {', '.join(keyword_options)}. User query: {query}"
    response = llm.invoke(prompt).content
    
    match = re.search(r'ID: (\d+)', response)
    return int(match.group(1)) if match and int(match.group(1)) in data_dict else None

# Original function preserved for reference, now using cached results from batch process
def extract_name(query, batch_results=None):
    if batch_results and "name" in batch_results:
        return batch_results["name"]
    
    prompt = (
        f"Extract the user's name from this query if provided: '{query}'. "
        f"Return the name as a single word or phrase (e.g., 'John') or 'Unknown' if no name is found."
    )
    response = llm.invoke(prompt).content.strip()
    return response if response != "Unknown" else None

# Original function preserved exactly as it was
def generate_response(query, content, name=None):
    # Simple, friendly greeting
    greeting = f"Hi {name}!" if name and name != "Unknown" else "Hello!"
    
    # Check if a name or phone number is being provided
    name_or_number_check = (
        f"Analyze this message carefully: '{query}'. "
        f"Is this ONLY providing personal information like a name or phone number, with NO question, "
        f"request, or health issue? For example, 'John Smith' or '9876543210' would be a 'yes', "
        f"but 'What payment methods do you accept?' would be a 'no'. "
        f"Answer with just 'yes' or 'no'."
    )
    is_just_name_or_number = llm.invoke(name_or_number_check).content.strip().lower() == "yes"
    
    if is_just_name_or_number:
        return f"{greeting} Thank you for that information. How can we help you today?"
    
    # List of common health conditions to check for
    health_conditions = [
        "back pain", "headache", "stress", "anxiety", "weight", "kidney", 
        "blood pressure", "asthma", "digestion", "sleep", "joint pain"
    ]
    
    # Check if query mentions any health condition
    mentioned_conditions = []
    for condition in health_conditions:
        if condition in query.lower():
            mentioned_conditions.append(condition)
    
    if mentioned_conditions:
        # Modify the prompt to be more proactive with suggestions
        condition_str = ", ".join(mentioned_conditions)
        prompt = (
            f"You are a friendly receptionist at R K Nature Cure Home, a naturopathy hospital. "
            f"The user mentioned these health issues: {condition_str}. "
            f"Using ONLY the information in this text: '{content}', provide a warm, concise response (max 2 lines) "
            f"that specifically mentions therapies or treatments we offer for their condition. "
            f"Be PROACTIVE - don't just say 'we can help' but mention 2-3 specific treatments. "
            f"End with a brief invitation to schedule an appointment. User query: '{query}'"
        )
    else:
        prompt = (
            f"You are a friendly receptionist at R K Nature Cure Home, a naturopathy hospital. "
            f"We are asking user to provide name and number through other function, incase they reply with name or number, just say thank you and ask how can we help you. "
            f"Answer the user's question in a warm, concise tone (max 2 lines total, including greeting), using this info: '{content}'. "
            f"Keep it extremely concise and avoid technical terms. If the info isn't enough, briefly suggest contacting us. User query: '{query}'"
        )
    
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return f"{greeting} We're experiencing a technical issue. Please call R K Nature Cure Home for immediate assistance."

# Use batch results for generate_response if available
async def generate_response_with_batch(query, content, batch_results):
    if batch_results and "is_just_info" in batch_results:
        is_just_name_or_number = batch_results["is_just_info"]
        name = batch_results["name"]
        mentioned_conditions = batch_results["health_conditions"]
        
        # Simple, friendly greeting
        greeting = f"Hi {name}!" if name and name != "Unknown" else "Hello!"
        
        if is_just_name_or_number:
            return f"{greeting} Thank you for that information. How can we help you today?"
        
        if mentioned_conditions:
            # Modify the prompt to be more proactive with suggestions
            condition_str = ", ".join(mentioned_conditions)
            prompt = (
                f"You are a friendly receptionist at R K Nature Cure Home, a naturopathy hospital. "
                f"The user mentioned these health issues: {condition_str}. "
                f"Using ONLY the information in this text: '{content}', provide a warm, concise response (max 2 lines) "
                f"that specifically mentions therapies or treatments we offer for their condition. "
                f"Be PROACTIVE - don't just say 'we can help' but mention 2-3 specific treatments. "
                f"End with a brief invitation to schedule an appointment. User query: '{query}'"
            )
        else:
            prompt = (
                f"You are a friendly receptionist at R K Nature Cure Home, a naturopathy hospital. "
                f"We are asking user to provide name and number through other function, incase they reply with name or number, just say thank you and ask how can we help you. "
                f"Answer the user's question in a warm, concise tone (max 2 lines total, including greeting), using this info: '{content}'. "
                f"Keep it extremely concise and avoid technical terms. If the info isn't enough, briefly suggest contacting us. User query: '{query}'"
            )
        
        try:
            response = llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return f"{greeting} We're experiencing a technical issue. Please call R K Nature Cure Home for immediate assistance."
    else:
        # Fall back to original method if batch processing fails
        return generate_response(query, content, batch_results.get("name") if batch_results else None)

# Original function preserved exactly as it was
def generate_summary(existing_summary, new_log_entry):
    if existing_summary:
        prompt = (
            f"Previous summary: '{existing_summary}'. "
            f"New chat entry: '{new_log_entry}'. "
            f"Update the previous summary to include any new information about the user. "
            f"If new information conflicts with old information, use the new information. "
            f"Provide a concise two-line summary of what has happened so far. "
            f"Include a second line in this format: 'User: [name], Phone: [phone], Interested in: [product]' "
            f"where [name], [phone], and [product] are extracted from both the previous summary and new chat. "
            f"Use 'Unknown' only if the information is still not available."
        )
    else:
        prompt = (
            f"Based on this chat log: '{new_log_entry}', provide a concise two-line summary of what has happened so far. "
            f"Include a second line in this format: 'User: [name], Phone: [phone], Interested in: [product]' "
            f"where [name], [phone], and [product] are extracted from the log or 'Unknown' if not found."
        )
    
    summary = llm.invoke(prompt).content.strip()
    logging.info(f"Generated summary: {summary}")
    return summary