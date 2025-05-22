from pathlib import Path
import os
import base64
import logging
from typing import Any, Dict, Optional, List # Added List

from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

from pdf2image import convert_from_path, pdfinfo_from_path


# load_dotenv should be handled by the main Flask app.
# from dotenv import load_dotenv
# load_dotenv(Path(__file__).resolve().parent.parent.parent / '.env') # Example path

logger = logging.getLogger(__name__)


def fetch_test_file_path(*path_parts: str, index: int = 0) -> Path:
    """
    Fetch the PDF at the given index under test_data/path_part1/path_part2/... .
    (This function is likely for testing and might not be used directly by the Flask app's main flow)
    """
    # Construct path relative to this file's location if test_data is structured accordingly
    base_test_data_path = Path(__file__).parent / "test_data" / "mark_schemes"
    target_dir = base_test_data_path.joinpath(*path_parts)

    if not target_dir.is_dir():
        raise FileNotFoundError(f"No such directory for test files: {target_dir!r}")

    pdfs = sorted(target_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF files in test directory {target_dir!r}")

    idx = int(index)
    if not 0 <= idx < len(pdfs):
        raise IndexError(f"Index {idx} out of range for PDFs in {target_dir!r}")

    return Path(str(pdfs[idx]).replace('\\', '/'))

def get_llm(model_name: str) -> Optional[ChatCompletionsClient]:
    """Return an AzureChatOpenAI instance (or None on config error)."""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_4_1")
    key = os.getenv("AZURE_OPENAI_API_KEY")
    version = os.getenv("AZURE_OPENAI_VERSION_4_1")

    print(endpoint)
    print(key)
    print(version)

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
        api_version=version,
    )

    try:
        return client
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("LLM init error: %s", exc)
        return None

# MODIFIED pdf_to_images function
def pdf_to_images(pdf_path: Path, output_image_folder: Path) -> list[Path]:
    """
    Convert a PDF file to a list of image file paths, one per page.
    Images are saved in the specified output_image_folder.
    """
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        return []

    output_image_folder.mkdir(parents=True, exist_ok=True)
    image_paths = []

    try:
        # Get POPPLER_PATH from environment; crucial for pdf2image on many systems
        poppler_path_env = os.getenv('POPPLER_PATH')
        images = convert_from_path(str(pdf_path), poppler_path=poppler_path_env)

        for i, image in enumerate(images):
            image_filename = f"page_{i+1}.png"
            persistent_image_path = output_image_folder / image_filename
            image.save(persistent_image_path, "PNG")
            image_paths.append(persistent_image_path)
        logger.info(f"Converted PDF {pdf_path.name} to {len(image_paths)} images in {output_image_folder}")
    except Exception as e:
        logger.error(f"Failed to convert PDF {pdf_path.name} to images: {e}")
        logger.error("Ensure Poppler is installed and POPPLER_PATH environment variable is set correctly if needed.")
        # import traceback # Uncomment for detailed stack trace during debugging
        # traceback.print_exc() # Uncomment for detailed stack trace
        return [] # Return empty list on failure

    return image_paths


def load_image_as_data_url(image_path: Path) -> Optional[str]:
    """Encodes an image file to a base64 data URL."""
    if not image_path.exists():
        logger.error(f"Image file not found for data URL: {image_path}")
        return None
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

        # Determine MIME type (simple check, mimetypes library could be more robust)
        ext = image_path.suffix.lower()
        if ext == ".png":
            mime_type = "image/png"
        elif ext in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        else:
            logger.warning(f"Unsupported image type for data URL: {ext}. Defaulting to image/png.")
            mime_type = "image/png" # Fallback

        return f"data:{mime_type};base64,{encoded_image}"
    except Exception as e:
        logger.error(f"Failed to load image {image_path} as data URL: {e}")
        return None


def escape_braces(json_str: str) -> str:
    """Escapes curly braces for use in f-string formatting if needed (though less common with direct JSON objects)."""
    return json_str.replace("{", "{{").replace("}", "}}")

def collapse_entries(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Given a list of question-dicts (typically from initial mark scheme extraction),
    merge any entries with question_number == 'previous' into the dict immediately
    before them. This handles mark schemes spanning multiple OCR segments/pages.
    """
    if not data:
        return []

    result: List[Dict[str, Any]] = []
    for item in data:
        current_item_copy = item.copy() # Work with a copy

        if current_item_copy.get("question_number") == "previous":
            if not result:
                logger.warning("Found 'previous' item at the beginning of the list. Cannot merge. Item: %s", current_item_copy)
                # Optionally, decide to keep it or discard it. Keeping it might be safer.
                # result.append(current_item_copy) # Or skip
                continue

            parent = result[-1] # Get the last valid item to merge into

            # Merge 'mark_scheme_information'
            if current_item_copy.get("mark_scheme_information"):
                parent["mark_scheme_information"] = (
                    parent.get("mark_scheme_information", "") +
                    "\n\n" + # Add a separator
                    current_item_copy["mark_scheme_information"]
                )

            # Merge 'question_text' if present (less common for 'previous' but handle it)
            if current_item_copy.get("question_text"):
                parent["question_text"] = (
                    parent.get("question_text", "") +
                    "\n\n" +
                    current_item_copy["question_text"]
                ).strip() # strip in case one was None/empty

            # If parent was missing marks_available, inherit from 'previous' item if it has it
            if current_item_copy.get("marks_available") is not None and parent.get("marks_available") is None:
                parent["marks_available"] = current_item_copy["marks_available"]

            # Potentially merge other fields if necessary, e.g., if classification could differ
            # For now, assuming 'mark_scheme_information' and 'marks_available' are primary concerns

        else: # Not a 'previous' item, so add it to results
            result.append(current_item_copy)

    return result
