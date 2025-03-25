import os
import json
import pandas as pd
import requests
import streamlit as st
import zipfile
import io
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Default GitHub URL for codebook
DEFAULT_CODEBOOK_URL = "https://raw.githubusercontent.com/CNielsen94/GreenTrac/refs/heads/main/codebook_enhanced.json"

def get_default_api_key():
    """Get the default API key from environment variables."""
    return os.getenv("GOOGLE_API_KEY")

def load_codebook_template(path="plastics_codebook.json"):
    """Load the codebook template from file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Error: {path} not found in the application directory")
        return {}

def fetch_github_file(url):
    """Fetches a file from a GitHub URL (raw content)."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching file from GitHub: {e}")
        return None

def load_codebook_comments(local_path="codebook_finetune.json", github_url=DEFAULT_CODEBOOK_URL, force_local=False):
    """
    Load the codebook comments from GitHub first, then fall back to local file if needed.
    
    Args:
        local_path: Path to local codebook file
        github_url: URL to GitHub raw codebook file
        force_local: If True, only try to load from local file
        
    Returns:
        Dictionary containing the codebook comments
    """
    # Try to load from GitHub first unless force_local is True
    if not force_local:
        with st.spinner("Fetching codebook from GitHub..."):
            github_content = fetch_github_file(github_url)
            if github_content:
                try:
                    return json.loads(github_content)
                except json.JSONDecodeError as e:
                    st.warning(f"Error parsing GitHub codebook: {e}. Falling back to local file.")
    
    # Fall back to local file if GitHub fails or if force_local is True
    try:
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Error: {local_path} not found in the application directory")
        
        # If we got here, both GitHub and local file failed
        st.error("Could not load codebook from either GitHub or local file. Using empty codebook.")
        return {}

def save_codebook_comments(comments_data, path="codebook_finetune.json"):
    """Save the codebook comments to file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(comments_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving codebook comments: {e}")
        return False

def display_json_editor(json_data, key):
    """Displays a JSON editor for the given data."""
    json_str = json.dumps(json_data, indent=2)
    edited_json_str = st.text_area(f"Edit {key}", json_str, height=400, key=f"editor_{key}")
    try:
        return json.loads(edited_json_str)
    except json.JSONDecodeError:
        st.error(f"Invalid JSON format. Please fix the JSON before saving.")
        return json_data

def render_nested_json(json_data, depth=0):
    """Renders nested JSON data with expandable sections."""
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            if isinstance(value, (dict, list)):
                expander = st.expander(f"{' ' * depth * 2}{key}")
                with expander:
                    render_nested_json(value, depth + 1)
            else:
                st.write(f"{' ' * depth * 2}{key}: {value}")
    elif isinstance(json_data, list):
        for i, item in enumerate(json_data):
            expander = st.expander(f"{' ' * depth * 2}Item {i+1}")
            with expander:
                render_nested_json(item, depth + 1)

def flatten_json_for_table(nested_json, prefix=""):
    """Flatten a nested JSON structure for tabular display."""
    flattened = {}
    for key, value in nested_json.items():
        if isinstance(value, dict) and not any(k in ['location', 'reasoning'] for k in value.keys()):
            flattened_child = flatten_json_for_table(value, f"{prefix}{key}.")
            flattened.update(flattened_child)
        else:
            if isinstance(value, dict) and ('location' in value or 'reasoning' in value):
                if 'value' in value:
                    flattened[f"{prefix}{key}"] = value['value']
                if 'location' in value:
                    flattened[f"{prefix}{key}.location"] = value['location']
                if 'reasoning' in value:
                    flattened[f"{prefix}{key}.reasoning"] = value['reasoning']
            else:
                flattened[f"{prefix}{key}"] = value
    return flattened

def create_dataframe_from_json(result):
    """Create a pandas DataFrame from flattened JSON data for display."""
    try:
        flat_data = flatten_json_for_table(result)
        df = pd.DataFrame([flat_data])
        df_transposed = df.T.reset_index()
        df_transposed.columns = ['Field', 'Value']
        return df_transposed
    except Exception as e:
        st.error(f"Error creating dataframe: {e}")
        return None

def load_lyrics(song_filename, lyrics_folder="lyrics"):
    """Load lyrics from a file with the same base name as the song."""
    base_name = os.path.splitext(song_filename)[0]
    possible_extensions = ['.txt', '.md']
    
    for ext in possible_extensions:
        lyric_path = os.path.join(lyrics_folder, f"{base_name}{ext}")
        if os.path.exists(lyric_path):
            try:
                with open(lyric_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                st.error(f"Error loading lyrics: {e}")
                return None
    
    # If no lyric file is found
    return None

def save_uploaded_file(uploaded_file, target_folder):
    """Save an uploaded file to the target folder."""
    try:
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
            
        file_path = os.path.join(target_folder, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True
    except Exception as e:
        st.error(f"Error saving uploaded file: {e}")
        return False

def create_zip_from_results(results):
    """Create a zip file containing all results."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename, result in results.items():
            output_filename = f"{os.path.splitext(filename)[0]}_codebook.json"
            zip_file.writestr(output_filename, json.dumps(result, indent=2, ensure_ascii=False))
    return zip_buffer.getvalue()

def ensure_folders_exist(folders):
    """Ensure all required folders exist."""
    for folder in folders:
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
                st.success(f"Created folder: {folder}")
            except Exception as e:
                st.error(f"Error creating folder {folder}: {e}")