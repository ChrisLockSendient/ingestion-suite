import json
from .infer_openai import invoke_openai
from .helpers import pdf_to_images, fetch_test_file_path, load_image_as_data_url, collapse_entries
from typing import List
from pathlib import Path
from azure.ai.inference.models import ImageContentItem, ImageUrl, UserMessage
from .prompt_lib import extract_mark_schemes_from_image_and_classify_prompt
from .output import ExtractedMarkSchemesInformationWrapper
from .few_shot_examples import extract_mark_schemes_from_image_and_classify_example_output_1, extract_mark_schemes_from_image_and_classify_example_output_2

def extract_mark_scheme_information_from_images_openai(images: List[Path], prompt: str, model_name: str) -> ExtractedMarkSchemesInformationWrapper:
    all_mark_schemes = []
    for image in images:
        data_url = load_image_as_data_url(image)

        user_message = UserMessage(content=[ImageContentItem(image_url=ImageUrl(url=data_url))])
        extracted_markscheme_json = json.loads(invoke_openai(prompt, model_name, output_format=ExtractedMarkSchemesInformationWrapper, payload=[user_message]))
        all_mark_schemes.extend(extracted_markscheme_json["mark_schemes"])
    return collapse_entries(all_mark_schemes)


def extract_tables_from_images_and_save_openai(images: List[Path], prompt: str, model_name: str, output_file_name: str) -> ExtractedMarkSchemesInformationWrapper:
    all_mark_schemes = []
    for image in images:
        data_url = load_image_as_data_url(image)
        user_message = UserMessage(content=[ImageContentItem(image_url=ImageUrl(url=data_url))])
        extracted_markscheme_json = json.loads(invoke_openai(prompt, model_name, output_format=ExtractedMarkSchemesInformationWrapper, payload=[user_message]))
        all_mark_schemes.extend(extracted_markscheme_json["mark_schemes"])
    with open(f"test_output/{output_file_name}.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(all_mark_schemes, indent=4))
    return all_mark_schemes

# if __name__ == "__main__":
#     qualification_level = "GCSE"
#     exam_board = "AQA"
#     subject = "Chemistry"
#     index = 0

#     pdf = fetch_test_file_path(qualification_level, exam_board, subject, index=index)
#     images = pdf_to_images(pdf)

#     # images = [Path("test_data/Rubrics/rubric1.jpg")]

#     prompt = extract_mark_schemes_from_image_and_classify_prompt.format(
#         example_output_1=json.dumps(extract_mark_schemes_from_image_and_classify_example_output_1, indent=4),
#         example_output_2=json.dumps(extract_mark_schemes_from_image_and_classify_example_output_2, indent=4)
#     )

#     from datetime import datetime

#     current_time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
#     output_file_name = f"{qualification_level}_{exam_board}_{subject}_{index}_extracted_json_openai_{current_time_str}"
#     extracted_markscheme_table_openai = extract_mark_scheme_information_from_images_openai(
#         images,
#         prompt,
#         model_name="gpt-4.1",
#         output_file_name=output_file_name
#     )

    # Route and extract mark schemes by type
    # extraction_results = route_and_extract_mark_schemes(extracted_markscheme_table_openai)

    # print(extraction_results)
