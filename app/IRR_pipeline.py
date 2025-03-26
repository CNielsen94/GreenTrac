import json
import pandas as pd
import numpy as np

import seaborn as sns
import os
import re
import traceback
from pathlib import Path
import matplotlib.pyplot as plt
from pathlib import Path


print("Script starting...")

def safe_extract_value(data, *keys, default=None):
    """
    Safely extract values from nested dictionaries, handling both direct values and {value, location, reasoning} structures.
    
    Parameters:
    -----------
    data : dict
        Dictionary to extract value from
    *keys : list
        Keys to navigate through the nested dictionary
    default : any
        Default value to return if key doesn't exist
        
    Returns:
    --------
    The extracted value or default
    """
    try:
        current = data
        for key in keys[:-1]:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        # Last key processing
        last_key = keys[-1]
        if isinstance(current, dict) and last_key in current:
            item = current[last_key]
            
            # Handle both direct values and {value, location, reasoning} structures
            if isinstance(item, dict) and 'value' in item:
                return item['value']
            else:
                return item
        else:
            return default
    except Exception:
        return default

def get_json_files(directory='docs'):
    """
    Returns a list of all JSON files in the specified directory.
    
    Parameters:
    -----------
    directory : str
        Path to the directory to search (default: 'docs')
        
    Returns:
    --------
    list
        List of full file paths to all JSON files in the directory
    """
    json_files = []
    
    # Check if the directory exists
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return json_files
    
    # Walk through the directory and find all JSON files
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.json'):
                # Get full path
                file_path = os.path.join(root, file)
                json_files.append(file_path)
    
    print(f"Found {len(json_files)} JSON files in {directory}.")
    return json_files

def process_json_files(file_paths_or_path):
    """
    Process one or multiple JSON files and convert them into a structured DataFrame.
    
    Parameters:
    -----------
    file_paths_or_path : list or str
        List of file paths to the JSON files or a single file path
        
    Returns:
    --------
    pd.DataFrame
        DataFrame containing the extracted data from all JSON files
    """
    # List to store data from each file
    all_data = []
    
    # Handle different input types
    if isinstance(file_paths_or_path, str):
        file_paths = [file_paths_or_path]
    else:
        file_paths = file_paths_or_path
    
    # Process each file
    for file_path in file_paths:
        try:
            # Load JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                data = json.loads(file_content)
            
            # Extract country name
            country = safe_extract_value(data, 'submission_metadata', 'country', default='Unknown')
            print(f"Processing country: {country}")
            
            # Create a dictionary for this country's data
            country_data = {'country': country}
            
            # Extract objectives data
            # C1: End plastic pollution
            end_pollution_mentioned = safe_extract_value(data, 'objectives', 'end_plastic_pollution', 'mentioned', default=False)
            end_pollution_timeframe = safe_extract_value(data, 'objectives', 'end_plastic_pollution', 'timeframe_specified', default=False)
            
            country_data['A : C1 Objectives - end plastic pollution'] = end_pollution_mentioned
            country_data['B : Mentioned with time frame'] = end_pollution_mentioned and end_pollution_timeframe
            country_data['C : Mentioned, no time frame'] = end_pollution_mentioned and not end_pollution_timeframe
            country_data['D : Not mentioned'] = not end_pollution_mentioned
            
            # C2: Reduce production of plastics
            reduce_production_mentioned = safe_extract_value(data, 'objectives', 'reduce_production', 'mentioned', default=False)
            reduce_production_spec = safe_extract_value(data, 'objectives', 'reduce_production', 'specification_provided', default=False)
            
            country_data['E : C2 Objectives - reduce production of plastics'] = reduce_production_mentioned
            country_data['F : Mentioned with specification'] = reduce_production_mentioned and reduce_production_spec
            country_data['G : Mentioned, no specification'] = reduce_production_mentioned and not reduce_production_spec
            country_data['H : Not mentioned'] = not reduce_production_mentioned
            
            # C3: Benefits of plastics
            benefits_mentioned = safe_extract_value(data, 'objectives', 'benefits_of_plastics', 'mentioned', default=False)
            
            country_data['I : C3 Objectives - benefits of plastics'] = benefits_mentioned
            country_data['J : Mentioned'] = benefits_mentioned
            country_data['K : Not mentioned'] = not benefits_mentioned
            
            # C4: Protect human health
            health_mentioned = safe_extract_value(data, 'objectives', 'protect_human_health', 'mentioned', default=False)
            
            country_data['L : C4 Objectives - protect human health'] = health_mentioned
            country_data['M : Mentioned'] = health_mentioned
            country_data['N : Not mentioned'] = not health_mentioned
            
            # C5: Protect biodiversity
            biodiversity_mentioned = safe_extract_value(data, 'objectives', 'protect_biodiversity', 'mentioned', default=False)
            
            country_data['O : C5 Objectives - protect biodiversity and (marine) environment'] = biodiversity_mentioned
            country_data['P : Mentioned'] = biodiversity_mentioned
            country_data['Q : Not mentioned'] = not biodiversity_mentioned
            
            # C10: Time horizon of implementation
            timeframe_specified = safe_extract_value(data, 'implementation', 'timeframe', 'specified', default=False)
            
            country_data['R : C10 Time horizon of implementation'] = True
            country_data['S : Not relevant'] = False
            country_data['T : Not specified'] = not timeframe_specified
            country_data['U : Specified'] = timeframe_specified
            
            # C11: Stringency of measure
            stringency_level = safe_extract_value(data, 'implementation', 'stringency', 'level', default='')
            
            country_data['V : C11 Stringency of measure'] = True
            country_data['W : High'] = stringency_level == 'High'
            country_data['X : Low'] = stringency_level == 'Low'
            country_data['Y : Non relevant'] = stringency_level == ''
            
            # C6: Addressing the full life cycle of plastics
            lifecycle_mentioned = safe_extract_value(data, 'objectives', 'lifecycle_approach', 'mentioned', default=False)
            lifecycle_coverage = safe_extract_value(data, 'objectives', 'lifecycle_approach', 'coverage', default='')
            
            country_data['Z : C6 Objectives - addressing the full life cycle of plastics'] = lifecycle_mentioned
            country_data['AA : Mentioned'] = lifecycle_mentioned and lifecycle_coverage == 'Full lifecycle'
            country_data['AB : Not mentioned'] = not lifecycle_mentioned
            country_data['AC : Partial mention'] = lifecycle_mentioned and lifecycle_coverage != 'Full lifecycle'
            
            # C7: Other objectives
            other_objectives = safe_extract_value(data, 'objectives', 'other_objectives', default=[])
            # Make sure it's a list even if a dict was returned
            if not isinstance(other_objectives, list):
                other_objectives = []
                
            has_other_objectives = len(other_objectives) > 0
            
            # Extract specific objectives - safely handle if items are dicts with 'value' keys
            def check_if_contains(obj_list, keyword):
                for obj in obj_list:
                    value = obj.get('value', obj) if isinstance(obj, dict) else obj
                    if isinstance(value, str) and keyword in value.lower():
                        return True
                return False
            
            has_circular_economy = check_if_contains(other_objectives, 'circular')
            has_climate_change = check_if_contains(other_objectives, 'climate')
            has_esm = check_if_contains(other_objectives, 'sound management')
            has_sustainable_production = check_if_contains(other_objectives, 'sustainable production')
            
            country_data['AD : C7 Objectives - other objectives'] = has_other_objectives
            country_data['AE : Circular economy'] = has_circular_economy
            country_data['AF : Climate change'] = has_climate_change
            country_data['AG : ESM'] = has_esm
            country_data['AH : Mentioned'] = has_other_objectives
            country_data['AI : Not mentioned'] = not has_other_objectives
            country_data['AJ : Sustainable production'] = has_sustainable_production
            
            # C8: Value chain
            upstream_feedstock = safe_extract_value(data, 'value_chain', 'upstream', 'feedstock', 'mentioned', default=False)
            upstream_production = safe_extract_value(data, 'value_chain', 'upstream', 'production', 'mentioned', default=False)
            upstream_mentioned = upstream_feedstock or upstream_production
            
            midstream_design = safe_extract_value(data, 'value_chain', 'midstream', 'design', 'mentioned', default=False)
            midstream_product = safe_extract_value(data, 'value_chain', 'midstream', 'product_production', 'mentioned', default=False)
            midstream_distribution = safe_extract_value(data, 'value_chain', 'midstream', 'distribution', 'mentioned', default=False)
            midstream_consumption = safe_extract_value(data, 'value_chain', 'midstream', 'consumption', 'mentioned', default=False)
            midstream_mentioned = midstream_design or midstream_product or midstream_distribution or midstream_consumption
            
            downstream_collection = safe_extract_value(data, 'value_chain', 'downstream', 'collection', 'mentioned', default=False)
            downstream_waste = safe_extract_value(data, 'value_chain', 'downstream', 'waste_management', 'mentioned', default=False)
            downstream_recycling = safe_extract_value(data, 'value_chain', 'downstream', 'recycling', 'mentioned', default=False)
            downstream_legacy = safe_extract_value(data, 'value_chain', 'downstream', 'legacy_plastic', 'mentioned', default=False)
            downstream_mentioned = downstream_collection or downstream_waste or downstream_recycling or downstream_legacy
            
            cross_emissions = safe_extract_value(data, 'value_chain', 'cross_value_chain', 'emissions', 'mentioned', default=False)
            cross_microplastic = safe_extract_value(data, 'value_chain', 'cross_value_chain', 'microplastic_leakage', 'mentioned', default=False)
            cross_mentioned = cross_emissions or cross_microplastic
            
            country_data['AK : C8 Value chain'] = True
            country_data['AL : 1. Upstream'] = upstream_mentioned
            country_data['AM : 2. Midstream'] = midstream_mentioned
            country_data['AN : 3. Downstream'] = downstream_mentioned
            country_data['AO : 4. Cross value chain'] = cross_mentioned
            
            # C9: Type of measure
            has_targets = safe_extract_value(data, 'measures', 'targets', 'present', default=False)
            
            # Check for instruments - safely with checking dict paths
            def has_any_instruments(data, category, instrument_keys):
                if not isinstance(data, dict) or 'measures' not in data:
                    return False
                measures = data['measures']
                if not isinstance(measures, dict) or category not in measures:
                    return False
                category_data = measures[category]
                if not isinstance(category_data, dict):
                    return False
                    
                for key in instrument_keys:
                    if key in category_data:
                        instr_data = category_data[key]
                        if isinstance(instr_data, dict) and 'mentioned' in instr_data:
                            mentioned = instr_data['mentioned']
                            if isinstance(mentioned, dict) and 'value' in mentioned:
                                if mentioned['value']:
                                    return True
                            elif mentioned:
                                return True
                return False
            
            economic_instrument_keys = ['tax_incentives', 'subsidies', 'penalties', 'trading_systems', 
                                       'deposit_systems', 'public_procurement', 'rd_funding']
            economic_instruments = has_any_instruments(data, 'economic_instruments', economic_instrument_keys)
            
            regulatory_instrument_keys = ['bans', 'moratoriums', 'performance_standards', 'mandatory_infrastructure',
                                         'certification', 'labelling', 'action_plans', 'reporting', 
                                         'trade_requirements', 'epr', 'just_transition']
            regulatory_instruments = has_any_instruments(data, 'regulatory_instruments', regulatory_instrument_keys)
            
            soft_instrument_keys = ['voluntary_certification', 'voluntary_labelling', 'monitoring', 
                                    'information_guidance', 'education', 'expert_groups', 'research_promotion', 
                                    'harmonization', 'knowledge_sharing']
            soft_instruments = has_any_instruments(data, 'soft_instruments', soft_instrument_keys)
            
            has_instruments = economic_instruments or regulatory_instruments or soft_instruments
            
            country_data['AP : C9 Type of measure'] = has_instruments or has_targets
            country_data['AQ : Instrument'] = has_instruments
            country_data['AR : Target'] = has_targets
            
            # Add data to our list
            all_data.append(country_data)
            print(f"Successfully processed {country}")
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in file {file_path}: {e}")
            print(f"First 100 characters of file: {file_content[:100] if 'file_content' in locals() else 'Not available'}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            traceback.print_exc()
    
    # Convert to DataFrame
    if all_data:
        df = pd.DataFrame(all_data)
        return df
    else:
        print("No data was successfully processed.")
        return pd.DataFrame()

def run_extraction(directory='docs', output_file='country_submissions_analysis.xlsx'):
    """
    Run the extraction process on all JSON files in a directory and save results to Excel.
    
    Parameters:
    -----------
    directory : str
        Path to the directory containing JSON files
    output_file : str
        Path to the output Excel file
    
    Returns:
    --------
    pd.DataFrame
        DataFrame containing the extracted data
    """
    print(f"Starting extraction process on directory: {directory}")
    
    # Get all JSON files
    json_files = get_json_files(directory)
    
    if not json_files:
        print("No JSON files found. Cannot proceed.")
        return None
    
    # Process all JSON files
    df = process_json_files(json_files)
    
    if df is not None and not df.empty:
        # Save to Excel
        df.to_excel(output_file, index=False)
        print(f"Results saved to {output_file}")
        
        # Print some statistics
        print(f"\nExtraction Results:")
        print(f"Total countries processed: {len(df)}")
        print(f"Columns in output: {len(df.columns)}")
    
    return df

def map_country_names(df_llm):
    """
    Maps country names in the LLM dataframe to match the Nvivo format.
    
    Parameters:
    -----------
    df_llm : pandas.DataFrame
        Dataframe containing LLM-generated data with country names
        
    Returns:
    --------
    pandas.DataFrame
        A copy of the dataframe with updated country names
    """
    # Create a dictionary mapping LLM country names to Nvivo format
    country_mapping = {
        'United States of America': '11 : USA',
        'Bosnia and Herzegovina': '2 : Bosnia and Herzegovina',
        'Saudi Arabia': '9 : Saudi Arabia',
        'Principality of Monaco': '7 : Monaco',
        'Islamic Republic of Iran': '6 : Iran',
        'Cambodia': '4 : Cambodia',
        'Brazil': '3 : Brazil',
        'The Russian Federation': '8 : Russia',
        'URUGUAY': '10 : Uruguay',
        'COOK ISLANDS': '5 : Cook Islands',
        'European Union': '1 : EU'
    }
    
    # Create a copy of the original dataframe
    df_mapped = df_llm.copy()
    
    # Apply the mapping to the country column
    df_mapped['country'] = df_mapped['country'].map(country_mapping).fillna(df_mapped['country'])
    
    return df_mapped

def reorder_to_match(df_to_reorder, reference_df):
    """
    Reorders a dataframe to match the country order of a reference dataframe.
    
    Parameters:
    -----------
    df_to_reorder : pandas.DataFrame
        The dataframe to reorder
    reference_df : pandas.DataFrame
        The reference dataframe with the desired country order
        
    Returns:
    --------
    pandas.DataFrame
        The reordered dataframe
    """
    # Get the ordered list of countries from the reference dataframe
    country_order = reference_df['country'].tolist()
    
    # Create a categorical column with the specified order
    df_result = df_to_reorder.copy()
    df_result['country'] = pd.Categorical(df_result['country'], categories=country_order, ordered=True)
    
    # Sort by the categorical column and reset index
    result = df_result.sort_values('country').reset_index(drop=True)
    
    return result

def clean_datasets_for_irr(llm_data, nvivo_data):
    """
    Clean LLM and NVivo datasets by removing category header columns to prepare for IRR calculation.
    
    Parameters:
    -----------
    llm_data : pandas.DataFrame
        The dataframe containing LLM coding results
    nvivo_data : pandas.DataFrame
        The dataframe containing NVivo coding results
    
    Returns:
    --------
    tuple
        (cleaned_llm_data, cleaned_nvivo_data) - Dataframes with category header columns removed
    """
    # Create copies to avoid modifying the original dataframes
    llm_clean = llm_data.copy()
    nvivo_clean = nvivo_data.copy()
    
    # Identify category header columns based on pattern matching (C1, C2, C3, etc.)
    # These are the columns we want to exclude
    category_columns = []
    
    for col in llm_data.columns:
        # Match columns that contain "C" followed by a number in their name
        if re.search(r'C\d+\s+Objectives|C\d+\s+Time|C\d+\s+Stringency|C\d+\s+Value|C\d+\s+Type', col):
            category_columns.append(col)
    
    # Print identified category columns for verification
    print(f"Identified {len(category_columns)} category columns to exclude:")
    for col in category_columns:
        print(f"  - {col}")
    
    # Drop the category columns from both dataframes
    llm_clean = llm_clean.drop(columns=category_columns)
    nvivo_clean = nvivo_clean.drop(columns=category_columns)
    
    # Verify both dataframes have the same columns left
    remaining_columns = llm_clean.columns
    print(f"\nRemaining columns for IRR calculation: {len(remaining_columns)}")
    
    # Make sure both dataframes have identical columns
    assert set(llm_clean.columns) == set(nvivo_clean.columns), "Column mismatch after cleaning"
    
    return llm_clean, nvivo_clean

def gwets_ac1_manual(ratings1, ratings2):
    """
    Manually calculate Gwet's AC1 coefficient between two raters.
    
    Parameters:
    -----------
    ratings1 : numpy.ndarray
        Ratings from first rater
    ratings2 : numpy.ndarray
        Ratings from second rater
    
    Returns:
    --------
    float
        Gwet's AC1 coefficient
    """
    # Ensure ratings are numeric
    ratings1 = np.array(ratings1, dtype=float)
    ratings2 = np.array(ratings2, dtype=float)
    
    # Number of subjects
    n = len(ratings1)
    
    # Calculate observed agreement
    agreement = (ratings1 == ratings2).sum() / n
    
    # Calculate probability of chance agreement (specific to Gwet's AC1)
    # For binary ratings (0/1 or True/False)
    p1 = (ratings1.mean() + ratings2.mean()) / 2
    p_e = 2 * p1 * (1 - p1)
    
    # Calculate Gwet's AC1
    ac1 = (agreement - p_e) / (1 - p_e)
    
    return ac1

def calculate_category_irr(df1, df2, category_mappings):
    """
    Calculate Gwet's AC1 at the category level by aggregating related columns.
    
    Parameters:
    -----------
    df1 : pandas.DataFrame
        First dataframe (e.g., cleaned LLM data)
    df2 : pandas.DataFrame
        Second dataframe (e.g., cleaned NVivo data)
    category_mappings : dict
        Dictionary mapping category names to lists of column names
    
    Returns:
    --------
    dict
        Dictionary containing Gwet's AC1 scores for each category
    """
    # Make a copy to avoid modifying the original dataframes
    df1_copy = df1.copy()
    df2_copy = df2.copy()
    
    # Extract numeric index from country names for proper sorting
    def extract_country_index(country_str):
        """Extract the numeric index from country strings like '10 : Uruguay'"""
        try:
            # Extract the number at the beginning of the string
            import re
            match = re.match(r'^(\d+)', str(country_str))
            if match:
                return int(match.group(1))
            return 999  # Fallback for countries without numeric prefix
        except:
            return 999  # Fallback value
    
    # Create a new column with the numeric index
    df1_copy['country_index'] = df1_copy['country'].apply(extract_country_index)
    df2_copy['country_index'] = df2_copy['country'].apply(extract_country_index)
    
    # Sort by the numeric index 
    df1_copy = df1_copy.sort_values('country_index')
    df2_copy = df2_copy.sort_values('country_index')
    
    # Verify alignment
    if df1_copy['country'].tolist() != df2_copy['country'].tolist():
        print("\n⚠️ WARNING: Country lists don't match after sorting!")
        print("Using direct position-based alignment instead.")
        
        # Create a standardized reference list from the first dataframe
        reference_countries = df1_copy['country'].tolist()
        
        # Reindex the second dataframe to match the first
        country_order_mapping = {country: i for i, country in enumerate(reference_countries)}
        df2_positions = [country_order_mapping.get(country, 999) for country in df2_copy['country']]
        df2_copy['_position'] = df2_positions
        df2_copy = df2_copy.sort_values('_position').drop('_position', axis=1)
    
    # Clean up temporary columns
    df1_copy = df1_copy.drop('country_index', axis=1)
    df2_copy = df2_copy.drop('country_index', axis=1)
    
    if df1_copy['country'].tolist() == df2_copy['country'].tolist():
        print("✓ Countries are perfectly aligned!")
    
    # Create aggregated category columns
    results = {}
    
    for category, columns in category_mappings.items():
        # Verify columns exist in the dataframes
        existing_columns = [col for col in columns if col in df1_copy.columns and col in df2_copy.columns]
        
        if not existing_columns:
            print(f"Warning: No columns found for category {category}")
            continue
            
        print(f"\nProcessing category: {category}")
        print(f"Using columns: {existing_columns}")
        
        # Identify "Not mentioned" columns for this category
        not_mentioned_cols = [col for col in existing_columns if "Not mentioned" in col]
        positive_cols = [col for col in existing_columns if "Not mentioned" not in col]
        
        print(f"  Positive columns: {positive_cols}")
        print(f"  'Not mentioned' columns: {not_mentioned_cols}")
        
        # Encode the category value for each row in each dataframe based on column values
        df1_category_values = []
        df2_category_values = []
        
        for idx in range(len(df1_copy)):
            # FIXED LOGIC: A category is present if any positive column is True OR all "Not mentioned" columns are False
            df1_any_positive = any(df1_copy.iloc[idx][col] for col in positive_cols if col in df1_copy.columns)
            df1_all_not_mentioned_false = all(not df1_copy.iloc[idx][col] for col in not_mentioned_cols if col in df1_copy.columns)
            
            df2_any_positive = any(df2_copy.iloc[idx][col] for col in positive_cols if col in df2_copy.columns)
            df2_all_not_mentioned_false = all(not df2_copy.iloc[idx][col] for col in not_mentioned_cols if col in df2_copy.columns)
            
            # A category is considered present if any positive indicator is true OR all "not mentioned" indicators are false
            df1_category_present = df1_any_positive or (len(not_mentioned_cols) > 0 and df1_all_not_mentioned_false)
            df2_category_present = df2_any_positive or (len(not_mentioned_cols) > 0 and df2_all_not_mentioned_false)
            
            df1_category_values.append(1 if df1_category_present else 0)
            df2_category_values.append(1 if df2_category_present else 0)
        
        # Show category values for verification
        print(f"  LLM Category Values: {df1_category_values}")
        print(f"  NVivo Category Values: {df2_category_values}")
        print(f"  Match Count: {sum(1 for a, b in zip(df1_category_values, df2_category_values) if a == b)}/{len(df1_category_values)}")
        
        # Calculate Gwet's AC1 for this category
        try:
            ac1 = gwets_ac1_manual(df1_category_values, df2_category_values)
            results[category] = ac1
            print(f"  Gwet's AC1: {ac1:.4f}")
        except Exception as e:
            results[category] = f"Error: {str(e)}"
            print(f"  Error: {str(e)}")
    
    return results

def generate_irr_report(llm_data, nvivo_data, irr_results, category_mappings=None):
    """
    Generate a comprehensive statistical report for IRR analysis.
    
    Parameters:
    -----------
    llm_data : pandas.DataFrame
        The dataframe containing LLM coding results
    nvivo_data : pandas.DataFrame
        The dataframe containing NVivo coding results
    irr_results : dict
        Dictionary containing Gwet's AC1 results by category
    category_mappings : dict, optional
        Dictionary mapping category names to lists of column names
        
    Returns:
    --------
    pandas.DataFrame
        Summary statistics for the IRR analysis
    """
    # If no category mappings provided, use the default
    if category_mappings is None:
        category_mappings = {
            'C1: End plastic pollution': ['B : Mentioned with time frame', 'C : Mentioned, no time frame', 'D : Not mentioned'],
            'C2: Reduce production of plastics': ['F : Mentioned with specification', 'G : Mentioned, no specification', 'H : Not mentioned'],
            'C3: Benefits of plastics': ['J : Mentioned', 'K : Not mentioned'],
            'C4: Protect human health': ['M : Mentioned', 'N : Not mentioned'],
            'C5: Protect biodiversity and environment': ['P : Mentioned', 'Q : Not mentioned'],
            'C10: Time horizon of implementation': ['S : Not relevant', 'T : Not specified', 'U : Specified'],
            'C11: Stringency of measure': ['W : High', 'X : Low', 'Y : Non relevant'],
            'C6: Addressing full life cycle': ['AA : Mentioned', 'AB : Not mentioned', 'AC : Partial mention'],
            'C7: Other objectives': ['AE : Circular economy', 'AF : Climate change', 'AG : ESM', 
                                    'AH : Mentioned', 'AI : Not mentioned', 'AJ : Sustainable production'],
            'C8: Value chain': ['AL : 1. Upstream', 'AM : 2. Midstream', 'AN : 3. Downstream', 'AO : 4. Cross value chain'],
            'C9: Type of measure': ['AQ : Instrument', 'AR : Target']
        }
    
    # Create sorted copies of the data
    llm_sorted = llm_data.sort_values('country').reset_index(drop=True)
    nvivo_sorted = nvivo_data.sort_values('country').reset_index(drop=True)
    
    # Verify country alignment
    countries_match = llm_sorted['country'].tolist() == nvivo_sorted['country'].tolist()
    if not countries_match:
        # Try numeric sorting
        def extract_country_index(country_str):
            import re
            match = re.match(r'^(\d+)', str(country_str))
            if match:
                return int(match.group(1))
            return 999
        
        llm_sorted['country_index'] = llm_sorted['country'].apply(extract_country_index)
        nvivo_sorted['country_index'] = nvivo_sorted['country'].apply(extract_country_index)
        
        llm_sorted = llm_sorted.sort_values('country_index').reset_index(drop=True)
        nvivo_sorted = nvivo_sorted.sort_values('country_index').reset_index(drop=True)
        
        # Remove temp columns
        llm_sorted = llm_sorted.drop('country_index', axis=1)
        nvivo_sorted = nvivo_sorted.drop('country_index', axis=1)
        
        # Check alignment again
        countries_match = llm_sorted['country'].tolist() == nvivo_sorted['country'].tolist()
    
    print(f"Country Alignment: {'✓ MATCHED' if countries_match else '❌ MISMATCHED'}")
    
    # Calculate category presence and agreement
    report_data = []
    
    for category, columns in category_mappings.items():
        existing_columns = [col for col in columns if col in llm_sorted.columns and col in nvivo_sorted.columns]
        
        if not existing_columns:
            continue
            
        # Separate positive and not-mentioned columns
        positive_cols = [col for col in existing_columns if "Not mentioned" not in col]
        not_mentioned_cols = [col for col in existing_columns if "Not mentioned" in col]
        
        # Calculate category presence for each country
        llm_values = []
        nvivo_values = []
        
        for idx in range(len(llm_sorted)):
            # A category is present if any positive column is True OR all "Not mentioned" columns are False
            llm_any_positive = any(llm_sorted.iloc[idx][col] for col in positive_cols if col in llm_sorted.columns)
            llm_all_not_mentioned_false = all(not llm_sorted.iloc[idx][col] for col in not_mentioned_cols if col in llm_sorted.columns)
            
            nvivo_any_positive = any(nvivo_sorted.iloc[idx][col] for col in positive_cols if col in nvivo_sorted.columns)
            nvivo_all_not_mentioned_false = all(not nvivo_sorted.iloc[idx][col] for col in not_mentioned_cols if col in nvivo_sorted.columns)
            
            llm_present = llm_any_positive or (len(not_mentioned_cols) > 0 and llm_all_not_mentioned_false)
            nvivo_present = nvivo_any_positive or (len(not_mentioned_cols) > 0 and nvivo_all_not_mentioned_false)
            
            llm_values.append(1 if llm_present else 0)
            nvivo_values.append(1 if nvivo_present else 0)
        
        # Calculate agreement statistics
        matches = sum(1 for a, b in zip(llm_values, nvivo_values) if a == b)
        percent_agreement = (matches / len(llm_values)) * 100
        
        # Find disagreements
        disagreements = []
        for idx in range(len(llm_values)):
            if llm_values[idx] != nvivo_values[idx]:
                disagreements.append(f"{llm_sorted['country'].iloc[idx]} (LLM={llm_values[idx]}, NVivo={nvivo_values[idx]})")
        
        # Get AC1 score from results
        ac1_score = irr_results.get(category, "N/A")
        if isinstance(ac1_score, str) and ac1_score.startswith("Error"):
            ac1_score = "Error"
        
        # Add to report
        report_data.append({
            'Category': category,
            'LLM Present Count': sum(llm_values),
            'NVivo Present Count': sum(nvivo_values),
            'Difference': abs(sum(llm_values) - sum(nvivo_values)),
            'Matches': matches,
            'Total Countries': len(llm_values),
            'Percent Agreement': round(percent_agreement, 1),
            'Gwet AC1': ac1_score if isinstance(ac1_score, float) else ac1_score,
            'Disagreement Count': len(disagreements),
            'Disagreements': '; '.join(disagreements) if disagreements else "None"
        })
    
    # Create report DataFrame
    report_df = pd.DataFrame(report_data)
    
    # Print summary
    print("\n=== IRR ANALYSIS SUMMARY ===")
    print(f"Total Categories: {len(report_df)}")
    
    agreement_levels = [
        ('Excellent (0.8-1.0)', lambda x: x >= 0.8),
        ('Good (0.6-0.8)', lambda x: 0.6 <= x < 0.8),
        ('Moderate (0.4-0.6)', lambda x: 0.4 <= x < 0.6),
        ('Fair (0.2-0.4)', lambda x: 0.2 <= x < 0.4),
        ('Poor (0.0-0.2)', lambda x: 0.0 <= x < 0.2),
        ('Very Poor (<0.0)', lambda x: x < 0.0)
    ]
    
    print("\nAgreement Distribution:")
    for level_name, level_func in agreement_levels:
        count = sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and level_func(x))
        print(f"  {level_name}: {count} categories")
    
    # Calculate average AC1
    valid_ac1 = [x for x in report_df['Gwet AC1'] if isinstance(x, float)]
    if valid_ac1:
        avg_ac1 = sum(valid_ac1) / len(valid_ac1)
        print(f"\nAverage Gwet's AC1: {avg_ac1:.4f}")
    
    return report_df

def visualize_irr_results(report_df):
    """
    Create visualizations for IRR analysis results.
    
    Parameters:
    -----------
    report_df : pandas.DataFrame
        Report data from generate_irr_report
    """
    # Set style
    sns.set(style="whitegrid")
    
    # 1. Bar chart of Gwet's AC1 by category
    plt.figure(figsize=(12, 6))
    
    # Filter to only include numeric AC1 values
    ac1_data = report_df[report_df['Gwet AC1'].apply(lambda x: isinstance(x, float))].copy()
    ac1_data = ac1_data.sort_values('Gwet AC1')
    
    # Create bars with color based on agreement level
    bars = plt.barh(ac1_data['Category'], ac1_data['Gwet AC1'])
    
    # Color bars based on agreement level
    for i, bar in enumerate(bars):
        ac1 = ac1_data.iloc[i]['Gwet AC1']
        if ac1 >= 0.8:
            bar.set_color('forestgreen')
        elif ac1 >= 0.6:
            bar.set_color('yellowgreen')
        elif ac1 >= 0.4:
            bar.set_color('gold')
        elif ac1 >= 0.2:
            bar.set_color('orange')
        elif ac1 >= 0:
            bar.set_color('coral')
        else:
            bar.set_color('crimson')
    
    # Add reference line at 0
    plt.axvline(x=0, color='black', linestyle='--', alpha=0.7)
    
    # Add labels and title
    plt.xlabel("Gwet's AC1 Score")
    plt.ylabel("Category")
    plt.title("Inter-Rater Reliability by Category")
    
    # Add text labels
    for i, ac1 in enumerate(ac1_data['Gwet AC1']):
        plt.text(ac1 + 0.02, i, f'{ac1:.2f}', va='center')
    
    plt.tight_layout()
    plt.show()
    
    # 2. Comparison of LLM vs NVivo coding prevalence
    plt.figure(figsize=(12, 6))
    
    # Sort by difference
    prev_data = report_df.sort_values('Difference', ascending=False).copy()
    
    # Set index for plotting
    prev_data = prev_data.set_index('Category')
    
    # Create grouped bar chart
    prevalence = prev_data[['LLM Present Count', 'NVivo Present Count']].plot(kind='bar', figsize=(12, 6))
    
    plt.title('Coding Prevalence: LLM vs NVivo')
    plt.ylabel('Count')
    plt.xlabel('Category')
    plt.xticks(rotation=45, ha='right')
    plt.legend(['LLM', 'NVivo'])
    
    # Add count labels
    for i, p in enumerate(prevalence.patches):
        width, height = p.get_width(), p.get_height()
        x, y = p.get_xy() 
        prevalence.annotate('{}'.format(height),
                   (x + width/2, y + height + 0.1),
                   ha='center')
    
    plt.tight_layout()
    plt.show()
    
    # 3. Agreement percentage by category
    plt.figure(figsize=(12, 6))
    
    # Sort by agreement percentage
    agree_data = report_df.sort_values('Percent Agreement').copy()
    
    # Create bars
    bars = plt.barh(agree_data['Category'], agree_data['Percent Agreement'])
    
    # Color bars based on agreement percentage
    for i, bar in enumerate(bars):
        pct = agree_data.iloc[i]['Percent Agreement']
        if pct >= 90:
            bar.set_color('forestgreen')
        elif pct >= 80:
            bar.set_color('yellowgreen')
        elif pct >= 70:
            bar.set_color('gold')
        elif pct >= 60:
            bar.set_color('orange')
        else:
            bar.set_color('crimson')
    
    plt.xlabel('Percent Agreement')
    plt.ylabel('Category')
    plt.title('Agreement Percentage by Category')
    
    # Add text labels
    for i, pct in enumerate(agree_data['Percent Agreement']):
        plt.text(pct + 1, i, f'{pct:.1f}%', va='center')
    
    plt.tight_layout()
    plt.show()

def export_irr_report(report_df, filename='irr_analysis_report.xlsx'):
    """
    Export the IRR analysis report to Excel.
    
    Parameters:
    -----------
    report_df : pandas.DataFrame
        Report data from generate_irr_report
    filename : str, optional
        Output filename (default: 'irr_analysis_report.xlsx')
    """
    # Create a writer object
    with pd.ExcelWriter(filename) as writer:
        # Export full report
        report_df.to_excel(writer, sheet_name='Full Report', index=False)
        
        # Create summary sheet
        summary_data = {
            'Metric': [
                'Total Categories',
                'Excellent Agreement (AC1 ≥ 0.8)',
                'Good Agreement (0.6 ≤ AC1 < 0.8)',
                'Moderate Agreement (0.4 ≤ AC1 < 0.6)',
                'Fair Agreement (0.2 ≤ AC1 < 0.4)',
                'Poor Agreement (0.0 ≤ AC1 < 0.2)',
                'Very Poor Agreement (AC1 < 0.0)',
                'Average AC1 Score'
            ],
            'Value': [
                len(report_df),
                sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and x >= 0.8),
                sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and 0.6 <= x < 0.8),
                sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and 0.4 <= x < 0.6),
                sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and 0.2 <= x < 0.4),
                sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and 0.0 <= x < 0.2),
                sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and x < 0.0),
                sum(x for x in report_df['Gwet AC1'] if isinstance(x, float)) / 
                sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float))
            ]
        }
        
        # Create and export summary DataFrame
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Create disagreements sheet
        disagreements = report_df[['Category', 'Disagreement Count', 'Disagreements']].copy()
        disagreements = disagreements[disagreements['Disagreement Count'] > 0]
        if not disagreements.empty:
            disagreements.to_excel(writer, sheet_name='Disagreements', index=False)
    
    print(f"Report exported to {filename}")

def analyze_irr(llm_data, nvivo_data):
    """
    Analyze inter-rater reliability between LLM and NVivo data at the category level.
    
    Parameters:
    -----------
    llm_data : pandas.DataFrame
        The dataframe containing LLM coding results
    nvivo_data : pandas.DataFrame
        The dataframe containing NVivo coding results
    
    Returns:
    --------
    tuple
        (cleaned_llm_data, cleaned_nvivo_data, irr_results)
    """
    print(f"LLM data: {llm_data.shape[0]} rows and {llm_data.shape[1]} columns")
    print(f"NVivo data: {nvivo_data.shape[0]} rows and {nvivo_data.shape[1]} columns")
    
    # Clean the datasets (remove category header columns)
    llm_clean, nvivo_clean = clean_datasets_for_irr(llm_data, nvivo_data)
    
    # Define the category mappings based on column groups
    category_mappings = {
        'C1: End plastic pollution': ['B : Mentioned with time frame', 'C : Mentioned, no time frame', 'D : Not mentioned'],
        'C2: Reduce production of plastics': ['F : Mentioned with specification', 'G : Mentioned, no specification', 'H : Not mentioned'],
        'C3: Benefits of plastics': ['J : Mentioned', 'K : Not mentioned'],
        'C4: Protect human health': ['M : Mentioned', 'N : Not mentioned'],
        'C5: Protect biodiversity and environment': ['P : Mentioned', 'Q : Not mentioned'],
        'C10: Time horizon of implementation': ['S : Not relevant', 'T : Not specified', 'U : Specified'],
        'C11: Stringency of measure': ['W : High', 'X : Low', 'Y : Non relevant'],
        'C6: Addressing full life cycle': ['AA : Mentioned', 'AB : Not mentioned', 'AC : Partial mention'],
        'C7: Other objectives': ['AE : Circular economy', 'AF : Climate change', 'AG : ESM', 
                                'AH : Mentioned', 'AI : Not mentioned', 'AJ : Sustainable production'],
        'C8: Value chain': ['AL : 1. Upstream', 'AM : 2. Midstream', 'AN : 3. Downstream', 'AO : 4. Cross value chain'],
        'C9: Type of measure': ['AQ : Instrument', 'AR : Target']
    }
    
    # Calculate Gwet's AC1 at the category level
    category_results = calculate_category_irr(llm_clean, nvivo_clean, category_mappings)
    
    # Display results
    print("\nGwet's AC1 results by coding category:")
    for category, ac1 in category_results.items():
        if isinstance(ac1, float):
            print(f"{category}: {ac1:.4f}")
        else:
            print(f"{category}: {ac1}")
    
    # Calculate overall average AC1
    valid_scores = [score for score in category_results.values() if isinstance(score, float)]
    if valid_scores:
        avg_ac1 = sum(valid_scores) / len(valid_scores)
        print(f"\nAverage Gwet's AC1 across all categories: {avg_ac1:.4f}")
        print(f"Number of categories included in average: {len(valid_scores)}")
    else:
        print("\nNo valid AC1 scores calculated.")
    
    return llm_clean, nvivo_clean, category_results

def run_irr_analysis(llm_data_path, nvivo_data_path, output_dir='output'):
    """
    Run the complete IRR analysis pipeline.
    
    Parameters:
    -----------
    llm_data_path : str
        Path to the LLM data file (Excel or CSV)
    nvivo_data_path : str
        Path to the NVivo data file (Excel or CSV)
    output_dir : str, optional
        Directory to save output files (default: 'output')
    
    Returns:
    --------
    tuple
        (report_df, llm_clean, nvivo_clean, irr_results)
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 80)
    print("STARTING IRR ANALYSIS PIPELINE")
    print("=" * 80)
    
    # Load data based on file extension
    print(f"\nLoading LLM data from: {llm_data_path}")
    if llm_data_path.endswith('.xlsx') or llm_data_path.endswith('.xls'):
        llm_data = pd.read_excel(llm_data_path)
    else:
        llm_data = pd.read_csv(llm_data_path)
    
    print(f"Loading NVivo data from: {nvivo_data_path}")
    if nvivo_data_path.endswith('.xlsx') or nvivo_data_path.endswith('.xls'):
        nvivo_data = pd.read_excel(nvivo_data_path)
    else:
        nvivo_data = pd.read_csv(nvivo_data_path, encoding='utf-8')
        
    # Check if 'country' column exists in NVivo data
    if 'Unnamed: 0' in nvivo_data.columns and 'country' not in nvivo_data.columns:
        nvivo_data = nvivo_data.rename(columns={'Unnamed: 0': 'country'})
    
    # Map country names to ensure consistency
    llm_data_mapped = map_country_names(llm_data)
    
    # Run IRR analysis
    print("\nAnalyzing inter-rater reliability...")
    llm_clean, nvivo_clean, irr_results = analyze_irr(llm_data_mapped, nvivo_data)
    
    # Generate report
    print("\nGenerating comprehensive report...")
    report_df = generate_irr_report(llm_clean, nvivo_clean, irr_results)
    
    # Export report to Excel
    report_path = os.path.join(output_dir, 'irr_analysis_report.xlsx')
    export_irr_report(report_df, report_path)
    
    # Create and save visualizations
    print("\nGenerating visualizations...")
    try:
        # Store the current backend
        orig_backend = plt.get_backend()
        
        # Try to set a non-interactive backend for headless environments
        plt.switch_backend('Agg')
        
        # Create figure 1: AC1 by category
        plt.figure(figsize=(12, 6))
        ac1_data = report_df[report_df['Gwet AC1'].apply(lambda x: isinstance(x, float))].copy()
        ac1_data = ac1_data.sort_values('Gwet AC1')
        
        bars = plt.barh(ac1_data['Category'], ac1_data['Gwet AC1'])
        
        for i, bar in enumerate(bars):
            ac1 = ac1_data.iloc[i]['Gwet AC1']
            if ac1 >= 0.8:
                bar.set_color('forestgreen')
            elif ac1 >= 0.6:
                bar.set_color('yellowgreen')
            elif ac1 >= 0.4:
                bar.set_color('gold')
            elif ac1 >= 0.2:
                bar.set_color('orange')
            elif ac1 >= 0:
                bar.set_color('coral')
            else:
                bar.set_color('crimson')
        
        plt.axvline(x=0, color='black', linestyle='--', alpha=0.7)
        plt.xlabel("Gwet's AC1 Score")
        plt.ylabel("Category")
        plt.title("Inter-Rater Reliability by Category")
        
        for i, ac1 in enumerate(ac1_data['Gwet AC1']):
            plt.text(ac1 + 0.02, i, f'{ac1:.2f}', va='center')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'ac1_by_category.png'), dpi=300)
        plt.close()
        
        # Create figure 2: Coding prevalence
        plt.figure(figsize=(12, 6))
        prev_data = report_df.sort_values('Difference', ascending=False).copy()
        prev_data = prev_data.set_index('Category')
        
        prev_data[['LLM Present Count', 'NVivo Present Count']].plot(kind='bar', figsize=(12, 6))
        
        plt.title('Coding Prevalence: LLM vs NVivo')
        plt.ylabel('Count')
        plt.xlabel('Category')
        plt.xticks(rotation=45, ha='right')
        plt.legend(['LLM', 'NVivo'])
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'coding_prevalence.png'), dpi=300)
        plt.close()
        
        # Create figure 3: Percent agreement
        plt.figure(figsize=(12, 6))
        agree_data = report_df.sort_values('Percent Agreement').copy()
        
        bars = plt.barh(agree_data['Category'], agree_data['Percent Agreement'])
        
        for i, bar in enumerate(bars):
            pct = agree_data.iloc[i]['Percent Agreement']
            if pct >= 90:
                bar.set_color('forestgreen')
            elif pct >= 80:
                bar.set_color('yellowgreen')
            elif pct >= 70:
                bar.set_color('gold')
            elif pct >= 60:
                bar.set_color('orange')
            else:
                bar.set_color('crimson')
        
        plt.xlabel('Percent Agreement')
        plt.ylabel('Category')
        plt.title('Agreement Percentage by Category')
        
        for i, pct in enumerate(agree_data['Percent Agreement']):
            plt.text(pct + 1, i, f'{pct:.1f}%', va='center')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'percent_agreement.png'), dpi=300)
        plt.close()
        
        # Restore the original backend
        plt.switch_backend(orig_backend)
        
        print(f"Visualizations saved to {output_dir}")
    except Exception as e:
        print(f"Error generating visualizations: {str(e)}")
        traceback.print_exc()
    
    print("\nIRR analysis complete!")
    print("=" * 80)
    
    return report_df, llm_clean, nvivo_clean, irr_results, report_path

if __name__ == "__main__":
    print("Parsing arguments...")
    import argparse
    
    parser = argparse.ArgumentParser(description='Run IRR analysis between LLM and NVivo data')
    parser.add_argument('--llm_data', required=False, help='Path to LLM data file (Excel or CSV)')
    parser.add_argument('--nvivo_data', required=True, help='Path to NVivo data file (Excel or CSV)')
    parser.add_argument('--output_dir', default='output', help='Directory to save output files')
    parser.add_argument('--json_dir', default=None, help='Directory containing JSON files for extraction (optional)')
    
    try:
        args = parser.parse_args()
        print(f"Arguments: {args}")
        
        # Optional: Run extraction from JSON files first
        if args.json_dir:
            print(f"Starting JSON extraction from {args.json_dir}...")
            llm_output_path = os.path.join(args.output_dir, 'country_submissions_analysis.xlsx')
            print(f"Output will be saved to {llm_output_path}")
            df = run_extraction(args.json_dir, llm_output_path)
            if df is not None:
                args.llm_data = llm_output_path
                print(f"Setting LLM data path to {args.llm_data}")
            else:
                print("Error: JSON extraction returned None")
        
        # Run the IRR analysis
        print("Starting IRR analysis...")
        report_df, llm_clean, nvivo_clean, irr_results = run_irr_analysis(
            args.llm_data, 
            args.nvivo_data, 
            args.output_dir
        )
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
