import json
import os # For os.getenv
from pathlib import Path
from typing import List, Union, cast # Added Union and cast

from azure.ai.inference.models import TextContentItem, UserMessage

# Assuming infer_openai, output, few_shot_examples, prompt_lib, helpers, structured_extraction
# are in the same directory or correctly pathed for the Flask app.
# Use relative imports for modules within the same package.
from .infer_openai import invoke_openai
from .output import (
    ExtractedMarkSchemesInformationWrapper, ExtractedMarkSchemeInformation,
    ObjectiveMarkSchemeModel, RubricMarkSchemeModel, MarkSchemeBaseModel,
    IngestedMarkSchemesModel, IngestedMarkSchemeModel as SingleIngestedMarkSchemeType # Alias for clarity
)
from .few_shot_examples import (
    extract_levelled_mark_scheme_example_output_1, extract_levelled_mark_scheme_example_output_2,
    extract_generic_mark_scheme_example_output_1, extract_generic_mark_scheme_example_output_2,
    extract_generic_mark_scheme_example_output_3,
    extract_rubric_mark_scheme_example_output_1, extract_rubric_mark_scheme_example_output_2 # Added rubrics
)
from .prompt_lib import (
    extract_levelled_mark_scheme_prompt, extract_generic_mark_scheme_prompt,
    extract_rubric_mark_scheme_prompt, # Added rubric prompt
    extract_mark_schemes_from_image_and_classify_prompt
)
from .helpers import pdf_to_images as csis_pdf_to_images # Use aliased helper
from .structured_extraction import extract_mark_scheme_information_from_images_openai

import logging
logger = logging.getLogger(__name__)


def extract_generic_mark_scheme(mark_scheme_raw: ExtractedMarkSchemeInformation) -> MarkSchemeBaseModel:
    logger.info(f"Extracting generic mark scheme for: {mark_scheme_raw.get('question_number', 'N/A')}")
    question_text_context = f"\nFor your context, the question that the mark scheme is for is as follows: \n<question>\n{mark_scheme_raw.get('question_text')}\n</question>" if mark_scheme_raw.get("question_text") else ""
    marks_available_context = f"\nFor additional context, the total marks available for the question is as follows: \n<marks_available>\n{str(mark_scheme_raw.get('marks_available'))}\n</marks_available>" if mark_scheme_raw.get("marks_available") is not None else ""

    prompt = extract_generic_mark_scheme_prompt.format(
        question_text=question_text_context,
        marks_available=marks_available_context,
        example_output_1=json.dumps(extract_generic_mark_scheme_example_output_1, indent=2),
        example_output_2=json.dumps(extract_generic_mark_scheme_example_output_2, indent=2),
        example_output_3=json.dumps(extract_generic_mark_scheme_example_output_3, indent=2),
        # example_output_4=json.dumps(extract_generic_mark_scheme_example_output_4, indent=2) # Add if you have a 4th example
    )

    mark_scheme_content_for_llm = mark_scheme_raw.get('mark_scheme_information', '')
    user_message = UserMessage(content=[TextContentItem(text=mark_scheme_content_for_llm)])

    try:
        response_str = invoke_openai(
            prompt=prompt,
            model_name=os.getenv("MARK_SCHEME_LLM_MODEL", "gpt-4.1"),
            output_format=MarkSchemeBaseModel, # Pass the Pydantic model class
            payload=[user_message]
        )
        if response_str:
            # The invoke_openai should ideally return a dict if output_format is used with azure.ai.inference
            # If it returns a string, parse it.
            parsed_response = json.loads(response_str) if isinstance(response_str, str) else response_str
            return MarkSchemeBaseModel(**parsed_response)
        else:
            logger.error("LLM returned empty response for generic mark scheme extraction.")
            return MarkSchemeBaseModel(criteria=[], total_marks_available=mark_scheme_raw.get('marks_available'))
    except Exception as e:
        logger.error(f"Error extracting generic mark scheme: {e}. Raw MS info: {mark_scheme_content_for_llm[:200]}")
        # Fallback or re-raise
        return MarkSchemeBaseModel(criteria=[], total_marks_available=mark_scheme_raw.get('marks_available'))


def extract_levelled_mark_scheme(mark_scheme_raw: ExtractedMarkSchemeInformation) -> ObjectiveMarkSchemeModel:
    logger.info(f"Extracting levelled mark scheme for: {mark_scheme_raw.get('question_number', 'N/A')}")
    question_text_context = f"\nFor your context, the question that the mark scheme is for is as follows: \n<question>\n{mark_scheme_raw.get('question_text')}\n</question>" if mark_scheme_raw.get("question_text") else ""

    prompt = extract_levelled_mark_scheme_prompt.format(
        question_text=question_text_context,
        example_output_1=json.dumps(extract_levelled_mark_scheme_example_output_1, indent=2),
        example_output_2=json.dumps(extract_levelled_mark_scheme_example_output_2, indent=2)
    )

    mark_scheme_content_for_llm = mark_scheme_raw.get('mark_scheme_information', '')
    user_message = UserMessage(content=[TextContentItem(text=mark_scheme_content_for_llm)])

    try:
        response_str = invoke_openai(
            prompt=prompt,
            model_name=os.getenv("MARK_SCHEME_LLM_MODEL", "gpt-4.1"),
            output_format=ObjectiveMarkSchemeModel, # Pass Pydantic model
            payload=[user_message]
        )
        if response_str:
            parsed_response = json.loads(response_str) if isinstance(response_str, str) else response_str
            return ObjectiveMarkSchemeModel(**parsed_response)
        else:
            logger.error("LLM returned empty response for levelled mark scheme extraction.")
            # Provide a minimal valid ObjectiveMarkSchemeModel
            return ObjectiveMarkSchemeModel(objective="Unknown", mark_scheme=[])
    except Exception as e:
        logger.error(f"Error extracting levelled mark scheme: {e}. Raw MS info: {mark_scheme_content_for_llm[:200]}")
        return ObjectiveMarkSchemeModel(objective="Error", mark_scheme=[])


def extract_rubric_mark_scheme(mark_scheme_raw: ExtractedMarkSchemeInformation) -> RubricMarkSchemeModel:
    logger.info(f"Extracting rubric mark scheme for: {mark_scheme_raw.get('question_number', 'N/A')}")
    question_text_context = f"\nFor your context, the question that the mark scheme is for is as follows: \n<question>\n{mark_scheme_raw.get('question_text')}\n</question>" if mark_scheme_raw.get("question_text") else ""

    # Assuming extract_rubric_mark_scheme_prompt exists and is similar to others
    prompt = extract_rubric_mark_scheme_prompt.format(
        question_text=question_text_context,
        example_output_1=json.dumps(extract_rubric_mark_scheme_example_output_1, indent=2), # Ensure these examples exist
        example_output_2=json.dumps(extract_rubric_mark_scheme_example_output_2, indent=2)
    )

    mark_scheme_content_for_llm = mark_scheme_raw.get('mark_scheme_information', '')
    user_message = UserMessage(content=[TextContentItem(text=mark_scheme_content_for_llm)])

    try:
        response_str = invoke_openai(
            prompt=prompt,
            model_name=os.getenv("MARK_SCHEME_LLM_MODEL", "gpt-4.1"),
            output_format=RubricMarkSchemeModel, # Pass Pydantic model
            payload=[user_message]
        )
        if response_str:
            parsed_response = json.loads(response_str) if isinstance(response_str, str) else response_str
            return RubricMarkSchemeModel(**parsed_response)
        else:
            logger.error("LLM returned empty response for rubric mark scheme extraction.")
            return RubricMarkSchemeModel(rubric=[]) # Minimal valid model
    except Exception as e:
        logger.error(f"Error extracting rubric mark scheme: {e}. Raw MS info: {mark_scheme_content_for_llm[:200]}")
        return RubricMarkSchemeModel(rubric=[])


def route_and_extract_mark_schemes(
    raw_mark_schemes_list: List[ExtractedMarkSchemeInformation]
) -> IngestedMarkSchemesModel:

    processed_mark_schemes: List[SingleIngestedMarkSchemeType] = []

    for raw_ms_info_dict in raw_mark_schemes_list:
        # Ensure raw_ms_info_dict is a dictionary, not the Pydantic model instance yet,
        # or convert Pydantic model to dict if needed by classification functions.
        # The functions extract_generic/levelled/rubric expect ExtractedMarkSchemeInformation (which is a dict-like Pydantic model)

        # No need to create Pydantic model here if functions accept dict-like
        # raw_ms_pydantic_item = ExtractedMarkSchemeInformation(**raw_ms_info_dict)

        classification = raw_ms_info_dict.get('classification')
        question_number = raw_ms_info_dict.get('question_number', 'UNKNOWN_QN')

        extracted_detail: Union[MarkSchemeBaseModel, ObjectiveMarkSchemeModel, RubricMarkSchemeModel, None] = None
        final_type_str = ""

        if classification == "generic":
            extracted_detail = extract_generic_mark_scheme(raw_ms_info_dict)
            final_type_str = "generic"
        elif classification == "levelled":
            extracted_detail = extract_levelled_mark_scheme(raw_ms_info_dict)
            final_type_str = "levelled"
        elif classification == "rubric":
            extracted_detail = extract_rubric_mark_scheme(raw_ms_info_dict)
            final_type_str = "rubric"
        else:
            logger.warning(f"Unknown classification: '{classification}' for question '{question_number}'. Skipping detailed extraction for this item.")
            # Create a placeholder or skip
            # For now, let's create a basic entry to acknowledge it was seen
            extracted_detail = MarkSchemeBaseModel(criteria=[], total_marks_available=raw_ms_info_dict.get('marks_available'))
            final_type_str = "unknown_classification"


        # Construct the SingleIngestedMarkSchemeType object
        # Ensure all fields are present or have defaults
        ingested_item_data = {
            "type": final_type_str,
            "question_number": question_number,
            "question_text": raw_ms_info_dict.get("question_text"),
            "marks_available": raw_ms_info_dict.get("marks_available"),
            "mark_scheme_information": raw_ms_info_dict.get("mark_scheme_information", ""), # Raw text
            "mark_scheme": extracted_detail # The structured Pydantic model
        }
        try:
            processed_mark_schemes.append(SingleIngestedMarkSchemeType(**ingested_item_data))
        except Exception as e_pydantic:
            logger.error(f"Pydantic validation error for QN {question_number} with type {final_type_str}: {e_pydantic}")
            logger.error(f"Data causing error: {ingested_item_data}")


    return IngestedMarkSchemesModel(mark_schemes=processed_mark_schemes)

# REFACTORED ingest_mark_scheme function
def ingest_mark_scheme(
    input_files: List[Path],
    job_output_dir: Path,
    job_id: str,
    temp_image_base_path: Path # Base path for storing temporary images from PDF
) -> Path:

    if not input_files:
        logger.error(f"Job {job_id}: No input files provided for mark scheme ingestion.")
        raise ValueError("No input files provided for mark scheme ingestion.")

    image_paths_for_extraction: List[Path] = []

    # Check if input is PDF (assume only one PDF if type is PDF)
    is_pdf_input = any(f.suffix.lower() == '.pdf' for f in input_files)

    if is_pdf_input:
        if len(input_files) > 1:
            logger.error(f"Job {job_id}: Multiple files provided but expected a single PDF for mark scheme.")
            raise ValueError("If uploading a PDF mark scheme, only one PDF file should be provided.")

        pdf_file_path = input_files[0]
        logger.info(f"Job {job_id}: Processing PDF mark scheme: {pdf_file_path.name}")

        # Define a job-specific folder for images extracted from this PDF
        pdf_conversion_image_folder = temp_image_base_path / job_id / "ms_pdf_pages"
        pdf_conversion_image_folder.mkdir(parents=True, exist_ok=True)

        image_paths_for_extraction = csis_pdf_to_images(pdf_file_path, pdf_conversion_image_folder)
        if not image_paths_for_extraction:
            logger.error(f"Job {job_id}: PDF to image conversion failed for {pdf_file_path.name}.")
            raise RuntimeError(f"PDF to image conversion failed for {pdf_file_path.name}.")
    else: # Input is already a list of image paths
        logger.info(f"Job {job_id}: Processing pre-uploaded images for mark scheme.")
        image_paths_for_extraction = input_files

    if not image_paths_for_extraction:
        logger.error(f"Job {job_id}: No images available for mark scheme extraction after input processing.")
        raise RuntimeError("No images available for mark scheme extraction.")

    # Prepare the prompt for the initial image-to-text/classification step
    # This prompt is defined in prompt_lib.py
    prompt_for_initial_extraction = extract_mark_schemes_from_image_and_classify_prompt

    # Call the function from structured_extraction.py
    # This returns a list of ExtractedMarkSchemeInformation (as dicts after collapse_entries)
    logger.info(f"Job {job_id}: Starting initial mark scheme extraction from {len(image_paths_for_extraction)} images.")
    raw_extracted_ms_list: List[ExtractedMarkSchemeInformation] = extract_mark_scheme_information_from_images_openai(
        images=image_paths_for_extraction,
        prompt=prompt_for_initial_extraction,
        model_name=os.getenv("MARK_SCHEME_IMAGE_LLM_MODEL", "gpt-4.1") # Configurable model
    )

    if not raw_extracted_ms_list:
        logger.warning(f"Job {job_id}: Initial extraction (structured_extraction) returned no mark schemes.")
        # Create an empty IngestedMarkSchemesModel
        processed_data = IngestedMarkSchemesModel(mark_schemes=[])
    else:
        logger.info(f"Job {job_id}: Routing and performing detailed extraction for {len(raw_extracted_ms_list)} raw mark schemes.")
        # Perform detailed extraction based on classification
        processed_data: IngestedMarkSchemesModel = route_and_extract_mark_schemes(raw_extracted_ms_list)

    # Save the final processed data
    job_output_dir.mkdir(parents=True, exist_ok=True) # Ensure output directory exists
    output_file_name = f"{job_id}_ingested_mark_scheme.json"
    final_output_path = job_output_dir / output_file_name

    with open(final_output_path, "w", encoding="utf-8") as f:
        # Use .model_dump_json() for Pydantic models for proper serialization
        f.write(processed_data.model_dump_json(indent=2))

    logger.info(f"Job {job_id}: Successfully ingested mark scheme. Saved to {final_output_path}")
    return final_output_path


# Remove or comment out the old if __name__ == "__main__": block
# if __name__ == "__main__":
#    # qualification_level = "GCSE"
#    # exam_board = "AQA"
#    # subject = "German" # Example
#    # index = 0
#
#    # This old main block is not suitable for Flask app.
#    # For testing, you'd call the refactored ingest_mark_scheme directly with appropriate paths.
#    # Example (conceptual, paths need to be valid):
#    # test_pdf_path = Path("path/to/your/test_ms.pdf")
#    # test_job_output_dir = Path("test_outputs/ms_ingestion_test_job")
#    # test_temp_image_dir = Path("test_temp_images")
#    # ingest_mark_scheme([test_pdf_path], test_job_output_dir, "test_job_001", test_temp_image_dir)
#    pass
