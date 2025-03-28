import os
import json
import time
import datetime
import shutil
import pandas as pd
import streamlit as st
from pathlib import Path
import zipfile
import io

# Directory for storing experiment versions
EXPERIMENTS_DIR = "experiments"

def ensure_experiments_dir():
    """Ensure the experiments directory exists."""
    if not os.path.exists(EXPERIMENTS_DIR):
        os.makedirs(EXPERIMENTS_DIR)
        return True
    return False

def generate_experiment_id():
    """Generate a unique experiment ID based on timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"exp_{timestamp}"

def save_experiment(results, codebook, notes="", name=""):
    """
    Save an experiment with its associated codebook and metadata.
    
    Parameters:
    -----------
    results : dict
        A dictionary mapping filenames to their processed results
    codebook : dict
        The codebook used for the experiment
    notes : str
        User notes about the experiment
    name : str
        Optional user-provided name for the experiment
    
    Returns:
    --------
    str
        The ID of the saved experiment
    """
    ensure_experiments_dir()
    
    # Generate experiment ID if no name provided
    if not name:
        experiment_id = generate_experiment_id()
    else:
        # Use name but ensure it's safe for filenames
        safe_name = "".join([c if c.isalnum() or c in ['-', '_'] else '_' for c in name])
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        experiment_id = f"{timestamp}_{safe_name}"
    
    # Create experiment directory
    experiment_dir = os.path.join(EXPERIMENTS_DIR, experiment_id)
    os.makedirs(experiment_dir, exist_ok=True)
    
    # Save metadata
    metadata = {
        "id": experiment_id,
        "name": name,
        "timestamp": datetime.datetime.now().isoformat(),
        "notes": notes,
        "files_processed": list(results.keys()),
        "num_files": len(results)
    }
    
    with open(os.path.join(experiment_dir, "metadata.json"), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    
    # Save codebook (single file)
    with open(os.path.join(experiment_dir, "codebook.json"), 'w', encoding='utf-8') as f:
        json.dump(codebook, f, indent=4, ensure_ascii=False)
    
    # Save individual results
    results_dir = os.path.join(experiment_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    for filename, result in results.items():
        result_filename = os.path.splitext(filename)[0] + "_codebook.json"
        with open(os.path.join(results_dir, result_filename), 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
    
    # Copy IRR analysis if available
    irr_report_path = os.path.join("results", "irr_analysis_report.xlsx")
    if os.path.exists(irr_report_path):
        shutil.copy(irr_report_path, os.path.join(experiment_dir, "irr_analysis_report.xlsx"))
    
    for img_name in ["ac1_by_category.png", "coding_prevalence.png", "percent_agreement.png"]:
        img_path = os.path.join("results", img_name)
        if os.path.exists(img_path):
            shutil.copy(img_path, os.path.join(experiment_dir, img_name))
    
    return experiment_id

def list_experiments():
    """
    List all saved experiments.
    
    Returns:
    --------
    list
        List of experiment metadata dictionaries, sorted by timestamp (newest first)
    """
    ensure_experiments_dir()
    
    experiments = []
    for exp_dir in os.listdir(EXPERIMENTS_DIR):
        metadata_path = os.path.join(EXPERIMENTS_DIR, exp_dir, "metadata.json")
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    experiments.append(metadata)
            except Exception as e:
                print(f"Error reading metadata for {exp_dir}: {e}")
    
    # Sort by timestamp (newest first)
    experiments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return experiments

def get_experiment(experiment_id):
    """
    Load a specific experiment by ID.
    
    Parameters:
    -----------
    experiment_id : str
        The ID of the experiment to load
    
    Returns:
    --------
    dict
        A dictionary containing all experiment data including metadata, codebook, and results
    """
    experiment_dir = os.path.join(EXPERIMENTS_DIR, experiment_id)
    
    if not os.path.exists(experiment_dir):
        return None
    
    experiment_data = {}
    
    # Load metadata
    metadata_path = os.path.join(experiment_dir, "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            experiment_data['metadata'] = json.load(f)
    
    # Load codebook (try new format first, then old for backward compatibility)
    codebook_path = os.path.join(experiment_dir, "codebook.json")
    if os.path.exists(codebook_path):
        with open(codebook_path, 'r', encoding='utf-8') as f:
            experiment_data['codebook'] = json.load(f)
    else:
        # For backward compatibility
        codebook_finetuned_path = os.path.join(experiment_dir, "codebook_finetuned.json")
        if os.path.exists(codebook_finetuned_path):
            with open(codebook_finetuned_path, 'r', encoding='utf-8') as f:
                experiment_data['codebook'] = json.load(f)
    
    # Load results
    results_dir = os.path.join(experiment_dir, "results")
    if os.path.exists(results_dir):
        experiment_data['results'] = {}
        for result_file in os.listdir(results_dir):
            if result_file.endswith(".json"):
                with open(os.path.join(results_dir, result_file), 'r', encoding='utf-8') as f:
                    experiment_data['results'][result_file] = json.load(f)
    
    # Load IRR analysis
    irr_report_path = os.path.join(experiment_dir, "irr_analysis_report.xlsx")
    if os.path.exists(irr_report_path):
        experiment_data['irr_report_path'] = irr_report_path
        try:
            experiment_data['irr_report_df'] = pd.read_excel(irr_report_path)
        except Exception as e:
            print(f"Error loading IRR report for {experiment_id}: {e}")
    
    return experiment_data

def delete_experiment(experiment_id):
    """
    Delete an experiment.
    
    Parameters:
    -----------
    experiment_id : str
        The ID of the experiment to delete
        
    Returns:
    --------
    bool
        True if deletion was successful, False otherwise
    """
    experiment_dir = os.path.join(EXPERIMENTS_DIR, experiment_id)
    
    if not os.path.exists(experiment_dir):
        return False
    
    try:
        shutil.rmtree(experiment_dir)
        return True
    except Exception as e:
        print(f"Error deleting experiment {experiment_id}: {e}")
        return False

def apply_experiment_codebook(experiment_id):
    """
    Apply codebook from a specific experiment to the current session.
    
    Parameters:
    -----------
    experiment_id : str
        The ID of the experiment whose codebook to apply
        
    Returns:
    --------
    dict
        Codebook loaded from the experiment
    """
    experiment_dir = os.path.join(EXPERIMENTS_DIR, experiment_id)
    
    codebook = None
    
    # Try the new single codebook format first
    codebook_path = os.path.join(experiment_dir, "codebook.json")
    if os.path.exists(codebook_path):
        with open(codebook_path, 'r', encoding='utf-8') as f:
            codebook = json.load(f)
    # For backward compatibility, try the old format
    else:
        codebook_finetuned_path = os.path.join(experiment_dir, "codebook_finetuned.json")
        if os.path.exists(codebook_finetuned_path):
            with open(codebook_finetuned_path, 'r', encoding='utf-8') as f:
                codebook = json.load(f)
    
    return codebook

def create_experiment_zip(experiment_id):
    """
    Create a ZIP file containing all files for an experiment.
    
    Parameters:
    -----------
    experiment_id : str
        The ID of the experiment to export
        
    Returns:
    --------
    bytes
        ZIP file content as bytes
    """
    experiment_dir = os.path.join(EXPERIMENTS_DIR, experiment_id)
    
    if not os.path.exists(experiment_dir):
        return None
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(experiment_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, EXPERIMENTS_DIR)
                zip_file.write(file_path, rel_path)
    
    return zip_buffer.getvalue()

def compare_experiments(experiment_id1, experiment_id2):
    """
    Compare two experiments and identify differences.
    
    Parameters:
    -----------
    experiment_id1 : str
        The ID of the first experiment to compare
    experiment_id2 : str
        The ID of the second experiment to compare
        
    Returns:
    --------
    dict
        A dictionary containing comparison results
    """
    exp1 = get_experiment(experiment_id1)
    exp2 = get_experiment(experiment_id2)
    
    if not exp1 or not exp2:
        return None
    
    comparison = {
        "metadata": {
            "experiment1": exp1.get('metadata', {}),
            "experiment2": exp2.get('metadata', {})
        },
        "codebook_diffs": {},
        "result_diffs": {}
    }
    
    # Compare IRR results if available
    if 'irr_report_df' in exp1 and 'irr_report_df' in exp2:
        try:
            irr1 = exp1['irr_report_df']
            irr2 = exp2['irr_report_df']
            
            # Assuming both have 'Category' and 'Gwet AC1' columns
            merged = pd.merge(
                irr1[['Category', 'Gwet AC1']], 
                irr2[['Category', 'Gwet AC1']], 
                on='Category', 
                how='outer',
                suffixes=('_1', '_2')
            )
            
            merged['Difference'] = merged['Gwet AC1_2'] - merged['Gwet AC1_1']
            comparison['irr_comparison'] = merged.to_dict(orient='records')
        except Exception as e:
            print(f"Error comparing IRR results: {e}")
    
    return comparison
