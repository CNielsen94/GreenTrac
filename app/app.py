import streamlit as st
import os
from utils import load_codebook_comments, ensure_folders_exist
import pandas as pd

# Import UI elements
from ui_elements import (
    render_sidebar, render_how_to_tab, 
    render_audio_player_tab, render_file_processing_tab, 
    render_batch_processing_tab, render_codebook_editor_tab,
    render_results_viewer_tab, render_irr_analysis_tab,
    DOCS_FOLDER, AUDIO_FOLDER, LYRICS_FOLDER, RESULTS_FOLDER
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

    if 'irr_analysis' not in st.session_state:
        st.session_state.irr_analysis = None
        
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
    
    # Main content area with tabs - MAKE SURE THIS ORDER MATCHES THE ORDER BELOW
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "How-To", "File Processing", "Batch Processing", 
        "Results", "Codebook Editor", "IRR Analysis", "Audio Player"
    ])
    
    # Render each tab content - MAKE SURE THIS ORDER MATCHES THE ORDER ABOVE
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
        render_irr_analysis_tab()
    
    with tab7:
        render_audio_player_tab()

# Entry point for the application 
if __name__ == "__main__":
    main()
