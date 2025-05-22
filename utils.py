import uuid
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from pdf2image import pdfinfo_from_path # For page count

UPLOAD_FOLDER = Path('uploads')
INGESTED_DATA_FOLDER = Path('ingested_data')
ALLOWED_EXTENSIONS_PDF = {'pdf'}
ALLOWED_EXTENSIONS_IMG = {'png', 'jpg', 'jpeg'}

# Ensure directories exist when this module is loaded
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
INGESTED_DATA_FOLDER.mkdir(parents=True, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_job_id():
    """Generates a unique job ID."""
    return str(uuid.uuid4())

def save_uploaded_files(files, job_id: str, file_type_prefix: str) -> list[Path]:
    """
    Saves uploaded files (a single PDF or multiple images) to a job-specific directory.
    'files' can be a single FileStorage object (for PDF) or a list of them (for images).
    'file_type_prefix' helps organize, e.g., 'assignment_pdf', 'assignment_images'.
    Returns a list of Path objects to the saved files.
    """
    job_upload_path = UPLOAD_FOLDER / job_id / file_type_prefix
    job_upload_path.mkdir(parents=True, exist_ok=True)

    saved_file_paths = []

    # Normalize 'files' to be a list
    if not isinstance(files, list):
        files_to_process = [files]
    else:
        files_to_process = files

    # Determine allowed extensions based on prefix
    current_allowed_extensions = ALLOWED_EXTENSIONS_PDF if 'pdf' in file_type_prefix else ALLOWED_EXTENSIONS_IMG

    for file_storage_item in files_to_process:
        if file_storage_item and file_storage_item.filename != '' and \
           allowed_file(file_storage_item.filename, current_allowed_extensions):

            filename = secure_filename(file_storage_item.filename)
            file_path = job_upload_path / filename
            file_storage_item.save(file_path)
            saved_file_paths.append(file_path)

    return saved_file_paths


def get_file_list_for_ingestion(job_id: str, file_type_prefix: str) -> list[Path]:
    """
    Gets the list of successfully saved files (PDF or images) for the ingestion process.
    """
    job_upload_path = UPLOAD_FOLDER / job_id / file_type_prefix
    if not job_upload_path.exists():
        return []
    # Sort to ensure deterministic order if it matters (e.g., for multi-page images)
    return sorted([p for p in job_upload_path.iterdir() if p.is_file()])


def get_page_count_or_image_num(file_paths: list[Path]) -> int:
    """
    Estimates work units: number of pages if PDF, else number of images.
    Assumes if it's a PDF, it's the first (and only) file in the list for that type.
    """
    if not file_paths:
        return 1 # Default to 1 unit to avoid division by zero in progress

    first_file = file_paths[0] # We only care about the first file for PDF page count

    if first_file.suffix.lower() == '.pdf':
        try:
            # Ensure POPPLER_PATH is set in your .env if poppler is not in system PATH
            poppler_path = os.getenv('POPPLER_PATH')
            info = pdfinfo_from_path(first_file, poppler_path=poppler_path)
            return info.get('Pages', 1) # Default to 1 if 'Pages' key is missing
        except Exception as e:
            print(f"Could not get PDF info (is Poppler installed and in PATH?): {e}")
            return 5 # Default for problematic PDF or missing Poppler
    else: # It's a list of images
        return len(file_paths) if len(file_paths) > 0 else 1
