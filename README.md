# GreenTracCoder: Qualitative Coding Analysis Tool

GreenTracCoder is a Streamlit-based application for processing, analyzing, and comparing qualitative coding data. It's designed to help researchers analyze policy documents using a combination of AI-powered LLM analysis and traditional NVivo coding techniques, with robust inter-rater reliability (IRR) measurement capabilities.

## Features

* **Document Processing**: Process PDF documents using Google's Gemini API to extract structured data based on a predefined codebook
* **Batch Processing**: Analyze multiple documents at once for efficient workflow
* **IRR Analysis**: Compare AI-generated coding with human NVivo coding using Gwet's AC1 coefficient
* **Visualizations**: View interactive charts showing agreement levels and coding patterns
* **Results Viewer**: Examine the structured data extracted from documents
* **Codebook Editor**: Modify the field definitions to test different extraction approaches
* **Audio Player**: Take a break and enjoy project-related music tracks

## Installation

1. Clone this repository:

```bash
git clone https://github.com/your-username/greentrac_interface.git
cd greentrac_interface
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Set up your API key:
   * Create a `.env` file in the project root
   * Add your Google Gemini API key: `GOOGLE_API_KEY=your_key_here`

## Usage

1. Start the application:

```bash
streamlit run app.py
```

2. Place your PDF files in the `docs` folder
3. Place your NVivo export file (named `nvivo_export.csv`) in the project root
4. Use the interface to process documents and analyze results

## Project Structure

```
greentrac_interface/
├── app.py                # Main application file
├── utils.py              # Utility functions
├── irr_analysis.py       # IRR analysis implementation
├── ui_elements.py        # UI components and tab rendering
├── gemini_calls.py       # API calls to Google Gemini
├── IRR_pipeline.py       # Core IRR calculation functions
├── plastic_codebook.json # Structure for data extraction
├── codebook_finetune.json # Instructions for data extraction
├── docs/                 # Directory for PDF files
├── results/              # Output directory for analysis results
├── audio/                # Audio files for the music player (auto-generated on application start up)
└── lyrics/               # Lyrics for audio tracks (auto-generated on application start up)
```

## Workflow

1. **How-To Tab**: Read the instructions to understand how to use the app
2. **File Processing**: Process individual files or use batch processing for multiple files
3. **Results Viewer**: Examine the structured data extracted from documents
4. **IRR Analysis**: Compare LLM results with NVivo coding and measure agreement
5. **Codebook Editor**: Modify the field definitions if needed

## IRR Analysis

The IRR analysis measures agreement between two different coding approaches:
1. **LLM Coding**: Automated extraction of structured data from documents using AI
2. **NVivo Coding**: Manual human coding of the same documents

The analysis uses Gwet's AC1 coefficient, which is appropriate for categorical data with potential prevalence problems. The results include:
* Agreement levels for different categories
* Visualizations of agreement patterns
* Detailed statistics about coding differences
* Excel reports for further analysis

## Requirements

* Python 3.8+
* Streamlit
* Pandas
* NumPy
* Matplotlib
* Seaborn
* Google Gemini API key

## Credits

* IRR calculation code based on Gwet's AC1
* Music tracks generated using Suno AI
* PDF processing powered by Google Gemini