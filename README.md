# Chris Lock Sendient Ingestion Suite

This project is a Flask web application designed for ingesting, processing, and matching educational assessment documents and their corresponding mark schemes. It leverages Optical Character Recognition (OCR) and Large Language Models (LLMs) to structure the content from uploaded PDF or image files.

## Features

* **File Upload:** Supports uploading assignments and mark schemes as either single PDF files or multiple image files (PNG, JPG, JPEG).
* **Concurrent Processing:** Handles assignment and mark scheme ingestion in separate threads for concurrent processing.
* **OCR Integration:** Utilizes Mistral AI for OCR to extract text and layout information from documents.
* **LLM-Powered Structuring:** Employs Azure OpenAI models (configurable, e.g., GPT-4.1, GPT-4o) to parse OCR output into a structured JSON format.
* **Content Deduplication:** Identifies and deduplicates common components (text, images, tables, etc.) within assessments to optimize storage and referencing.
* **Mark Scheme Ingestion:** Processes mark scheme documents, classifies them (generic, levelled, rubric), and extracts detailed marking criteria.
* **Assessment-Mark Scheme Matching:** Implements a sophisticated algorithm to match ingested assessment questions with their corresponding mark scheme entries based on textual similarity, ID tokenization, and mark proximity.
* **Job-Based Processing:** Each upload session is treated as a unique job with its own status tracking and output storage.
* **Progress Tracking:** Provides a real-time ingesting page showing the status of different processing stages (assignment ingestion, mark scheme ingestion, matching).
* **Results Display:** Offers a view to inspect the structured assessment, including individual questions, their context, and matched mark schemes.

## Directory Structure

```
chrislocksendient-ingestion-suite/
├── app.py                           # Main Flask application file
├── requirements.txt                 # Python dependencies
├── utils.py                         # Utility functions for file handling, ID generation etc.
├── .env                             # Environment variable configuration (user needs to create this)
├── ingestion_suite/                 # Core ingestion logic
│   ├── assignment_ingestion/        # Handles assignment processing
│   │   ├── new_assessment_ingestion_v2.py # Main assignment ingestion script
│   │   ├── output.py                # Pydantic models for assignment output
│   │   └── prompt_lib.py            # Prompts for LLM in assignment ingestion
│   └── mark_scheme_ingestion/       # Handles mark scheme processing
│       ├── few_shot_examples.py     # Example data for mark scheme LLM prompts
│       ├── helpers.py               # Helper functions for mark scheme ingestion (PDF conversion, LLM client)
│       ├── infer_openai.py          # Azure OpenAI LLM invocation for mark schemes
│       ├── ingest_mark_scheme.py    # Main mark scheme ingestion script
│       ├── match_ms_to_question.py  # Script for matching mark schemes to questions
│       ├── output.py                # Pydantic models for mark scheme output
│       ├── prompt_lib.py            # Prompts for cleaning and extracting mark schemes
│       └── structured_extraction.py # Extracts structured information from mark scheme images
├── static/                          # Static files (CSS, JavaScript)
│   ├── css/
│   │   └── style.css                # Main stylesheet
│   └── js/
│       └── main.js                  # Main JavaScript for frontend interactions
└── templates/                       # HTML templates for Flask
    ├── assessment_view.html         # Displays the processed assessment and mark schemes
    ├── base.html                    # Base HTML template
    ├── index.html                   # Homepage for uploading files
    ├── ingesting.html               # Shows processing progress
    └── includes/                    # HTML partials
        ├── _mark_scheme_display.html # Macro for displaying mark schemes
        └── _question_card.html      # Macro for displaying question cards
```

## Setup and Installation

1. **Clone the Repository:**

   ```bash
   git clone <repository-url>
   cd chrislocksendient-ingestion-suite
   ```

2. **Create a Virtual Environment (Recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   The `requirements.txt` file lists the necessary Python packages.

   ```bash
   pip install -r requirements.txt
   ```

   Ensure you have Poppler installed for PDF processing (`pdf2image` dependency). If Poppler is not in your system's PATH, you'll need to set the `POPPLER_PATH` environment variable.

4. **Set Up Environment Variables:**
   Create a `.env` file in the root of the project (`chrislocksendient-ingestion-suite/`). This file should be loaded by `load_dotenv(Path(__file__).parent / '.env')` in `app.py`. Populate it with the necessary API keys and configuration:

   ```env
   # Flask
   SECRET_KEY='your_very_secret_flask_key_here'
   FLASK_DEBUG=True  # Set to False for production

   # Mistral API (for OCR)
   MISTRAL_API_KEY='your_mistral_api_key' 

   # Azure OpenAI (for LLM structuring and other AI tasks)
   AZURE_OPENAI_API_KEY='your_azure_openai_api_key'

   # Assignment Ingestion Models
   ASSIGNMENT_LLM_MODEL='gpt-4.1'  # Or 'gpt-4o', 'o3-mini', 'o4-mini'
   AZURE_OPENAI_ENDPOINT='your_azure_endpoint'
   AZURE_OPENAI_VERSION='your_api_version'
   AZURE_OPENAI_DEPLOYMENT='your_deployment_name'

   # Mark Scheme Ingestion Models
   MARK_SCHEME_LLM_MODEL='gpt-4.1'
   MARK_SCHEME_IMAGE_LLM_MODEL='gpt-4.1'
   ```

5. **Create Upload and Ingested Data Folders:**
   The application will attempt to create these if they don't exist, but it's good practice to ensure the base directories are present and writable.

   ```bash
   mkdir uploads
   mkdir ingested_data
   ```

## Running the Application

1. **Ensure Environment Variables are Set:** The `.env` file should be in the project root.
2. **Start the Flask Server:**

   ```bash
   python app.py
   ```

   The application will typically be available at `http://127.0.0.1:5000/` or `http://0.0.0.0:5000/`. Host, port, and debug mode can be configured via environment variables.

## Usage

1. **Navigate to the Homepage:** Open your web browser and go to the application's URL.
2. **Upload Documents:**

   * For both the "Assignment Document" and "Mark Scheme Document" sections, choose whether you are uploading a PDF or Images.
   * Select the appropriate file(s) using the file input fields.
   * Click "Upload and Process Documents".
3. **Monitor Progress:** You will be redirected to an "ingesting" page that shows the progress of:

   * Assignment Ingestion
   * Mark Scheme Ingestion
   * Matching Process
     Keep this page open.
4. **View Results:** Once all processes are complete, you will be automatically redirected to the "Assessment View" page. This page displays:

   * The structured assessment questions.
   * Associated context (text, images, tables).
   * The matched mark scheme for each question, along with the match score.

## Key Modules and Components

* **`app.py`**: Main Flask application handling routing, file uploads, and job orchestration.
* **`utils.py`**: Helper functions for file handling and ID generation.
* **`ingestion_suite/assignment_ingestion/`:**

  * `new_assessment_ingestion_v2.py`: Performs OCR, structures content, and deduplicates components.
  * `output.py`: Defines Pydantic models for assignment output.
  * `prompt_lib.py`: LLM prompt templates.
* **`ingestion_suite/mark_scheme_ingestion/`:**

  * `ingest_mark_scheme.py`: Orchestrates mark scheme ingestion and classification.
  * `helpers.py`: PDF-to-image conversion and LLM client setup.
  * `infer_openai.py`: Azure OpenAI invocation wrapper.
  * `structured_extraction.py`: Initial mark scheme extraction.
  * `output.py`: Pydantic models for mark scheme structures.
  * `prompt_lib.py` & `few_shot_examples.py`: Prompts and examples for LLM guidance.
  * `match_ms_to_question.py`: Logic to match questions with mark schemes.
* **`static/`:** CSS and JavaScript for frontend interactions.
* **`templates/`:** HTML templates for upload form, progress tracking, and results display.

## Technologies Used

* **Backend:** Python, Flask
* **OCR:** Mistral AI
* **LLMs:** Azure OpenAI (GPT-4.1, GPT-4o, etc.)
* **Data Validation:** Pydantic
* **PDF Processing:** `pdf2image` & Poppler
* **Text Matching:** `rapidfuzz`, `scipy`
* **Frontend:** HTML, CSS, JavaScript
* **Environment Management:** `python-dotenv`

## Error Handling

* Uses `try-except` blocks for file I/O, API calls, and processing to catch and log errors.
* Reports errors in the ingesting page and server logs.
* Provides user-friendly messages when uploads or parsing fail.
