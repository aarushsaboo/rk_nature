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

async def process_query_batch(user_query, session_id=None, existing_summary=None):
    """Process all query analysis in a single LLM call to reduce API usage"""
    
    # Get keyword data
    data_dict = get_keywords_data()
    keyword_options = [f"ID: {id} - Keyword: {info['keyword']}" for id, info in data_dict.items()]
    
    # Create a single batch prompt that handles all analysis tasks
    batch_prompt = f"""Analyze this user query: "{user_query}"

Task 1: Extract the user's name if provided. Return "Unknown" if none found.

Task 2: Determine if this message ONLY provides personal information like a name or phone number, with NO question or health issue. Answer "yes" or "no".

Task 3: From this list, choose the most suitable keyword ID: {', '.join(keyword_options)}.

Task 4: Identify any health conditions mentioned from this list: back pain, headache, stress, anxiety, weight, kidney, blood pressure, asthma, digestion, sleep, joint pain.

Format your response exactly as:
Name: [name or Unknown]  
Info_Only: [yes or no]
Keyword_ID: [ID number]
Health_Conditions: [comma-separated list or None]"""

    # Make a single LLM call
    response = llm.invoke(batch_prompt).content
    
    # Parse the response
    name_match = re.search(r'Name: (.+)', response)
    info_only_match = re.search(r'Info_Only: (.+)', response)
    keyword_id_match = re.search(r'Keyword_ID: (\d+)', response)
    health_match = re.search(r'Health_Conditions: (.+)', response)
    
    # Extract values
    name = name_match.group(1).strip() if name_match else "Unknown"
    name = None if name == "Unknown" else name
    
    is_just_info = info_only_match.group(1).strip().lower() == "yes" if info_only_match else False
    
    keyword_id = int(keyword_id_match.group(1)) if keyword_id_match else None
    keyword_id = keyword_id if keyword_id in data_dict else None
    
    health_conditions = health_match.group(1).strip() if health_match else "None"
    health_conditions = [] if health_conditions == "None" else [c.strip() for c in health_conditions.split(',')]
    
    # Return parsed results
    return {
        "name": name,
        "is_just_info": is_just_info,
        "keyword_id": keyword_id,
        "health_conditions": health_conditions
    }

async def generate_response_and_summary(user_query, analysis_results, content, session_id=None, existing_summary=None):
    """Generate response and summary in a single LLM call"""
    
    name = analysis_results["name"]
    is_just_info = analysis_results["is_just_info"]
    health_conditions = analysis_results["health_conditions"]
    
    # Create greeting
    greeting = f"Hi {name}!" if name else "Hello!"
    
    # Determine response type
    if is_just_info:
        initial_answer = f"{greeting} Thank you for that information. How can we help you today?"
    elif health_conditions:
        condition_str = ", ".join(health_conditions)
        response_type = "health_specific"
    else:
        response_type = "general"
    
    # Construct the batch prompt for response and summary
    new_log_entry = f"User: {user_query}"
    
    batch_prompt = f"""You are a friendly receptionist at R K Nature Cure Home, a naturopathy hospital.

Task 1: Generate a response to the user query.
User query: "{user_query}"
Available information: "{content}"
Response type: {"'Thank you' message" if is_just_info else f"'Health specific' addressing these conditions: {', '.join(health_conditions)}" if health_conditions else "General inquiry response"}
Guidelines:
- Start with "{greeting}"
- {"Keep it extremely concise (max 2 lines total)" if not health_conditions else f"Be PROACTIVE - mention 2-3 specific treatments for {', '.join(health_conditions)}"}
- End with an invitation to schedule an appointment if health issues are mentioned
- Keep it warm and friendly but concise

Task 2: Generate a conversation summary.
{"Previous summary: " + existing_summary if existing_summary else "No previous summary."}
New chat entry: "{new_log_entry}"
Guidelines:
- Provide a concise two-line summary
- Second line format: "User: [name], Phone: [phone], Interested in: [product]"
- Use "Unknown" for missing information
- Update with any new information from this exchange

Format your response exactly as:
Response: [your response to user]
Summary: [your conversation summary]"""

    # Make a single LLM call
    response = llm.invoke(batch_prompt).content
    
    # Parse the response
    response_match = re.search(r'Response: (.*?)(?=\nSummary:|$)', response, re.DOTALL)
    summary_match = re.search(r'Summary: (.*?)$', response, re.DOTALL)
    
    initial_answer = response_match.group(1).strip() if response_match else f"{greeting} Thank you for your inquiry. How can we help you today?"
    summary = summary_match.group(1).strip() if summary_match else f"User inquired about services. \nUser: {name if name else 'Unknown'}, Phone: Unknown, Interested in: Unknown"
    
    # Add prompts for missing information
    final_answer = initial_answer
    
    if "User: Unknown" in summary and "Phone: Unknown" in summary:
        final_answer += "\n\nCan you share your name and number to help us better?"
    elif "User: Unknown" in summary:
        final_answer += "\n\nCan you share your name to help us better?"
    elif "Phone: Unknown" in summary:
        final_answer += "\n\nCan you share your number to help us better?"
    
    return {
        "response": final_answer,
        "summary": summary
    }