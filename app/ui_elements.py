import streamlit as st
import numpy as np
from IRR_pipeline import process_json_files
import seaborn as sns
import re
import traceback
import matplotlib.pyplot as plt
from pathlib import Path
import os
import json
import pandas as pd
import zipfile
import io
from utils import (
    load_codebook_template, load_codebook_comments, save_codebook_comments, 
    fetch_github_file, display_json_editor, render_nested_json,
    create_dataframe_from_json, load_lyrics, save_uploaded_file,
    create_zip_from_results, ensure_folders_exist, get_default_api_key,
    DEFAULT_CODEBOOK_URL
)

from irr_analysis import run_irr_analysis_for_streamlit
from gemini_calls import analyze_pdf_file

# Directory setup
DOCS_FOLDER = "docs"     # Folder containing PDF files to analyze
AUDIO_FOLDER = "audio"   # Folder containing MP3 files
LYRICS_FOLDER = "lyrics" # Folder containing lyric files
RESULTS_FOLDER = "results"

def render_sidebar():
    """Render the application sidebar with configuration options."""
    with st.sidebar:
        st.header("Configuration")
        
        # Status indicators
        st.subheader("Status")
        
        # Load codebook template
        codebook_template = load_codebook_template()
        if codebook_template:
            st.success("✅ Codebook template loaded")
        else:
            st.error("❌ Codebook template not found")
            
        if st.session_state.codebook_comments:
            st.success("✅ Codebook comments loaded from GitHub")
        else:
            st.error("❌ Codebook comments could not be loaded")
        
        # Check if docs folder exists
        if os.path.isdir(DOCS_FOLDER):
            pdf_files = [f for f in os.listdir(DOCS_FOLDER) if f.lower().endswith(".pdf")]
            if pdf_files:
                st.success(f"✅ Found {len(pdf_files)} PDF files in '{DOCS_FOLDER}' folder")
            else:
                st.warning(f"⚠️ No PDF files found in '{DOCS_FOLDER}' folder")
        else:
            st.error(f"❌ '{DOCS_FOLDER}' folder not found")
            
        # API Key Configuration
        st.subheader("API Configuration")
        
        # Get default API key from environment or other sources
        default_key = get_default_api_key()
        
        # Determine default displayed value
        display_value = "•" * 8 if default_key else ""
        
        # Show API key input with a default masked value if available
        api_key = st.text_input(
            "Gemini API Key", 
            value=display_value,
            type="password",
            help="Enter your Google Gemini API key (NOT YET IMPLEMENTED)"
        )
        
        # Only update if the user has actually entered something
        if api_key and not (api_key == "•" * 8 and default_key):
            st.session_state.api_key = api_key
            st.success("API key updated!")
        elif default_key and not api_key:
            # If using the default key
            st.info("Using API key from environment variables")
        
        # GitHub integration
        st.subheader("GitHub Integration")
        
        # Show current GitHub URL
        st.info(f"Using codebook from GitHub:\n{DEFAULT_CODEBOOK_URL}")
        
        if st.button("Refresh Codebook from GitHub"):
            with st.spinner("Fetching latest codebook from GitHub..."):
                # Force reload from GitHub
                codebook = load_codebook_comments(github_url=DEFAULT_CODEBOOK_URL, force_local=False)
                if codebook:
                    st.session_state.codebook_comments = codebook
                    st.success("Successfully refreshed codebook from GitHub!")
                    
                    # Save to local file as a backup
                    if save_codebook_comments(codebook):
                        st.info("Also saved a local backup of the codebook.")
        
        # Option to use a different GitHub URL
        custom_url = st.checkbox("Use custom GitHub URL")
        
        if custom_url:
            github_url = st.text_input(
                "GitHub Raw URL for codebook",
                value=DEFAULT_CODEBOOK_URL,
                help="Enter the raw GitHub URL for the codebook JSON file"
            )
            
            if st.button("Fetch from Custom URL"):
                with st.spinner("Fetching from custom GitHub URL..."):
                    codebook = load_codebook_comments(github_url=github_url, force_local=False)
                    if codebook:
                        st.session_state.codebook_comments = codebook
                        st.success("Successfully fetched codebook from custom URL!")
                        
                        # Save to local file as a backup
                        if save_codebook_comments(codebook):
                            st.info("Also saved a local backup of the codebook.")
        
        # Option to use local file only
        local_only = st.checkbox("Use local file only")
        
        if local_only and st.button("Load from Local File"):
            with st.spinner("Loading from local file..."):
                codebook = load_codebook_comments(force_local=True)
                if codebook:
                    st.session_state.codebook_comments = codebook
                    st.success("Successfully loaded codebook from local file!")

def render_how_to_tab():
    """Render the How-To tab content."""
    st.header("How to Use the Qualitative Coding Tool")
    
    st.markdown("""
    This super duper cool interface helps researchers test and refine codebook definitions for qualitative coding, with a twist of entertainment. Here's how to use the application:
    
    ### Workflow Overview
    
    1. **Prepare codebook**: Just simply go to the github repository and edit the codebook_enhanced.json there
    2. **Synchronize GitHub Codebook**: On the left you'll see a button "Refresh Codebook from GitHub". Press it to synchronize - you should see a message pop up underneath the button.
    3. **File processing**: This is just a testing feature for the backend pipeline logic, you can ignore this for now. It will likely be removed later.
    2. **Batch processing Documents**: Use batch processing for multiple documents
    3. **Review Results**: Examine output in the Results tab, and perform IRR calculations in the IRR analysis tab.
                
        - The main difference here is the results tab give you the raw JSONs for each submission for review

        - IRR analysis tab gives you the aggregated metric results from the analysis, as well as some visuals

    4. **Refine Codebook**: Make changes to codebook comments and reprocess as needed
        - This can be done either directly in the interface (hopefully it should work, haven't tested it)
        - Or via the github repository (this definitely works, simply use the synchronize button as described earlier)
    
    ### API Key Configuration 
    (**IGNORE THIS API-KEY SETUP, THIS ISN'T IMPLEMENTED CORRECTLY YET - THERE IS A DEFAULT KEY ALREADY ACTIVE, JUST RUN THE REST**)
    
    This tool uses Google's Gemini API to analyze PDF documents:
    
    1. **Enter in the sidebar**: Type your API key in the sidebar field (temporary, for this session only)
    
    You can obtain a Gemini API key from [Google AI Studio](https://makersuite.google.com/)
    
    ### GitHub Integration
    
    The codebook comments file can be synchronized with a GitHub repository (Default is GreenTrack, no need to enter it):
                
    (**You can ignore this for now - this is just placeholder functionality. Just use the button without entering anything**)
    1. Enable GitHub integration in the sidebar
    2. Enter the raw URL to the GitHub version of the file
    3. Click "Fetch from GitHub" to update your local version
    4. Process documents with the updated codebook
    
    ### Batch Processing (Recommended)
    
    (**The zip download hasn't been tested, but should work**)            

    For processing multiple documents at once:
    
    1. Go to the "Batch Processing" tab
    2. You can review the list of available PDF files
    3. Click "Process All Files" to analyze the entire set
    4. When complete, you can download a ZIP of all results or review individual files in the Results tab
    
    ### Reviewing Results
    
    In the "Results" tab:
    
    1. Select a processed file from the dropdown 
    2. Choose between Raw JSON view (complete data) or Tabular View (formatted for readability)
    3. Download results for further analysis if desired
    4. The IRR analysis tab provides with a better overview of the aggregated results, and agreement percentages
    
    ### Editing the Codebook
    
    To test different field definitions:
    
    1. Go to the "Codebook Editor" tab
    2. Modify the descriptions in the JSON editor
    3. Click "Save Changes" to update the file
    4. Return to Processing tabs to test the changes
    5. Let me know if this is broken, as I realize this will probably be easier to manage
                
    ### Future stuff:
    1. **Fix versioning logic** - currently we don't save between runs, so please download and maintain the codebook definitions as they run for now.
                I will try to sort out the logic asap
    2. Add a feedback mechanism for users (you lovely folk) to provide quicker feedback for updates
    3. Remove unused code categories - these are just an artifact of earlier experiments
    """)

def render_file_processing_tab():
    """Render the individual file processing tab."""
    st.header("Process Individual Files")
    
    st.info("""
    This tab allows you to process a single PDF file for testing purposes. 
    Select a file from the dropdown and click "Process File" to analyze it.
    The results will be saved to disk and can be viewed in the Results tab.
    """, icon="ℹ️")
    
    # API key is handled automatically in analyze_pdf_file
    
    codebook_template = load_codebook_template()
    if not codebook_template or not st.session_state.codebook_comments:
        st.warning("Missing codebook files. Please check that the required files exist.")
    else:
        # Get PDF files from the docs folder
        if os.path.isdir(DOCS_FOLDER):
            pdf_files = [f for f in os.listdir(DOCS_FOLDER) if f.lower().endswith(".pdf")]
            if pdf_files:
                selected_file = st.selectbox(
                    "Select a PDF file to process",
                    pdf_files,
                    index=None,
                    placeholder="Choose a file..."
                )
                
                if selected_file:
                    file_path = os.path.join(DOCS_FOLDER, selected_file)
                    
                    # Display file info
                    st.write(f"Selected file: **{selected_file}**")
                    
                    # Get file size
                    try:
                        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
                        st.write(f"File size: {file_size:.2f} MB")
                    except Exception as e:
                        st.error(f"Error getting file info: {e}")
                    
                    # Process button
                    if st.button("Process File"):
                        # API key handling is done within the function
                        result = analyze_pdf_file(
                            file_path, 
                            codebook_template, 
                            st.session_state.codebook_comments
                        )
                        
                        if result:
                            st.session_state.results[selected_file] = result
                            if selected_file not in st.session_state.processed_files:
                                st.session_state.processed_files.append(selected_file)
                            
                            # Save result to file
                            output_filename = os.path.splitext(file_path)[0] + "_codebook.json"
                            with open(output_filename, 'w', encoding="utf-8") as outfile:
                                json.dump(result, outfile, indent=2, ensure_ascii=False)
                            
                            st.success(f"Results saved to {os.path.basename(output_filename)}")
                            
                            # Display results
                            st.subheader("Results")
                            st.json(result)
                            
                            # Download button
                            st.download_button(
                                label="Download Results",
                                data=json.dumps(result, indent=2, ensure_ascii=False),
                                file_name=f"{os.path.splitext(selected_file)[0]}_codebook.json",
                                mime="application/json"
                            )
            else:
                st.warning(f"No PDF files found in the '{DOCS_FOLDER}' folder.")
        else:
            st.error(f"The '{DOCS_FOLDER}' folder does not exist. Please create it and add PDF files.")

def render_batch_processing_tab():
    """Render the batch processing tab."""
    st.header("Batch Process All Files")
    
    st.info("""
    This tab allows you to process all PDF files in the docs folder at once.
    This is the recommended approach for analyzing multiple documents efficiently.
    Results will be saved individually and can also be downloaded as a ZIP file when complete.
    """, icon="ℹ️")
    
    codebook_template = load_codebook_template()
    if not codebook_template or not st.session_state.codebook_comments:
        st.warning("Missing codebook files. Please check that the required files exist.")
    else:
        # Get PDF files from the docs folder
        if os.path.isdir(DOCS_FOLDER):
            pdf_files = [f for f in os.listdir(DOCS_FOLDER) if f.lower().endswith(".pdf")]
            if pdf_files:
                st.write(f"Found {len(pdf_files)} PDF files in the '{DOCS_FOLDER}' folder:")
                for file in pdf_files:
                    st.write(f"- {file}")
                
                if st.button("Process All Files"):
                    progress_bar = st.progress(0)
                    
                    results = {}
                    for i, filename in enumerate(pdf_files):
                        file_path = os.path.join(DOCS_FOLDER, filename)
                        st.write(f"Processing {filename} ({i+1}/{len(pdf_files)})")
                        
                        # API key handling is done within the function
                        result = analyze_pdf_file(
                            file_path, 
                            codebook_template, 
                            st.session_state.codebook_comments
                        )
                        
                        if result:
                            results[filename] = result
                            st.session_state.results[filename] = result
                            if filename not in st.session_state.processed_files:
                                st.session_state.processed_files.append(filename)
                            
                            # Save result to file
                            output_filename = os.path.splitext(file_path)[0] + "_codebook.json"
                            with open(output_filename, 'w', encoding="utf-8") as outfile:
                                json.dump(result, outfile, indent=2, ensure_ascii=False)
                            
                            st.success(f"Results saved to {os.path.basename(output_filename)}")
                        else:
                            st.error(f"Failed to process {filename}")
                        
                        # Update progress
                        progress_bar.progress((i + 1) / len(pdf_files))
                    
                    st.success(f"Batch processing complete. Processed {len(results)}/{len(pdf_files)} files.")
                    
                    # Create zip file with all results
                    if results:
                        zip_data = create_zip_from_results(results)
                        st.download_button(
                            label="Download All Results (ZIP)",
                            data=zip_data,
                            file_name="codebook_results.zip",
                            mime="application/zip"
                        )
            else:
                st.warning(f"No PDF files found in the '{DOCS_FOLDER}' folder.")
        else:
            st.error(f"The '{DOCS_FOLDER}' folder does not exist. Please create it and add PDF files.")

def render_results_viewer_tab():
    """Render the results viewer tab."""
    st.header("Results Viewer")
    
    st.info("""
    After processing files, use this tab to review the results.
    Select a file from the dropdown and choose your preferred view mode.
    You can download individual results as JSON files for further analysis.
    """, icon="ℹ️")
    
    if not st.session_state.processed_files:
        st.info("No files have been processed yet. Use the 'File Processing' or 'Batch Processing' tab to analyze files.")
    else:
        # File selector
        selected_file = st.selectbox(
            "Select a processed file to view",
            st.session_state.processed_files,
            index=None,
            placeholder="Choose a file..."
        )
        
        if selected_file and selected_file in st.session_state.results:
            st.subheader(f"Results for {selected_file}")
            
            # View options
            view_mode = st.radio(
                "View Mode",
                ["Raw JSON", "Tabular View"],
                horizontal=True
            )
            
            result = st.session_state.results[selected_file]
            
            if view_mode == "Raw JSON":
                st.json(result)
                
            elif view_mode == "Tabular View":
                # Create tabular view using DataFrame
                df = create_dataframe_from_json(result)
                if df is not None:
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error("Could not create tabular view. Showing raw JSON instead.")
                    st.json(result)
            
            # Download button
            st.download_button(
                label="Download Results",
                data=json.dumps(result, indent=2, ensure_ascii=False),
                file_name=f"{os.path.splitext(selected_file)[0]}_codebook.json",
                mime="application/json"
            )

def render_codebook_editor_tab():
    """Render the codebook editor tab."""
    st.header("Codebook Comments Editor")
    
    st.info("""
    This tab allows you to edit the codebook comments (codebook_finetune.json) which determine how information is extracted.
    Make changes to test different definitions, save them, and then process documents to see how the changes affect results.
    Changes are saved directly to the codebook_finetune.json file.
    """, icon="ℹ️")
    
    if not st.session_state.codebook_comments:
        st.warning("Codebook comments not loaded. Please check if codebook_finetune.json exists.")
    else:
        st.write("Edit the codebook comments to test different definitions and instructions:")
        
        # JSON editor for comments
        edited_comments = display_json_editor(st.session_state.codebook_comments, "codebook_comments")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Changes"):
                st.session_state.codebook_comments = edited_comments
                
                # Save to file
                if save_codebook_comments(edited_comments):
                    st.success("Changes saved successfully to codebook_finetune.json!")
                else:
                    st.error("Failed to save changes to file.")
        
        with col2:
            # Download button
            st.download_button(
                label="Download Edited Comments",
                data=json.dumps(edited_comments, indent=2, ensure_ascii=False),
                file_name="codebook_finetune_edited.json",
                mime="application/json"
            )

def render_audio_player_tab():
    """Render the audio player tab."""
    st.header("🎵 Project Soundtracks")
    
    st.markdown("""
    Take a break and enjoy music related to the project! You can play existing tracks or upload your own.
    
    Pre-made tracks were created using [Suno](https://suno.com), an AI music generation platform.
    """)
    
    # Create tabs for different audio player modes
    audio_tab1, audio_tab2 = st.tabs(["Play Existing Tracks", "Upload New Tracks"])
    
    # Tab for playing existing tracks
    with audio_tab1:
        st.subheader("Select a Track")
        
        # Check if audio folder exists and scan for MP3 files
        if os.path.isdir(AUDIO_FOLDER):
            mp3_files = [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith(".mp3")]
            
            if mp3_files:
                # Predefined songs with descriptions (for known songs)
                song_descriptions = {
                    "Pattern_Weavers.mp3": "Pattern Weavers - A melodic, slightly melancholic tune about ocean pollution",
                    "policy_jam.mp3": "Policy Jam - An upbeat track about environmental regulations"
                }
                
                # Function to get a description for any song
                def get_song_description(filename):
                    if filename in song_descriptions:
                        return song_descriptions[filename]
                    return filename  # Default to just showing the filename for uploaded songs
                
                # Display song selection and player
                selected_song = st.radio(
                    "Choose a song to play:",
                    mp3_files,
                    format_func=get_song_description
                )
                
                if selected_song:
                    # Play the selected song
                    st.audio(os.path.join(AUDIO_FOLDER, selected_song))
                    
                    # Display song info based on selection for predefined songs
                    if selected_song == "Pattern_Weavers.mp3":
                        st.info("🎵 This song reflects the journey of using computational methods to analyze plastic policy evolution over time.")
                    elif selected_song == "policy_jam.mp3":
                        st.info("🎵 The rhythm of this track follows the typical timeline of policy implementation!")
                    
                    # Load and display lyrics if available
                    lyrics = load_lyrics(selected_song, LYRICS_FOLDER)
                    
                    # Display lyrics if available
                    if lyrics:
                        st.subheader("Lyrics")
                        st.markdown(lyrics)
                    else:
                        st.info("No lyrics available for this track.")
            else:
                st.warning(f"No MP3 files found in the '{AUDIO_FOLDER}' folder.")
        else:
            st.error(f"The '{AUDIO_FOLDER}' folder does not exist.")
            
            # Button to create audio folder
            if st.button("Create Audio Folder"):
                try:
                    os.makedirs(AUDIO_FOLDER)
                    st.success(f"Created '{AUDIO_FOLDER}' folder successfully!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error creating folder: {e}")
    
    # Tab for uploading new tracks
    with audio_tab2:
        st.subheader("Upload Your Own Tracks")
        
        # Create columns for upload fields
        col1, col2 = st.columns(2)
        
        with col1:
            # Upload audio file
            uploaded_audio = st.file_uploader(
                "Upload an MP3 file", 
                type=["mp3"], 
                key="audio_uploader"
            )
            
            if uploaded_audio:
                st.success(f"Uploaded: {uploaded_audio.name}")
                
                # Preview the audio
                st.audio(uploaded_audio)
        
        with col2:
            # Text area for entering lyrics directly
            lyrics_text = st.text_area(
                "Enter lyrics (optional)",
                height=300,
                placeholder="Enter song lyrics here...\nYou can use Markdown formatting for better presentation.",
                help="You can use Markdown formatting like **bold**, *italics*, and ## headers"
            )
            
            if lyrics_text:
                with st.expander("Preview Lyrics", expanded=False):
                    st.markdown(lyrics_text)
        
        # Button to save uploaded files
        if uploaded_audio:
            if st.button("Save Track to Library"):
                # Create folders if they don't exist
                ensure_folders_exist([AUDIO_FOLDER, LYRICS_FOLDER])
                
                # Save audio file
                audio_saved = save_uploaded_file(uploaded_audio, AUDIO_FOLDER)
                
                # Save lyrics as file if provided
                lyrics_saved = True
                if lyrics_text:
                    # Create lyrics filename based on audio filename
                    base_name = os.path.splitext(uploaded_audio.name)[0]
                    lyrics_filename = f"{base_name}.md"
                    lyrics_path = os.path.join(LYRICS_FOLDER, lyrics_filename)
                    
                    try:
                        with open(lyrics_path, "w", encoding="utf-8") as f:
                            f.write(lyrics_text)
                    except Exception as e:
                        st.error(f"Error saving lyrics: {e}")
                        lyrics_saved = False
                
                if audio_saved and lyrics_saved:
                    st.success("Track saved successfully to the library!")
                    st.info("Switch to the 'Play Existing Tracks' tab to see and play your track.")
    
    # Attribution
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center;">
        <p>Pre-made tracks generated with <a href="https://suno.com" target="_blank">Suno AI</a></p>
        <small>These tracks are for entertainment purposes and are related to the research themes.</small>
    </div>
    """, unsafe_allow_html=True)

def render_results_viewer_tab():
    """Render the results viewer tab."""
    st.header("Results Viewer")
    
    st.info("""
    After processing files, use this tab to review the results.
    Select a file from the dropdown and choose your preferred view mode.
    You can download individual results as JSON files for further analysis.
    """, icon="ℹ️")
    
    if not st.session_state.processed_files:
        st.info("No files have been processed yet. Use the 'File Processing' or 'Batch Processing' tab to analyze files.")
    else:
        # File selector
        selected_file = st.selectbox(
            "Select a processed file to view",
            st.session_state.processed_files,
            index=None,
            placeholder="Choose a file..."
        )
        
        if selected_file and selected_file in st.session_state.results:
            st.subheader(f"Results for {selected_file}")
            
            # View options
            view_mode = st.radio(
                "View Mode",
                ["Raw JSON", "Tabular View"],
                horizontal=True
            )
            
            result = st.session_state.results[selected_file]
            
            if view_mode == "Raw JSON":
                st.json(result)
                
            elif view_mode == "Tabular View":
                # Create tabular view using DataFrame
                df = create_dataframe_from_json(result)
                if df is not None:
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error("Could not create tabular view. Showing raw JSON instead.")
                    st.json(result)
            
            # Download button
            st.download_button(
                label="Download Results",
                data=json.dumps(result, indent=2, ensure_ascii=False),
                file_name=f"{os.path.splitext(selected_file)[0]}_codebook.json",
                mime="application/json"
            )

def render_irr_analysis_tab():
    """Render the IRR Analysis tab."""
    st.header("IRR Analysis")

    st.info("""
    This tab runs Inter-Rater Reliability (IRR) analysis between LLM results and NVivo coding reference data.

    **Input Requirements:**
    1. **NVivo Data File:** Place your NVivo export file (CSV or Excel) named `nvivo_export.csv` in the main application directory (next to `app.py`).
    2. **LLM Processed JSON Files:** Ensure you have processed PDF documents using the 'File Processing' or 'Batch Processing' tabs. The resulting `_codebook.json` files should be located in the `docs` folder.

    The analysis uses Gwet's AC1 coefficient to measure agreement.
    """, icon="ℹ️")

    # Create output directory if it doesn't exist
    os.makedirs(RESULTS_FOLDER, exist_ok=True)

    # Check for required files
    nvivo_path = os.path.join("nvivo_export.csv")  # Path to existing NVivo file
    nvivo_exists = os.path.exists(nvivo_path)

    # Find all processed JSON files in docs folder
    json_files = []
    if os.path.exists(DOCS_FOLDER):
        for file in os.listdir(DOCS_FOLDER):
            if file.endswith("_codebook.json"):
                json_files.append(os.path.join(DOCS_FOLDER, file)) # Get full path

    # Status indicators
    st.subheader("Data Status")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### NVivo Reference Data")
        if nvivo_exists:
            st.success(f"✅ NVivo reference data found at `{nvivo_path}`")
        else:
            st.error(f"❌ NVivo reference data missing. Expected at `{nvivo_path}` in the application root directory.")

    with col2:
        st.markdown("### LLM Processed Data")

        # Check if any JSON files were found
        if not json_files:
            st.warning("⚠️ No processed JSON files found in `docs` folder")
            st.info("Use the 'File Processing' or 'Batch Processing' tab to analyze files first.")
        else:
            st.success(f"✅ Found {len(json_files)} processed JSON files in `docs` folder.")
            with st.expander("View processed files"):
                for file in json_files:
                    st.write(f"- {os.path.basename(file)}") # Just show filename

    # Run IRR analysis button - only if we have the NVivo data and at least one processed file
    should_run_analysis = False
    if nvivo_exists and json_files:
        should_run_analysis = st.button("Run IRR Analysis", key="run_irr_button")

        if should_run_analysis:
            if not json_files: # Double check in case files were removed since last check
                st.error("No processed JSON files found in 'docs' folder. Cannot run IRR analysis.")
            else:
                with st.spinner("Preparing LLM data and running IRR analysis..."):
                    try:
                        # 1. Process JSON files into a DataFrame
                        llm_data_df = process_json_files(json_files) # Use your existing function

                        if llm_data_df.empty:
                            st.error("Could not process JSON files into a usable DataFrame for IRR analysis.")
                            irr_results = None # Indicate failure
                        else:
                            # 2. Save DataFrame to a temporary CSV file
                            temp_llm_csv_path = os.path.join(RESULTS_FOLDER, "temp_llm_data.csv")
                            llm_data_df.to_csv(temp_llm_csv_path, index=False)

                            # 3. Run IRR analysis using the temporary CSV file
                            irr_results = run_irr_analysis_for_streamlit( # Now correctly calling streamlit version
                                llm_data_path=temp_llm_csv_path, # Pass path to the temp CSV
                                nvivo_data_path=nvivo_path,
                                output_dir=RESULTS_FOLDER
                            )
                            # Clean up temporary CSV (optional, but good practice)
                            # os.remove(temp_llm_csv_path) # Commented out for debugging - you can uncomment later

                        if irr_results:
                            # Store results in session state
                            st.session_state.irr_analysis = irr_results

                            st.success("IRR analysis completed successfully!")
                            # ... (rest of the result display logic - summary, visualizations, table, download - remains largely the same as before)
                            # ... (adjustments might be needed based on changes in run_irr_analysis_for_streamlit output if you made big changes)
                            # Show a summary of the results
                            st.subheader("Summary of IRR Analysis")

                            # Display summary metrics
                            if 'summary_data' in irr_results:
                                summary_data = irr_results['summary_data']
                                st.markdown("### Agreement Quality")

                                # Create metrics in a row
                                cols = st.columns(4)
                                with cols[0]:
                                    st.metric("Total Categories", summary_data['Total Categories'])
                                with cols[1]:
                                    st.metric("Excellent Agreement", summary_data['Excellent Agreement (AC1 ≥ 0.8)'])
                                with cols[2]:
                                    st.metric("Good Agreement", summary_data['Good Agreement (0.6 ≤ AC1 < 0.8)'])
                                with cols[3]:
                                    avg_ac1 = summary_data.get('Average AC1 Score')
                                    if avg_ac1:
                                        st.metric("Average AC1", f"{avg_ac1:.2f}")
                                    else:
                                        st.metric("Average AC1", "N/A")

                            # Display visualizations
                            if 'fig_data' in irr_results:
                                st.subheader("Visualizations")

                                tabs = st.tabs(["AC1 by Category", "Coding Prevalence", "Percent Agreement"])

                                with tabs[0]:
                                    if 'ac1_by_category' in irr_results['fig_data']:
                                        st.image(irr_results['fig_data']['ac1_by_category'])

                                with tabs[1]:
                                    if 'coding_prevalence' in irr_results['fig_data']:
                                        st.image(irr_results['fig_data']['coding_prevalence'])

                                with tabs[2]:
                                    if 'percent_agreement' in irr_results['fig_data']:
                                        st.image(irr_results['fig_data']['percent_agreement'])

                            # Display detailed results table
                            if 'report_df' in irr_results:
                                st.subheader("Detailed Results")
                                st.dataframe(irr_results['report_df'], use_container_width=True)

                            # Download buttons for results
                            if 'report_path' in irr_results and os.path.exists(irr_results['report_path']):
                                st.download_button(
                                    label="Download Report (Excel)",
                                    data=open(irr_results['report_path'], "rb").read(),
                                    file_name="irr_analysis_report.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                        else:
                            st.error("IRR Analysis Failed: `run_irr_analysis_for_streamlit` returned None. Check error messages above for details.")

                    except Exception as e:
                        st.error(f"Error preparing LLM data or running IRR analysis: {str(e)}")
                        st.error(f"Details: {traceback.format_exc()}")
                        irr_results = None # Ensure irr_results is None in case of exception

    elif not nvivo_exists:
        st.warning("NVivo reference data not found. Please check the file path.")
    elif not json_files:
        st.warning("No processed JSON files found. Process some files first before running analysis.")

    # Show previous results if available, but only if last analysis was successful
    if 'irr_analysis' in st.session_state and st.session_state.irr_analysis is not None and not should_run_analysis and st.session_state.irr_analysis: # Added check for non-None irr_analysis
        st.subheader("Previous IRR Analysis Results")

        irr_results = st.session_state.irr_analysis

        if irr_results: # Check again if irr_results is not None before proceeding
            # Display summary metrics
            if 'summary_data' in irr_results:
                summary_data = irr_results['summary_data']
                st.markdown("### Agreement Quality")

                # Create metrics in a row
                cols = st.columns(4)
                with cols[0]:
                    st.metric("Total Categories", summary_data.get('Total Categories', 'N/A'))
                with cols[1]:
                    st.metric("Excellent Agreement", summary_data.get('Excellent Agreement (AC1 ≥ 0.8)', 'N/A'))
                with cols[2]:
                    st.metric("Good Agreement", summary_data.get('Good Agreement (0.6 ≤ AC1 < 0.8)', 'N/A'))
                with cols[3]:
                    avg_ac1 = summary_data.get('Average AC1 Score')
                    if avg_ac1:
                        st.metric("Average AC1", f"{avg_ac1:.2f}")
                    else:
                        st.metric("Average AC1", "N/A")

            # Visualizations
            if 'fig_data' in irr_results:
                st.subheader("Visualizations")

                tabs = st.tabs(["AC1 by Category", "Coding Prevalence", "Percent Agreement"])

                fig_data = irr_results['fig_data']
                with tabs[0]:
                    if 'ac1_by_category' in fig_data:
                        st.image(fig_data['ac1_by_category'])
                    else:
                        st.info("AC1 by Category visualization not available")

                with tabs[1]:
                    if 'coding_prevalence' in fig_data:
                        st.image(fig_data['coding_prevalence'])
                    else:
                        st.info("Coding Prevalence visualization not available")

                with tabs[2]:
                    if 'percent_agreement' in fig_data:
                        st.image(fig_data['percent_agreement'])
                    else:
                        st.info("Percent Agreement visualization not available")

            # Detailed results table
            if 'report_df' in irr_results and irr_results['report_df'] is not None:
                st.subheader("Detailed Results")
                st.dataframe(irr_results['report_df'], use_container_width=True)

            # Download button
            if 'report_path' in irr_results and os.path.exists(irr_results['report_path']):
                st.download_button(
                    label="Download Report (Excel)",
                    data=open(irr_results['report_path'], "rb").read(),
                    file_name="irr_analysis_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("No previous IRR analysis results available or last analysis failed.")
