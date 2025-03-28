# irr_analysis.py (modified)
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import traceback
import re
from pathlib import Path
import streamlit as st

# Import the run_irr_analysis function directly from IRR_pipeline
from IRR_pipeline import run_irr_analysis

def run_irr_analysis_for_streamlit(llm_data_path, nvivo_data_path, output_dir='results'):
    """
    Run the IRR analysis pipeline and return results adapted for Streamlit display.

    Parameters:
    -----------
    llm_data_path : str
        Path to the LLM data file (Excel or CSV)
    nvivo_data_path : str
        Path to the NVivo data file (Excel or CSV)
    output_dir : str, optional
        Directory to save output files (default: 'results')

    Returns:
    --------
    dict
        Dictionary containing all analysis results and visualization data for Streamlit
    """
    #print(f'DEBUGGING - run_irr_analysis_for_streamlit recieved the following file path for JSON data: {llm_data_path}')
    try:
        # Run the main IRR analysis pipeline from IRR_pipeline.py
        report_df, llm_clean, nvivo_clean, irr_results, report_path = run_irr_analysis( # Capture report_path
            llm_data_path, nvivo_data_path, output_dir
        )

        # Create visualizations as bytes data for Streamlit
        fig_data = {}

        # AC1 by category plot
        fig1 = plt.figure(figsize=(12, 6))
        ac1_data = report_df[report_df['Gwet AC1'].apply(lambda x: isinstance(x, float))].copy()
        ac1_data = ac1_data.sort_values('Gwet AC1')
        bars = plt.barh(ac1_data['Category'], ac1_data['Gwet AC1'])
        for i, bar in enumerate(bars):
            ac1 = ac1_data.iloc[i]['Gwet AC1']
            if ac1 >= 0.8: bar.set_color('forestgreen')
            elif ac1 >= 0.6: bar.set_color('yellowgreen')
            elif ac1 >= 0.4: bar.set_color('gold')
            elif ac1 >= 0.2: bar.set_color('orange')
            elif ac1 >= 0: bar.set_color('coral')
            else: bar.set_color('crimson')
        plt.axvline(x=0, color='black', linestyle='--', alpha=0.7)
        plt.xlabel("Gwet's AC1 Score")
        plt.ylabel("Category")
        plt.title("Inter-Rater Reliability by Category")
        for i, ac1 in enumerate(ac1_data['Gwet AC1']):
            plt.text(ac1 + 0.02, i, f'{ac1:.2f}', va='center')
        plt.tight_layout()
        buf1 = io.BytesIO()
        fig1.savefig(buf1, format='png', dpi=300)
        buf1.seek(0)
        fig_data['ac1_by_category'] = buf1
        plt.close(fig1)

        # Coding prevalence plot
        fig2 = plt.figure(figsize=(12, 6))
        prev_data = report_df.sort_values('Difference', ascending=False).copy()
        prev_data = prev_data.set_index('Category')
        prev_data[['LLM Present Count', 'NVivo Present Count']].plot(kind='bar', figsize=(12, 6), ax=plt.gca()) # Pass current axes to pandas plot
        plt.title('Coding Prevalence: LLM vs NVivo')
        plt.ylabel('Count')
        plt.xlabel('Category')
        plt.xticks(rotation=45, ha='right')
        plt.legend(['LLM', 'NVivo'])

        # Add count labels on bars (Correctly access patches of the bar chart)
        for container in plt.gca().containers: # get current axes and iterate through containers
            plt.gca().bar_label(container, label_type='edge') # Use bar_label for clarity

        plt.tight_layout()
        buf2 = io.BytesIO()
        fig2.savefig(buf2, format='png', dpi=300)
        buf2.seek(0)
        fig_data['coding_prevalence'] = buf2
        plt.close(fig2)


        # Percent agreement plot
        fig3 = plt.figure(figsize=(12, 6))
        agree_data = report_df.sort_values('Percent Agreement').copy()
        bars = plt.barh(agree_data['Category'], agree_data['Percent Agreement'])
        for i, bar in enumerate(bars):
            pct = agree_data.iloc[i]['Percent Agreement']
            if pct >= 90: bar.set_color('forestgreen')
            elif pct >= 80: bar.set_color('yellowgreen')
            elif pct >= 70: bar.set_color('gold')
            elif pct >= 60: bar.set_color('orange')
            else: bar.set_color('crimson')
        plt.xlabel('Percent Agreement')
        plt.ylabel('Category')
        plt.title('Agreement Percentage by Category')
        for i, pct in enumerate(agree_data['Percent Agreement']):
            plt.text(pct + 1, i, f'{pct:.1f}%', va='center')
        plt.tight_layout()
        buf3 = io.BytesIO()
        fig3.savefig(buf3, format='png', dpi=300)
        buf3.seek(0)
        fig_data['percent_agreement'] = buf3
        plt.close(fig3)

        # Calculate summary statistics
        summary_data = {
            'Total Categories': len(report_df),
            'Excellent Agreement (AC1 ≥ 0.8)': sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and x >= 0.8),
            'Good Agreement (0.6 ≤ AC1 < 0.8)': sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and 0.6 <= x < 0.8),
            'Moderate Agreement (0.4 ≤ AC1 < 0.6)': sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and 0.4 <= x < 0.6),
            'Fair Agreement (0.2 ≤ AC1 < 0.4)': sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and 0.2 <= x < 0.4),
            'Poor Agreement (0.0 ≤ AC1 < 0.2)': sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and 0.0 <= x < 0.2),
            'Very Poor Agreement (AC1 < 0.0)': sum(1 for x in report_df['Gwet AC1'] if isinstance(x, float) and x < 0.0),
        }

        # Calculate average AC1
        valid_ac1 = [x for x in report_df['Gwet AC1'] if isinstance(x, float)]
        avg_ac1 = sum(valid_ac1) / len(valid_ac1) if valid_ac1 else None
        summary_data['Average AC1 Score'] = avg_ac1

        # Return all results
        return {
            'report_df': report_df,
            'llm_clean': llm_clean,
            'nvivo_clean': nvivo_clean,
            'irr_results': irr_results,
            'fig_data': fig_data,
            'summary_data': summary_data,
            'report_path': report_path # Now report_path is defined
        }

    except Exception as e:
        st.error(f"Error during IRR analysis in irr_analysis.py: {e}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return None # Return None to indicate failure
