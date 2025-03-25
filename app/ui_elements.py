import streamlit as st
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
from gemini_calls import analyze_pdf_file

# Directory setup
DOCS_FOLDER = "docs"     # Folder containing PDF files to analyze
AUDIO_FOLDER = "audio"   # Folder containing MP3 files
LYRICS_FOLDER = "lyrics" # Folder containing lyric files

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
            help="Enter your Google Gemini API key. You can also store it in a .env file."
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
    This interface helps researchers test and refine codebook definitions for qualitative coding. Here's how to use each part of the application:
    
    ### Workflow Overview
    
    1. **Prepare Files**: Place PDF documents to analyze in the `docs` folder
    2. **Process Documents**: Use batch processing for multiple documents or individual processing for testing
    3. **Review Results**: Examine output in the Results tab
    4. **Refine Codebook**: Make changes to codebook comments and reprocess as needed
    
    ### API Key Configuration
    
    This tool uses Google's Gemini API to analyze PDF documents. You have multiple options for setting the API key:
    
    1. **Enter in the sidebar**: Type your API key in the sidebar field (temporary, for this session only)
    2. **Create a .env file**: Add a file named `.env` with the line `GOOGLE_API_KEY=your_key_here` 
    3. **Set environment variable**: Run `export GOOGLE_API_KEY=your_key_here` before starting the app
    
    You can obtain a Gemini API key from [Google AI Studio](https://makersuite.google.com/)
    
    ### GitHub Integration
    
    The codebook comments file (`codebook_finetune.json`) can be synchronized with a GitHub repository:
    
    1. Enable GitHub integration in the sidebar
    2. Enter the raw URL to the GitHub version of the file
    3. Click "Fetch from GitHub" to update your local version
    4. Process documents with the updated codebook
    
    ### Batch Processing (Recommended)
    
    For processing multiple documents at once:
    
    1. Go to the "Batch Processing" tab
    2. Review the list of available PDF files
    3. Click "Process All Files" to analyze the entire set
    4. When complete, download a ZIP of all results or review individual files in the Results tab
    
    ### Reviewing Results
    
    In the "Results" tab:
    
    1. Select a processed file from the dropdown 
    2. Choose between Raw JSON view (complete data) or Tabular View (formatted for readability)
    3. Download results for further analysis
    
    ### Editing the Codebook
    
    To test different field definitions:
    
    1. Go to the "Codebook Editor" tab
    2. Modify the descriptions in the JSON editor
    3. Click "Save Changes" to update the file
    4. Return to Processing tabs to test the changes
    
    ### Future Features
    
    - IRR (Inter-Rater Reliability) metrics will be added in a future update
    - Enhanced visualization options for results
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