import os
import json
import re
import time
import threading
import streamlit as st
from google import genai
from google.genai import types
import pathlib
from collections import deque
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Rate limiter setup
MAX_CALLS_PER_MINUTE = 10
CALL_HISTORY = deque()
lock = threading.Lock()

def rate_limit():
    """Rate limits the API calls to avoid exceeding the quota."""
    with lock:
        current_time = time.time()
        while CALL_HISTORY and CALL_HISTORY[0] <= current_time - 60:
            CALL_HISTORY.popleft()
        if len(CALL_HISTORY) >= MAX_CALLS_PER_MINUTE:
            sleep_time = 60 - (current_time - CALL_HISTORY[0])
            st.warning(f"Rate limit hit. Waiting for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)
        CALL_HISTORY.append(time.time())

def create_dynamic_prompt(codebook_template, codebook_comments):
    """Creates a dynamic prompt based on codebook comments."""
    prompt = """
    Analyze the provided PDF document and extract information according to the provided codebook JSON structure. Populate the fields in the codebook with data from the document.
    If a specific field isn't directly found in the text, leave it as null, an empty array or an empty string as specified in the codebook template.

    IMPORTANT: For each extracted value, your output should have the following structure:
    ```
    {
      "field_name": {
        "value": "extracted value",
        "location": "section where this was found in the document",
        "reasoning": "explanation of why you extracted this value"
      }
    }
    ```

    For each extracted value, include in the output JSON the section heading and sub-section heading (if available) it was found in, using the key 'location' within the same object as the value. Document sections like introduction, methods, results, etc. should be used for location. Please make sure the output in the location is in the format "section, subsection", or "section" if no subsection is found. If there is no specific section, please leave the location as a blank string "".
    
    For each extracted value, also include your reasoning for choosing that value in a "reasoning" field. This should explain how you determined the value.
    
    You should never infer/extract information based on the document headers, and only use document headers for the location key inside the output JSON.
    In addition, try to infer information from sensible places, such as objectives from objective sections etc where applicable. Note also, that preamble and objectives should not be seen as the same thing.
    """

    def add_instructions(data, comments, prefix=""):
        nonlocal prompt
        for key, value in data.items():
            comment = comments.get(key)
            if isinstance(value, dict):
                 add_instructions(value, comment, prefix=f"{prefix}{key}.")
            elif isinstance(comment, str):
                prompt_line = f"  - For the field '{prefix}{key}', the following description applies: '{comment}'. "
                if "Boolean" in comment:
                     prompt_line += "If the text contains a positive affirmation or mentions of this field, populate it with `true`, otherwise populate with `false`"
                if "YYYY-MM-DD" in comment:
                    prompt_line += " Please make sure the date is in YYYY-MM-DD format."
                if "['Member State', 'Observer', 'Organization']" in comment:
                    prompt_line += " Please choose between `Member State`, `Observer`, or `Organization`. "
                if "['Global', 'National', 'Sub-national']" in comment:
                    prompt_line += " Please choose between `Global`, `National` or `Sub-national`. "

                prompt += prompt_line + "\n"

    add_instructions(codebook_template, codebook_comments)

    prompt += f"""
    Codebook structure:
    ```
    {json.dumps(codebook_template, indent=2)}
    ```

    IMPORTANT FORMATTING INSTRUCTIONS:
    1. For all fields, including nested fields, follow this structure:
       - Boolean values should be formatted as: {{"value": true/false, "location": "section", "reasoning": "explanation"}}
       - String values should be formatted as: {{"value": "text", "location": "section", "reasoning": "explanation"}}
       - Array values should have the location and reasoning at the item level, like:
         [
           {{"value": "item 1", "location": "section 1", "reasoning": "explanation 1"}},
           {{"value": "item 2", "location": "section 2", "reasoning": "explanation 2"}}
         ]

    2. Always include all three of these fields (value, location, reasoning) for every extracted piece of information.
    3. Never omit the location or reasoning fields, even if they're empty strings.

    Output the complete codebook in JSON format, ensuring every field has the proper structure.
    """
    return prompt

def extract_answer_and_reasoning(response):
    """Extracts answer and reasoning text from the response."""
    answer_json = None
    reasoning_text = ""

    if not hasattr(response, 'text'):
        st.error("Unexpected response format from Gemini API")
        return None, None
    
    response_text = response.text
    
    # Try to extract JSON content
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
    if json_match:
        try:
            answer_json = json.loads(json_match.group(1).strip())
            # The rest might contain reasoning
            reasoning_parts = response_text.split('```json')
            if len(reasoning_parts) > 1:
                reasoning_text = reasoning_parts[0].strip()
                if not reasoning_text:
                    # Check for text after the JSON block
                    reasoning_parts = response_text.split('```', 2)
                    if len(reasoning_parts) > 2:
                        reasoning_text = reasoning_parts[2].strip()
        except json.JSONDecodeError as e:
            st.error(f"Error decoding JSON answer: {e}")
            st.code(json_match.group(1).strip(), language="json")
            return None, None
    else:
        # Try to extract JSON without code blocks
        try:
            # Look for something that looks like JSON
            potential_json = re.search(r'(\{[\s\S]*\})', response_text)
            if potential_json:
                answer_json = json.loads(potential_json.group(1).strip())
                # Everything else might be reasoning
                reasoning_text = response_text.replace(potential_json.group(1), "").strip()
        except json.JSONDecodeError as e:
            st.error(f"Error decoding JSON answer (no code block): {e}")
            st.code(response_text, language="text")
            return None, None

    return answer_json, reasoning_text

def add_reasoning_to_json(json_data, reasoning_text):
    """
    Adds the reasoning to each field in the JSON data.
    This version preserves existing reasoning if present and only adds reasoning where missing.
    """
    def recursive_add(data, reasoning):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    # Only add reasoning if value has location but no reasoning
                    if "value" in value and "location" in value and "reasoning" not in value:
                        value["reasoning"] = reasoning
                    else:
                        # Process nested dictionaries
                        recursive_add(value, reasoning)
                elif isinstance(value, list):
                    # Process lists
                    for item in value:
                        if isinstance(item, dict):
                            # Only add reasoning to list items with value and location but no reasoning
                            if "value" in item and "location" in item and "reasoning" not in item:
                                item["reasoning"] = reasoning
                            else:
                                recursive_add(item, reasoning)
        return data

    return recursive_add(json_data, reasoning_text)

def process_extracted_data(data):
    """
    Processes extracted data to handle inconsistencies and ensure correct structure.
    This version preserves the location and reasoning fields.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                # Check if it has all required fields
                if "value" in value:
                    # Make sure we preserve location and reasoning if present
                    location = value.get("location", "")
                    reasoning = value.get("reasoning", "")
                    
                    # Replace the value with a properly structured dict
                    data[key] = {
                        "value": value["value"],
                        "location": location if location is not None else "",
                        "reasoning": reasoning if reasoning is not None else ""
                    }
                else:
                    # Process nested dictionaries
                    process_extracted_data(value)
            elif isinstance(value, list):
                # Process lists
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        # If list item has value field, ensure correct structure
                        if "value" in item:
                            location = item.get("location", "")
                            reasoning = item.get("reasoning", "")
                            
                            value[i] = {
                                "value": item["value"],
                                "location": location if location is not None else "",
                                "reasoning": reasoning if reasoning is not None else ""
                            }
                        else:
                            # Process nested dicts within lists
                            process_extracted_data(item)
    return data

def get_api_key(user_provided_key=None):
    """Get the API key from various sources in order of priority."""
    # 1. Use the user-provided key if available
    if user_provided_key:
        return user_provided_key
    
    # 2. Check if there's a key in session state
    if 'api_key' in st.session_state and st.session_state.api_key:
        return st.session_state.api_key
    
    # 3. Check for environment variable from .env file
    env_key = os.getenv("GOOGLE_API_KEY")
    if env_key:
        return env_key
    
    # If no API key found, show error
    st.error("No API key found. Please enter an API key in the sidebar or add it to your .env file.")
    return None

def analyze_pdf_file(pdf_file_path, codebook_template, codebook_comments, api_key=None):
    """Analyzes a PDF file using Gemini and returns a populated codebook JSON."""
    try:
        # Check if file exists
        if not os.path.exists(pdf_file_path):
            st.error(f"Error: File not found at {pdf_file_path}")
            return None
    except Exception as e:
        st.error(f"Error checking PDF file: {e}")
        return None

    # Get the API key from various sources
    api_key = get_api_key(api_key)
    
    # Check if we have a valid API key
    if not api_key:
        st.error("No valid API key found. Please provide an API key to continue.")
        return None
    
    # Set up environment variable for API key
    os.environ["GOOGLE_API_KEY"] = api_key
    
    # Initialize Gemini client
    client = genai.Client()
    
    # Use st.status to show processing status
    with st.status(f"Processing {os.path.basename(pdf_file_path)}...", expanded=True) as status:
        st.write("Creating dynamic prompt...")
        
        prompt = create_dynamic_prompt(codebook_template, codebook_comments)
        
        status.update(label=f"Rate limiting API calls", state="running")
        rate_limit()  # Rate limiter called before API call
        
        status.update(label=f"Sending PDF to Gemini API", state="running")
        try:
            # Create a pathlib Path object for the PDF
            pdf_path = pathlib.Path(pdf_file_path)
            
            # Generate content with PDF and prompt
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=pdf_path.read_bytes(),
                        mime_type='application/pdf',
                    ),
                    prompt
                ]
            )
            
            status.update(label=f"Extracting response data", state="running")
            extracted_json, reasoning_text = extract_answer_and_reasoning(response)

            if extracted_json:
                status.update(label=f"Processing extracted data", state="running")
                # First add any missing reasoning from the response text
                extracted_json_with_reasoning = add_reasoning_to_json(extracted_json, reasoning_text)
                # Then ensure proper structure
                processed_json = process_extracted_data(extracted_json_with_reasoning)
                status.update(label=f"Finished processing", state="complete")
                return processed_json
            else:
                st.error(f"Error: No JSON extracted from Gemini response for {os.path.basename(pdf_file_path)}")
                status.update(label=f"Processing failed", state="error")
                return None
                
        except Exception as e:
            st.error(f"Error processing PDF with Gemini API: {e}")
            status.update(label=f"API error", state="error")
            return None