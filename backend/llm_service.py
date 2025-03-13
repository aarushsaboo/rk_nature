import re
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY, LLM_MODEL
from database import fetch_keywords_data

# Initialize LLM with Gemini
llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)

def match_query_to_keyword(query):
    data_dict = fetch_keywords_data()
    keyword_options = [f"ID: {id} - Keyword: {info['keyword']}" for id, info in data_dict.items()]
    
    prompt = f"Based on the following user query, choose the most suitable keyword ID from this list: {', '.join(keyword_options)}. User query: {query}"
    response = llm.invoke(prompt).content
    
    match = re.search(r'ID: (\d+)', response)
    return int(match.group(1)) if match and int(match.group(1)) in data_dict else None

def extract_name(query):
    prompt = (
        f"Extract the user's name from this query if provided: '{query}'. "
        f"Return the name as a single word or phrase (e.g., 'John') or 'Unknown' if no name is found."
    )
    response = llm.invoke(prompt).content.strip()
    return response if response != "Unknown" else None

def generate_response(query, content, name=None):
    greeting = f"Hi {name}!" if name and name != "Unknown" else "Hello!"
    
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
        return f"{greeting} Oops, something went wrong! Please call R K Nature Cure Home for help."

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