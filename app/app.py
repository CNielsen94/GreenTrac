import streamlit as st
import os
from utils import load_codebook_comments, ensure_folders_exist
import pandas as pd

# Import authentication
from auth import require_login, admin_panel

# Import UI elements
from ui_elements import (
    render_sidebar, render_how_to_tab, 
    render_audio_player_tab, render_batch_processing_tab, 
    render_codebook_editor_tab, render_results_viewer_tab,
    DOCS_FOLDER, AUDIO_FOLDER, LYRICS_FOLDER, RESULTS_FOLDER
)

# Import experiment history
from ui_experiment_history import render_experiment_history_tab

# Set page config
st.set_page_config(
    page_title="GreenTracCoder",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_app():
    """Initialize the application by setting up directories and session state."""
    # Ensure required directories exist
    ensure_folders_exist([DOCS_FOLDER, AUDIO_FOLDER, LYRICS_FOLDER, RESULTS_FOLDER])
    
    # Configure session state variables if they don't exist
    if 'results' not in st.session_state:
        st.session_state.results = {}

    # Initialize IRR analysis results
    if 'irr_analysis' not in st.session_state:
        # Check if there's an existing IRR analysis report
        irr_report_path = os.path.join(RESULTS_FOLDER, 'irr_analysis_report.xlsx')
        if os.path.exists(irr_report_path):
            # If report exists, create a minimal results structure
            st.session_state.irr_analysis = {
                'report_path': irr_report_path,
                'report_df': pd.read_excel(irr_report_path) if pd.read_excel else None,
                # Other fields will be populated later if needed
            }
        else:
            st.session_state.irr_analysis = None
        
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = []
        
    # Always load the codebook from GitHub on startup
    if 'codebook_comments' not in st.session_state:
        st.session_state.codebook_comments = load_codebook_comments(force_local=False)
    
    # Initialize API key in session state if not present
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None
    
    # Initialize active tab selection
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = None
        
    # Make sure experiments directory exists
    from versioning import ensure_experiments_dir
    ensure_experiments_dir()

@require_login
def main():
    """Main function to run the Streamlit application."""
    # Initialize the application at startup
    init_app()
    
    # Render sidebar
    render_sidebar()
    
    # Define tab names - simplified to remove redundant tabs
    tab_names = [
        "How-To", 
        "Batch Processing & Analysis", 
        "Codebook Editor", 
        "Experiment History", 
        "Audio Player", 
        "User Management"
    ]
    
    # Determine the active tab index
    default_tab = 0  # How-To is the default
    
    # Switch to a specific tab if requested by other parts of the app
    if st.session_state.active_tab == "Results":
        active_tab_index = 2  # Results tab index (adjusted for removed tabs)
        # Reset the active tab to avoid getting stuck in a loop
        st.session_state.active_tab = None
    elif st.session_state.active_tab == "Experiment History":
        active_tab_index = 4  # Experiment History tab index (adjusted for removed tabs)
        # Reset the active tab
        st.session_state.active_tab = None
    else:
        active_tab_index = default_tab
    
    # Create tabs with the active tab highlighted
    tabs = st.tabs(tab_names)
    
    # Render each tab content
    with tabs[0]:  # How-To
        render_how_to_tab()
    
    with tabs[1]:  # Batch Processing & Analysis
        render_batch_processing_tab()
    
    with tabs[2]:  # Codebook Editor
        render_codebook_editor_tab()
    
    with tabs[3]:  # Experiment History
        render_experiment_history_tab()
    
    with tabs[4]:  # Audio Player
        render_audio_player_tab()
    
    with tabs[5]:  # User Management
        # Only show the admin panel for admin users
        if st.session_state.get('is_admin', False):
            admin_panel()
        else:
            st.warning("You need admin privileges to access this section.")

# Entry point for the application 
if __name__ == "__main__":
    main()
