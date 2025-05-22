import os
import json
import time
import threading
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Load environment variables from .env file at the app root
# This should be called before other imports that might rely on env vars
load_dotenv(Path(__file__).parent / '.env')

from utils import (
    generate_job_id, save_uploaded_files, get_page_count_or_image_num,
    UPLOAD_FOLDER, INGESTED_DATA_FOLDER, get_file_list_for_ingestion
)

# --- Add ingestion suite to Python path ---
import sys
csis_path = Path(__file__).parent / 'chrislocksendient_ingestion_suite'
# Add the directory containing 'chrislocksendient_ingestion_suite' to sys.path
# This allows imports like from chrislocksendient_ingestion_suite.assignment_ingestion...
sys.path.insert(0, str(Path(__file__).parent))


# Now import your ingestion functions
# These will be the refactored versions
from ingestion_suite.assignment_ingestion.new_assessment_ingestion_v2 import \
    ingest_assignment as csis_ingest_assignment, \
    save_results as csis_save_assignment_results_refactored # This needs to be the refactored version
from ingestion_suite.mark_scheme_ingestion.ingest_mark_scheme import \
    ingest_mark_scheme as csis_ingest_mark_scheme_refactored # This needs to be the refactored version
from ingestion_suite.mark_scheme_ingestion.match_ms_to_question import \
    main as csis_match_ms_to_question_refactored # This needs to be the refactored version
# Note: csis_pdf_to_images is now part of the refactored ingest_mark_scheme logic or called by it.

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_dev_secret_key_please_change')
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['INGESTED_DATA_FOLDER'] = str(INGESTED_DATA_FOLDER)

# In-memory store for job statuses (for a real app, use a DB or Redis)
job_statuses = {}

# --- Helper for ingestion threads ---
def run_assignment_ingestion_thread(job_id: str, assignment_files_for_ingestion: list[Path]):
    try:
        job_statuses[job_id]['assignment_status'] = 'processing'
        job_output_dir = INGESTED_DATA_FOLDER / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Job {job_id}: Starting assignment ingestion with files: {assignment_files_for_ingestion}")

        # Call the original ingest_assignment function
        modified_data, common_data = csis_ingest_assignment(
            files=assignment_files_for_ingestion,
            llm_model=os.getenv("ASSIGNMENT_LLM_MODEL", "gpt-4.1") # Make model configurable
        )

        # Call the refactored save_results function
        csis_save_assignment_results_refactored(
            modified=modified_data,
            common=common_data,
            output_dir=job_output_dir
            # base_name is removed or made optional in refactored save_results
        )

        job_statuses[job_id]['assignment_status'] = 'completed'
        job_statuses[job_id]['assignment_output_path'] = str(job_output_dir / "modified_assessment.json")
        job_statuses[job_id]['common_components_path'] = str(job_output_dir / "common_components.json")
        print(f"Job {job_id}: Assignment ingestion completed.")

    except Exception as e:
        print(f"Error in assignment ingestion for job {job_id}: {e}")
        import traceback
        traceback.print_exc()
        job_statuses[job_id]['assignment_status'] = f'error: {str(e)}'

def run_mark_scheme_ingestion_thread(job_id: str, mark_scheme_files_for_ingestion: list[Path]):
    try:
        job_statuses[job_id]['mark_scheme_status'] = 'processing'
        job_output_dir = INGESTED_DATA_FOLDER / job_id
        job_temp_image_dir = UPLOAD_FOLDER # Base for temp images within job folder
        job_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Job {job_id}: Starting mark scheme ingestion with files: {mark_scheme_files_for_ingestion}")

        # Call the refactored csis_ingest_mark_scheme
        # It should handle PDF to image conversion internally if needed, using job_id for temp image storage
        # and save its output to job_output_dir, returning the path.
        ms_output_file_path = csis_ingest_mark_scheme_refactored(
            input_files=mark_scheme_files_for_ingestion,
            job_output_dir=job_output_dir,
            job_id=job_id,
            temp_image_base_path=job_temp_image_dir # Pass base path for its temp images
        )

        job_statuses[job_id]['mark_scheme_status'] = 'completed'
        job_statuses[job_id]['mark_scheme_output_path'] = str(ms_output_file_path)
        print(f"Job {job_id}: Mark scheme ingestion completed. Output: {ms_output_file_path}")

    except Exception as e:
        print(f"Error in mark scheme ingestion for job {job_id}: {e}")
        import traceback
        traceback.print_exc()
        job_statuses[job_id]['mark_scheme_status'] = f'error: {str(e)}'

def run_matching_process_thread(job_id: str):
    try:
        job_statuses[job_id]['matching_status'] = 'processing'
        job_output_dir = INGESTED_DATA_FOLDER / job_id

        assessment_json_path_str = job_statuses[job_id].get('assignment_output_path')
        mark_scheme_json_path_str = job_statuses[job_id].get('mark_scheme_output_path')

        if not assessment_json_path_str or not Path(assessment_json_path_str).exists():
            raise ValueError(f"Missing or invalid ingested assessment JSON path for job {job_id}: {assessment_json_path_str}")
        if not mark_scheme_json_path_str or not Path(mark_scheme_json_path_str).exists():
            raise ValueError(f"Missing or invalid ingested mark scheme JSON path for job {job_id}: {mark_scheme_json_path_str}")

        print(f"Job {job_id}: Starting matching process.")
        # Call the refactored csis_match_ms_to_question, which returns the matched data
        matched_data = csis_match_ms_to_question_refactored(
            assessment_source=Path(assessment_json_path_str), # Pass Path objects
            mark_scheme_source=Path(mark_scheme_json_path_str),
            verbose=False # Typically false for server-side processing
        )

        matched_output_filename = f"{job_id}_matched_data.json"
        matched_output_path = job_output_dir / matched_output_filename
        with open(matched_output_path, 'w', encoding='utf-8') as f:
            json.dump(matched_data, f, indent=4)

        job_statuses[job_id]['matching_status'] = 'completed'
        job_statuses[job_id]['matched_data_path'] = str(matched_output_path)
        job_statuses[job_id]['status'] = 'completed' # Overall job status
        print(f"Job {job_id}: Matching process completed. Output: {matched_output_path}")

    except Exception as e:
        print(f"Error in matching for job {job_id}: {e}")
        import traceback
        traceback.print_exc()
        job_statuses[job_id]['matching_status'] = f'error: {str(e)}'
        job_statuses[job_id]['status'] = 'error'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        job_id = generate_job_id()
        session['job_id'] = job_id # Store job_id in session for potential later use

        job_statuses[job_id] = {
            'status': 'starting', # Initial overall status
            'assignment_status': 'pending',
            'mark_scheme_status': 'pending',
            'matching_status': 'pending',
            'assignment_units': 1, # Default to 1 to avoid div by zero
            'mark_scheme_units': 1
        }

        # --- Handle Assignment Upload ---
        assignment_upload_type = request.form.get('assignment_upload_type')
        saved_assignment_files = []
        if assignment_upload_type == 'pdf':
            assignment_pdf_file = request.files.get('assignment_pdf')
            if assignment_pdf_file and assignment_pdf_file.filename:
                saved_assignment_files = save_uploaded_files(assignment_pdf_file, job_id, 'assignment_pdf')
        elif assignment_upload_type == 'images':
            assignment_image_files = request.files.getlist('assignment_images')
            if any(f and f.filename for f in assignment_image_files):
                saved_assignment_files = save_uploaded_files(assignment_image_files, job_id, 'assignment_images')

        if not saved_assignment_files:
            job_statuses[job_id]['assignment_status'] = 'error: No assignment file uploaded or file type not allowed.'
            job_statuses[job_id]['status'] = 'error'
            return redirect(url_for('ingesting', job_id=job_id)) # Show error on ingesting page

        job_statuses[job_id]['assignment_units'] = get_page_count_or_image_num(saved_assignment_files)

        # --- Handle Mark Scheme Upload ---
        mark_scheme_upload_type = request.form.get('mark_scheme_upload_type')
        saved_mark_scheme_files = []
        if mark_scheme_upload_type == 'pdf':
            mark_scheme_pdf_file = request.files.get('mark_scheme_pdf')
            if mark_scheme_pdf_file and mark_scheme_pdf_file.filename:
                saved_mark_scheme_files = save_uploaded_files(mark_scheme_pdf_file, job_id, 'mark_scheme_pdf')
        elif mark_scheme_upload_type == 'images':
            mark_scheme_image_files = request.files.getlist('mark_scheme_images')
            if any(f and f.filename for f in mark_scheme_image_files):
                saved_mark_scheme_files = save_uploaded_files(mark_scheme_image_files, job_id, 'mark_scheme_images')

        if not saved_mark_scheme_files:
            job_statuses[job_id]['mark_scheme_status'] = 'error: No mark scheme file uploaded or file type not allowed.'
            job_statuses[job_id]['status'] = 'error'
            return redirect(url_for('ingesting', job_id=job_id))

        job_statuses[job_id]['mark_scheme_units'] = get_page_count_or_image_num(saved_mark_scheme_files)

        job_statuses[job_id]['status'] = 'processing' # Update overall status

        # Get the actual file paths from the utils function after saving
        # These paths are what your ingestion scripts will use
        assignment_files_for_ingestion = get_file_list_for_ingestion(job_id, 'assignment_pdf') or \
                                         get_file_list_for_ingestion(job_id, 'assignment_images')

        mark_scheme_files_for_ingestion = get_file_list_for_ingestion(job_id, 'mark_scheme_pdf') or \
                                          get_file_list_for_ingestion(job_id, 'mark_scheme_images')

        # Start ingestion in threads
        ass_thread = threading.Thread(target=run_assignment_ingestion_thread, args=(job_id, assignment_files_for_ingestion))
        ms_thread = threading.Thread(target=run_mark_scheme_ingestion_thread, args=(job_id, mark_scheme_files_for_ingestion))

        ass_thread.start()
        ms_thread.start()

        return redirect(url_for('ingesting', job_id=job_id))

    return render_template('index.html')

@app.route('/ingesting/<job_id>')
def ingesting(job_id):
    if job_id not in job_statuses:
        return "Job not found.", 404
    # Pass the whole job_info for the template to use
    return render_template('ingesting.html', job_id=job_id, job_info=job_statuses[job_id])

@app.route('/status/<job_id>')
def status(job_id):
    if job_id not in job_statuses:
        return jsonify({"status": "not_found", "message": "Job ID does not exist."}), 404

    current_job_status_obj = job_statuses[job_id]

    # Check if both ingestions are complete, then start matching
    if current_job_status_obj.get('assignment_status') == 'completed' and \
       current_job_status_obj.get('mark_scheme_status') == 'completed' and \
       current_job_status_obj.get('matching_status') == 'pending': # Only start if pending

        print(f"Job {job_id}: Both ingestions complete. Starting matching.")
        current_job_status_obj['matching_status'] = 'queued' # Update status immediately
        match_thread = threading.Thread(target=run_matching_process_thread, args=(job_id,))
        match_thread.start()

    return jsonify(current_job_status_obj)


@app.route('/assessment/<job_id>')
def view_assessment(job_id):
    if job_id not in job_statuses:
         return "Job not found. Please start a new upload.", 404

    current_job = job_statuses[job_id]
    if current_job.get('status') != 'completed':
        # Could redirect to ingesting page or show an error/wait message
        return redirect(url_for('ingesting', job_id=job_id))

    data_dir = INGESTED_DATA_FOLDER / job_id
    assessment_data = {}
    common_components = {}
    mark_scheme_data = {"mark_schemes": []}
    matched_data = []

    try:
        ass_path = current_job.get('assignment_output_path')
        common_path = current_job.get('common_components_path')
        ms_path = current_job.get('mark_scheme_output_path')
        match_path = current_job.get('matched_data_path')

        if not ass_path or not Path(ass_path).exists():
            raise FileNotFoundError("Modified assessment file not found.")
        with open(ass_path, 'r', encoding='utf-8') as f:
            assessment_data = json.load(f)

        if not common_path or not Path(common_path).exists():
            raise FileNotFoundError("Common components file not found.")
        with open(common_path, 'r', encoding='utf-8') as f:
            common_components = json.load(f)

        if ms_path and Path(ms_path).exists():
             with open(ms_path, 'r', encoding='utf-8') as f:
                mark_scheme_data = json.load(f)
        else:
            print(f"Warning: Mark scheme file not found or not specified for job {job_id}")
            # Proceed without mark scheme data, or handle as error

        if match_path and Path(match_path).exists():
            with open(match_path, 'r', encoding='utf-8') as f:
                matched_data = json.load(f) # This is a list of matches
        else:
            print(f"Warning: Matched data file not found or not specified for job {job_id}")

    except FileNotFoundError as e:
        print(f"File not found error for job {job_id}: {e}")
        return f"Error: Ingested data file not found for this job ({e}). Please try re-uploading.", 404
    except json.JSONDecodeError as e:
        print(f"JSON decode error for job {job_id}: {e}")
        return "Error: Could not parse ingested data. The file might be corrupted.", 500
    except Exception as e:
        print(f"An unexpected error occurred loading data for job {job_id}: {e}")
        import traceback
        traceback.print_exc()
        return "An unexpected error occurred.", 500


    # Create a lookup for mark schemes by their question_number for easier access in template
    # The structure of mark_scheme_data is {"mark_schemes": [...]}
    mark_schemes_list = mark_scheme_data.get('mark_schemes', [])
    mark_schemes_lookup = {ms.get('question_number'): ms for ms in mark_schemes_list}

    # Augment questions with their matched mark schemes
    processed_questions = []
    for q_data in assessment_data.get("questions", []):
        q_id = q_data.get("question_id")
        # Find the match for this question_id from the matched_data list
        match_info = next((m for m in matched_data if m.get("question_id") == q_id), None)

        q_data_copy = q_data.copy() # Work with a copy

        if match_info and match_info.get("mark_scheme_question_number"):
            ms_q_num = match_info.get("mark_scheme_question_number")
            q_data_copy['matched_mark_scheme'] = mark_schemes_lookup.get(ms_q_num)
            q_data_copy['match_score'] = match_info.get("score")
        else:
            q_data_copy['matched_mark_scheme'] = None
            q_data_copy['match_score'] = match_info.get("score") if match_info else None
            if match_info and match_info.get("note"):
                 q_data_copy['match_note'] = match_info.get("note")

        processed_questions.append(q_data_copy)

    assessment_data["questions"] = processed_questions

    return render_template('assessment_view.html',
                           assessment=assessment_data,
                           common_components=common_components,
                           job_id=job_id)

if __name__ == '__main__':
    # Set a default Poppler path if running directly and it's needed,
    # though it's better to set it in .env
    # os.environ['POPPLER_PATH'] = os.environ.get('POPPLER_PATH', 'C:\\path\\to\\poppler\\bin')
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=5000)
