import json
import pandas as pd
import os
import traceback

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
        #df.to_excel(output_file, index=False)
        #print(f"Results saved to {output_file}")
        
        # Print some statistics
        print(f"\nExtraction Results:")
        print(f"Total countries processed: {len(df)}")
        print(f"Columns in output: {len(df.columns)}")
    
    return df

result_df = run_extraction('docs', 'country_submissions_analysis.xlsx')

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