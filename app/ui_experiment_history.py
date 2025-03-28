import streamlit as st
import pandas as pd
import os
import json
import datetime
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from PIL import Image

from versioning import (
    list_experiments, get_experiment, delete_experiment,
    apply_experiment_codebook, create_experiment_zip,
    compare_experiments
)

def format_timestamp(timestamp_str):
    """Format an ISO timestamp string to a more readable format."""
    try:
        dt = datetime.datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

def render_experiment_history_tab():
    """Render the Experiment History tab."""
    st.header("Experiment History")
    
    st.info("""
    This tab allows you to view, compare, and manage your past experiment runs.
    Each experiment stores the codebook configuration and results at the time of execution.
    """, icon="ℹ️")
    
    # Get list of experiments
    experiments = list_experiments()
    
    if not experiments:
        st.warning("No experiments found. Process some files first to create experiment history.")
        return
    
    # Create tabs for different views
    list_tab, compare_tab, details_tab = st.tabs(["Experiment List", "Compare Experiments", "Experiment Details"])
    
    # Experiment List tab
    with list_tab:
        st.subheader("All Experiments")
        
        # Create a DataFrame for better display
        exp_data = []
        for exp in experiments:
            exp_data.append({
                "ID": exp.get("id", "Unknown"),
                "Name": exp.get("name", ""),
                "Date": format_timestamp(exp.get("timestamp", "")),
                "Files Processed": exp.get("num_files", 0),
                "Notes": exp.get("notes", "")[:50] + ("..." if len(exp.get("notes", "")) > 50 else "")
            })
        
        if exp_data:
            exp_df = pd.DataFrame(exp_data)
            st.dataframe(exp_df, use_container_width=True)
            
            # Select an experiment for detailed view
            selected_exp_id = st.selectbox(
                "Select an experiment to view details:",
                [exp["ID"] for exp in exp_data],
                format_func=lambda x: f"{x} - {next((e['Name'] for e in exp_data if e['ID'] == x), '')}"
            )
            
            if selected_exp_id:
                # Store for details tab
                st.session_state.selected_experiment_id = selected_exp_id
                
                    # Export experiment as ZIP
                if st.button("Export Experiment", key="export_exp"):
                    zip_data = create_experiment_zip(selected_exp_id)
                    if zip_data:
                        # Create a download button
                        st.download_button(
                            label="Download Experiment ZIP",
                            data=zip_data,
                            file_name=f"{selected_exp_id}.zip",
                            mime="application/zip"
                        )
                    else:
                        st.error("Failed to create experiment ZIP file.")
                
                # Delete experiment option (with confirmation)
                with st.expander("Delete Experiment"):
                    st.warning("This action cannot be undone!")
                    delete_confirmation = st.text_input(
                        "Type the experiment ID to confirm deletion:", 
                        key="delete_confirmation"
                    )
                    
                    if st.button("Delete This Experiment", key="delete_exp"):
                        if delete_confirmation == selected_exp_id:
                            if delete_experiment(selected_exp_id):
                                st.success(f"Experiment {selected_exp_id} deleted successfully!")
                                st.session_state.pop('selected_experiment_id', None)
                                st.rerun()  # Refresh the page
                            else:
                                st.error("Failed to delete experiment.")
                        else:
                            st.error("Experiment ID doesn't match. Deletion cancelled.")
    
    # Compare Experiments tab
    with compare_tab:
        st.subheader("Compare Experiments")
        
        # Select two experiments to compare
        col1, col2 = st.columns(2)
        
        with col1:
            exp1_id = st.selectbox(
                "Select first experiment:",
                [exp["id"] for exp in experiments],
                format_func=lambda x: f"{x} - {next((e.get('name', '') for e in experiments if e.get('id', '') == x), '')}"
            )
            
        with col2:
            # Filter out the first selected experiment
            remaining_exps = [exp for exp in experiments if exp.get("id", "") != exp1_id]
            exp2_id = st.selectbox(
                "Select second experiment:",
                [exp["id"] for exp in remaining_exps] if remaining_exps else [""],
                format_func=lambda x: f"{x} - {next((e.get('name', '') for e in experiments if e.get('id', '') == x), '')}" if x else "Select an experiment"
            )
        
        if exp1_id and exp2_id:
            if st.button("Compare Experiments", key="compare_button"):
                comparison = compare_experiments(exp1_id, exp2_id)
                
                if comparison:
                    st.subheader("Comparison Results")
                    
                    # Show basic metadata
                    st.markdown("### Experiment Information")
                    
                    meta1 = comparison['metadata']['experiment1']
                    meta2 = comparison['metadata']['experiment2']
                    
                    meta_df = pd.DataFrame({
                        "Attribute": ["ID", "Name", "Date", "Files Processed", "Notes"],
                        "Experiment 1": [
                            meta1.get("id", ""),
                            meta1.get("name", ""),
                            format_timestamp(meta1.get("timestamp", "")),
                            meta1.get("num_files", 0),
                            meta1.get("notes", "")
                        ],
                        "Experiment 2": [
                            meta2.get("id", ""),
                            meta2.get("name", ""),
                            format_timestamp(meta2.get("timestamp", "")),
                            meta2.get("num_files", 0),
                            meta2.get("notes", "")
                        ]
                    })
                    
                    st.dataframe(meta_df, use_container_width=True)
                    
                    # Show IRR comparison if available
                    if 'irr_comparison' in comparison:
                        st.markdown("### IRR Score Comparison")
                        
                        irr_df = pd.DataFrame(comparison['irr_comparison'])
                        
                        # Clean up the DataFrame
                        irr_df = irr_df.rename(columns={
                            'Gwet AC1_1': 'Experiment 1 Score',
                            'Gwet AC1_2': 'Experiment 2 Score',
                            'Difference': 'Score Difference'
                        })
                        
                        # Color code the differences
                        def color_difference(val):
                            color = 'green' if val > 0 else 'red' if val < 0 else 'black'
                            return f'color: {color}'
                        
                        st.dataframe(
                            irr_df.style.applymap(
                                color_difference, 
                                subset=['Score Difference']
                            ),
                            use_container_width=True
                        )
                        
                        # Create visualization of differences
                        if not irr_df.empty and 'Score Difference' in irr_df.columns:
                            # Filter out rows with NaN differences
                            plot_df = irr_df.dropna(subset=['Score Difference'])
                            
                            if not plot_df.empty:
                                fig, ax = plt.subplots(figsize=(10, 6))
                                
                                categories = plot_df['Category']
                                differences = plot_df['Score Difference']
                                
                                # Create bar chart
                                bars = ax.barh(categories, differences)
                                
                                # Color bars based on value
                                for i, bar in enumerate(bars):
                                    bar.set_color('green' if differences.iloc[i] > 0 else 'red')
                                
                                # Add a reference line at 0
                                ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
                                
                                # Add labels
                                ax.set_xlabel('Score Difference (Experiment 2 - Experiment 1)')
                                ax.set_title('Changes in IRR Scores Between Experiments')
                                
                                # Add value labels
                                for i, diff in enumerate(differences):
                                    ax.text(
                                        diff + (0.01 if diff >= 0 else -0.03), 
                                        i, 
                                        f'{diff:.3f}', 
                                        va='center'
                                    )
                                
                                plt.tight_layout()
                                
                                # Display plot in Streamlit
                                st.pyplot(fig)
                                
                                # Calculate overall statistics
                                improved = sum(1 for diff in differences if diff > 0)
                                declined = sum(1 for diff in differences if diff < 0)
                                unchanged = sum(1 for diff in differences if diff == 0)
                                
                                st.markdown(f"""
                                **Summary**: 
                                - Categories improved: {improved}
                                - Categories declined: {declined}
                                - Categories unchanged: {unchanged}
                                - Average change: {differences.mean():.3f}
                                - Maximum improvement: {differences.max():.3f}
                                - Maximum decline: {differences.min():.3f}
                                """)
                else:
                    st.error("Failed to compare experiments. Make sure both experiments have data.")
    
    # Experiment Details tab
    with details_tab:
        st.subheader("Experiment Details")
        
        # Check if we have a selected experiment from the list tab
        selected_exp_id = st.session_state.get('selected_experiment_id')
        
        if not selected_exp_id:
            # If not, provide a selector
            selected_exp_id = st.selectbox(
                "Select an experiment to view:",
                [exp.get("id", "") for exp in experiments],
                format_func=lambda x: f"{x} - {next((e.get('name', '') for e in experiments if e.get('id', '') == x), '')}"
            )
        
        if selected_exp_id:
            # Load the experiment data
            experiment = get_experiment(selected_exp_id)
            
            if experiment and 'metadata' in experiment:
                metadata = experiment['metadata']
                
                # Display basic information
                st.markdown(f"### {metadata.get('name', 'Unnamed Experiment')}")
                st.markdown(f"**ID:** {metadata.get('id', 'Unknown')}")
                st.markdown(f"**Date:** {format_timestamp(metadata.get('timestamp', ''))}")
                st.markdown(f"**Files Processed:** {metadata.get('num_files', 0)}")
                
                if 'notes' in metadata and metadata['notes']:
                    st.markdown("**Notes:**")
                    st.markdown(metadata['notes'])
                
                # Show tabs for different aspects of the experiment
                result_tab, irr_tab, codebook_tab = st.tabs(["Results", "IRR Analysis", "Codebook"])
                
                # Results tab
                with result_tab:
                    if 'results' in experiment and experiment['results']:
                        st.subheader("Processed Results")
                        
                        # Select a result file to view
                        result_files = list(experiment['results'].keys())
                        selected_result = st.selectbox("Select a result file:", result_files)
                        
                        if selected_result:
                            result_data = experiment['results'][selected_result]
                            
                            # Display options
                            view_mode = st.radio(
                                "View Mode",
                                ["Raw JSON", "Pretty View"],
                                horizontal=True
                            )
                            
                            if view_mode == "Raw JSON":
                                st.json(result_data)
                            else:
                                # Create a prettier view (simplified for this example)
                                st.write("Result Overview:")
                                
                                # Extract key information
                                if isinstance(result_data, dict):
                                    # Create sections for different parts of the data
                                    if 'submission_metadata' in result_data:
                                        st.write("**Submission Metadata:**")
                                        for key, value in result_data['submission_metadata'].items():
                                            if isinstance(value, dict) and 'value' in value:
                                                display_val = value['value']
                                            else:
                                                display_val = value
                                            st.write(f"- {key.capitalize()}: {display_val}")
                                    
                                    # Show a list of keys at the top level
                                    top_level_keys = list(result_data.keys())
                                    if top_level_keys:
                                        st.write("**Sections in this result:**")
                                        st.write(", ".join(top_level_keys))
                    else:
                        st.info("No result data found for this experiment.")
                
                # IRR Analysis tab
                with irr_tab:
                    if 'irr_report_df' in experiment:
                        st.subheader("IRR Analysis Results")
                        
                        # Display the IRR report dataframe
                        st.dataframe(experiment['irr_report_df'], use_container_width=True)
                        
                        # Show IRR plots if available
                        for img_name in ["ac1_by_category.png", "coding_prevalence.png", "percent_agreement.png"]:
                            img_path = os.path.join("experiments", selected_exp_id, img_name)
                            if os.path.exists(img_path):
                                st.subheader(img_name.replace(".png", "").replace("_", " ").title())
                                st.image(img_path)
                    else:
                        st.info("No IRR analysis data found for this experiment.")
                
                # Codebook tab
                with codebook_tab:
                    st.subheader("Codebook Used")
                    
                    if 'codebook' in experiment:
                        st.json(experiment['codebook'])
                    else:
                        # For backward compatibility
                        if 'codebook_finetuned' in experiment:
                            st.json(experiment['codebook_finetuned'])
                        else:
                            st.info("No codebook data found for this experiment.")
            else:
                st.error("Failed to load experiment data.")

def save_current_experiment(results, notes="", name=""):
    """
    Save the current experiment state including codebook and results.
    
    Parameters:
    -----------
    results : dict
        Dictionary of processed results
    notes : str
        Optional notes about the experiment
    name : str
        Optional name for the experiment
        
    Returns:
    --------
    str
        ID of the saved experiment
    """
    # Get current codebook (prioritize from session state, then file)
    codebook = None
    
    # First try to get from session state
    if 'codebook_comments' in st.session_state:
        codebook = st.session_state.codebook_comments
    
    # If not in session state, try to load from file
    if not codebook:
        try:
            with open("codebook_finetune.json", 'r', encoding='utf-8') as f:
                codebook = json.load(f)
        except Exception as e:
            st.error(f"Error loading codebook: {e}")
            return None
    
    # Save the experiment
    from versioning import save_experiment
    experiment_id = save_experiment(
        results=results,
        codebook=codebook,
        notes=notes,
        name=name
    )
    
    return experiment_id
