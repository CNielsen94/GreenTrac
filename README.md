# GreenTracCoder: Qualitative Coding Analysis Tool

GreenTracCoder is a Streamlit-based application for processing, analyzing, and comparing qualitative coding data. It's designed to help researchers analyze policy documents using a combination of AI-powered LLM analysis (Google's Gemini API) and traditional NVivo coding techniques, with robust inter-rater reliability (IRR) measurement capabilities and experiment tracking.

## Features

* **Document Processing**: Process PDF documents using Google's Gemini API to extract structured data based on a predefined codebook
* **Batch Processing**: Analyze multiple documents at once for efficient workflow
* **IRR Analysis**: Compare AI-generated coding with human NVivo coding using Gwet's AC1 coefficient
* **Visualizations**: View interactive charts showing agreement levels and coding patterns
* **Experiment History**: Track experiments with different codebook configurations and compare results
* **Codebook Editor**: Modify the field definitions to test different extraction approaches
* **User Authentication**: Secure login system to protect your data and API usage
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

4. Set up environment variables:
   * Create a `.env` file in the project root
   * Add your Google Gemini API key: `GOOGLE_API_KEY=your_key_here`
   * (Optional) Set default admin credentials: `DEFAULT_ADMIN_USER=admin` and `DEFAULT_ADMIN_PASSWORD=secure_password`

## Usage

1. Start the application:

```bash
streamlit run app.py
```

2. Log in with your credentials (default admin account is created on first run if not specified)
3. Place your PDF files in the `docs` folder
4. Place your NVivo export file (named `nvivo_export.csv`) in the project root
5. Use the interface to process documents and analyze results

## Main Workflow

1. **How-To Tab**: Read the instructions to understand how to use the app
2. **Batch Processing & Analysis**: Process documents and run IRR analysis in a single workflow
   * Enter experiment name and notes
   * Click "Process & Analyze"
   * The system processes all PDFs, runs IRR analysis, and saves everything as a versioned experiment
3. **Codebook Editor**: Modify the field definitions to test different approaches
4. **Experiment History**: View past experiments and compare results
5. **Audio Player**: Take a break with project-related music
6. **User Management**: Admin tools for user access control

## Project Structure

```
greentrac_interface/
├── app.py                    # Main application file
├── utils.py                  # Utility functions
├── irr_analysis.py           # IRR analysis implementation
├── ui_elements.py            # UI components and tab rendering
├── ui_experiment_history.py  # Experiment history functionality
├── versioning.py             # Experiment versioning system
├── gemini_calls.py           # API calls to Google Gemini
├── IRR_pipeline.py           # Core IRR calculation functions
├── auth.py                   # Authentication system
├── plastic_codebook.json     # Structure for data extraction
├── codebook_finetune.json    # Instructions for data extraction
├── requirements.txt          # Required Python packages
├── docs/                     # Directory for PDF files
├── results/                  # Output directory for analysis results
├── experiments/              # Saved experiment versions
├── audio/                    # Audio files for the music player
└── lyrics/                   # Lyrics for audio tracks
```

## IRR Analysis

The IRR analysis measures agreement between two different coding approaches:
1. **LLM Coding**: Automated extraction of structured data from documents using AI
2. **NVivo Coding**: Manual human coding of the same documents

The analysis uses Gwet's AC1 coefficient, which is appropriate for categorical data with potential prevalence problems. The results include:
* Agreement levels for different categories
* Visualizations of agreement patterns
* Detailed statistics about coding differences
* Excel reports for further analysis

## Experiment Tracking

The experiment tracking system allows you to:
* Save different codebook configurations and their results
* View document processing results within experiment details
* Compare IRR scores between experiments to see if changes improved agreement
* Export experiments for sharing or backup
* Apply previous codebook configurations to new analyses

## User Management

The application includes a user authentication system with:
* Admin and regular user roles
* Password protection for API usage
* User management interface for admins

## GitHub Integration

The codebook can be synchronized with GitHub:
1. Edit the codebook on GitHub
2. Click "Refresh Codebook from GitHub" in the sidebar
3. Process documents with the updated codebook

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
