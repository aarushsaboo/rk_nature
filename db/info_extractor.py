import re
import json
from config import llm

def extract_user_info_llm(summary):
    prompt = f"""
    Extract the following information from this summary:
    1. User's name
    2. User's phone number
    3. What product or service the user is interested in

    Summary: "{summary}"

    Format your response as a valid JSON with these keys: "name", "phone", "product"
    If any information is not available, use "Unknown" as the value.
    """
    
    try:
        response = llm.complete(prompt).text.strip()
        json_match = re.search(r'({.*})', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            data = json.loads(json_str)
            return data.get("name", "Unknown"), data.get("phone", "Unknown"), data.get("product", "Unknown")
        else:
            return extract_user_info_regex(summary)
    except Exception:
        return extract_user_info_regex(summary)

def extract_user_info_regex(summary):
    name = "Unknown"
    phone = "Unknown"
    product = "Unknown"
    
    name_match = re.search(r'User: ([^,]+)', summary)
    if name_match and name_match.group(1).strip() != "Unknown":
        name = name_match.group(1).strip()
        
    phone_match = re.search(r'Phone: ([^,]+)', summary)
    if phone_match and phone_match.group(1).strip() != "Unknown":
        phone = phone_match.group(1).strip()
        
    product_match = re.search(r'Interested in: (.+?)(?:\.|\n|$)', summary)
    if product_match and product_match.group(1).strip() != "Unknown":
        product = product_match.group(1).strip()
    
    return name, phone, product