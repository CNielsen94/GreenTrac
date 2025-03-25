import streamlit as st
import os
from utils import load_codebook_comments, ensure_folders_exist

# Import UI elements
from ui_elements import (
    render_sidebar, render_how_to_tab, 
    render_audio_player_tab, render_file_processing_tab, 
    render_batch_processing_tab, render_codebook_editor_tab,
    render_results_viewer_tab, 
    DOCS_FOLDER, AUDIO_FOLDER, LYRICS_FOLDER
)

# Set page config
st.set_page_config(
    page_title="Qualitative Coding Tool",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_app():
    """Initialize the application by setting up directories and session state."""
    # Ensure required directories exist
    ensure_folders_exist([DOCS_FOLDER, AUDIO_FOLDER, LYRICS_FOLDER])
    
    # Configure session state variables if they don't exist
    if 'results' not in st.session_state:
        st.session_state.results = {}
        
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = []
        
    # Always load the codebook from GitHub on startup
    if 'codebook_comments' not in st.session_state:
        st.session_state.codebook_comments = load_codebook_comments(force_local=False)
    
    # Initialize API key in session state if not present
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None

def main():
    """Main function to run the Streamlit application."""
    # Initialize the application at startup
    init_app()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area with tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "How-To", "File Processing", "Batch Processing", 
        "Results", "Codebook Editor", "Audio Player"
    ])
    
    # Render each tab content
    with tab1:
        render_how_to_tab()
    
    with tab2:
        render_file_processing_tab()
    
    with tab3:
        render_batch_processing_tab()
    
    with tab4:
        render_results_viewer_tab()
    
    with tab5:
        render_codebook_editor_tab()
    
    with tab6:
        render_audio_player_tab()

# Entry point for the application 
if __name__ == "__main__":
    main()