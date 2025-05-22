"""
assignment_ingestion_simplified.py
----------------------------------
* OCR (Mistral)  ->  markdown + image map
* LLM structuring (invoke_llm_for_structuring unchanged)
* Common–component de-duplication
    • "chart -> image" wrappers are flattened immediately:
        – pooled payload marked  component_type="chart"
        – no intermediate chart object kept
    • Dedup-keys are `"{ctype}:{key}"`, so chart/image versions stay separate.
* Writes
    ├─ modified_assessment.json
    └─ common_components.json
"""

# ──────────────────────────────────────────────────────────────────────────────
# Std-lib
import logging
import structlog
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
)

import base64, hashlib, json, mimetypes, os, re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

# ──────────────────────────────────────────────────────────────────────────────
# 3rd-party
from dotenv import load_dotenv
from mistralai import Mistral
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_community.callbacks.openai_info import OpenAICallbackHandler
from pydantic import BaseModel

from tenacity import retry, stop_after_attempt, wait_exponential_jitter


log = structlog.get_logger()

# ──────────────────────────────────────────────────────────────────────────────
# Local stubs (remove in production or ensure correct pathing)
# Assuming output.py and prompt_lib.py are in the same directory
# For Flask app, ensure these imports work relative to the csis_path
try:
    from .output import QuestionModelV3, ComponentType # Relative import
    from .prompt_lib import assignment_extraction_prompt_template_reasoning_v9 # Relative import
    logging.info("✅ Local modules imported (assignment_ingestion)")
except ImportError:
    logging.warning("⚠️ Using dummy local stubs for output.py / prompt_lib.py in assignment_ingestion")

    class ComponentType(str): # type: ignore
        IMAGE = "image"
        TEXT = "text"
        TABLE = "table"
        CHART = "chart"
        EQUATION = "equation"
        REFERENCE = "reference"

    class QuestionModelV3(BaseModel): # type: ignore
        pass
    assignment_extraction_prompt_template_reasoning_v9 = ( # type: ignore
        "Dummy prompt {assignment_text}"
    )

# ──────────────────────────────────────────────────────────────────────────────
# Load environment variables. Flask app should handle this at its root.
# load_dotenv(Path(__file__).resolve().parent.parent.parent / '.env') # Example: if .env is three levels up
# For simplicity, assume Flask app's load_dotenv covers this.

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    logging.warning("⚠️ MISTRAL_API_KEY not set – OCR will be skipped")

AZURE = {
    "gpt-4o": {
        "endpoint":   os.getenv("AZURE_OPENAI_ENDPOINT"),
        "version":    os.getenv("AZURE_OPENAI_VERSION"),
        "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    },
    "o3-mini": {
        "endpoint":   os.getenv("AZURE_OPENAI_ENDPOINT_O3"),
        "version":    os.getenv("AZURE_OPENAI_VERSION_O3"),
        "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_O3"),
    },
    "gpt-4.1": {
        "endpoint":   os.getenv("AZURE_OPENAI_ENDPOINT_4_1"),
        "version":    os.getenv("AZURE_OPENAI_VERSION_4_1"),
        "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_4_1"),
    },
    "o4-mini": {
        "endpoint":   os.getenv("AZURE_OPENAI_ENDPOINT_O4"),
        "version":    os.getenv("AZURE_OPENAI_VERSION_O4"),
        "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_O4"),
    },
    "key": os.getenv("AZURE_OPENAI_API_KEY"),
}

# logging.info(f"Azure gpt-4.1 version: {AZURE.get('gpt-4.1', {}).get('version')}")
# logging.info(f"Azure gpt-4.1 endpoint: {AZURE.get('gpt-4.1', {}).get('endpoint')}")
# logging.info(f"Azure gpt-4.1 deployment: {AZURE.get('gpt-4.1', {}).get('deployment')}")

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
DATA_URI_RE = re.compile(r"data:(image/[^;]+);base64,(.+)", re.I | re.S)


def safe_json_load(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        if "Invalid \\escape" not in str(err):
            raise
        # Attempt to fix common escape issues if possible, or re-raise
        try:
            return json.loads(text.encode().decode("unicode_escape"))
        except Exception as e:
            logging.error(f"JSON double decode failed: {e} for text: {text[:100]}...")
            raise err # re-raise original error


def parse_data_uri(uri: str) -> Optional[dict]:
    m = DATA_URI_RE.fullmatch(uri.strip())
    if not m:
        return None
    mime, b64 = m.groups()
    return {"extension": mime.split("/")[1].lower(), "base64": b64.replace("\n", "")}


def encode_image_to_base64(path: Path) -> Tuple[Optional[str], Optional[str]]:
    mime, _ = mimetypes.guess_type(path)
    if not (mime and mime.startswith("image/")):
        return None, None
    try:
        return base64.b64encode(path.read_bytes()).decode(), mime
    except FileNotFoundError:
        return None, None


def generate_hash(obj: Any) -> str:
    try:
        src = json.dumps(obj, sort_keys=True)
    except TypeError:
        src = str(obj)
    return hashlib.sha256(src.encode()).hexdigest()


class IdPool:
    def __init__(self, prefix: str):
        self.prefix, self._n = prefix, 1

    def next(self) -> str:
        cid = f"{self.prefix}_{self._n}"
        self._n += 1
        return cid


# ──────────────────────────────────────────────────────────────────────────────
# OCR
def extract_ocr(file_path: Path) -> Dict[str, Any]:
    if not MISTRAL_API_KEY:
        logging.error("MISTRAL_API_KEY not configured. OCR cannot proceed.")
        return {}
    if not file_path.exists():
        logging.error(f"OCR input file not found: {file_path}")
        return {}

    client = Mistral(api_key=MISTRAL_API_KEY)
    ext = file_path.suffix.lower()
    try:
        if ext == ".pdf":
            with file_path.open("rb") as f:
                up = client.files.upload(
                    file={"file_name": file_path.name, "content": f}, purpose="ocr"
                )
            # The signed URL is temporary, ensure processing happens quickly
            # For longer operations, consider re-fetching or a more persistent storage if Mistral supports it.
            url_response = client.files.get_signed_url(file_id=up.id)
            if not url_response or not url_response.url:
                 logging.error(f"Failed to get signed URL for Mistral file ID: {up.id}")
                 return {}
            url = url_response.url

            resp = client.ocr.process(
                model="mistral-ocr-latest",
                document={"type": "document_url", "document_url": url},
                include_image_base64=True,
            )
        elif ext in {".png", ".jpg", ".jpeg"}:
            b64, mime = encode_image_to_base64(file_path)
            if not b64 or not mime:
                logging.error(f"Failed to encode image to base64: {file_path}")
                return {}
            data_uri = f"data:{mime};base64,{b64}"
            resp = client.ocr.process(
                model="mistral-ocr-latest",
                document={"type": "image_url", "image_url": data_uri},
                include_image_base64=True,
            )
        else:
            logging.warning(f"Unsupported file type for OCR: {file_path}")
            return {}

        # The response from Mistral SDK's ocr.process is already a Pydantic model
        # To get a dictionary, use .model_dump()
        return resp.model_dump() if resp else {}

    except Exception as e:
        logging.error("OCR failed for %s: %s", file_path, e)
        import traceback
        traceback.print_exc()
        return {}


# ──────────────────────────────────────────────────────────────────────────────
# OCR -> markdown + image map
def markdown_from_ocr(
    pages: List[Dict[str, Any]],
) -> Tuple[str, Dict[str, Dict[str, str]]]:
    image_store: Dict[str, Dict[str, str]] = {}
    md_segments = []
    img_pool = IdPool("image") # Use a consistent prefix for image references

    for i, page in enumerate(pages):
        markdown = page.get("markdown", "") or ""
        # Ensure images from OCR are correctly mapped
        for img_idx, img_data in enumerate(page.get("images", []) or []):
            b64_uri = img_data.get("image_base64")
            ocr_img_id = img_data.get("id") # The ID Mistral OCR gives to the image

            if not b64_uri or not ocr_img_id:
                logging.warning(f"Page {i+1}, Image {img_idx+1}: Missing base64 or OCR ID.")
                continue

            # Generate a new, consistent key for our image_store
            internal_image_key = img_pool.next()

            parsed_uri = parse_data_uri(b64_uri)
            if parsed_uri:
                image_store[internal_image_key] = parsed_uri
            else:
                # Fallback if parse_data_uri fails, store raw (but this shouldn't happen with Mistral's output)
                image_store[internal_image_key] = {"base64": b64_uri, "extension": "png"} # Assume png if not parsable
                logging.warning(f"Could not parse data URI for image {ocr_img_id} on page {i+1}. Storing raw base64.")

            # Replace the ![...](ocr_img_id) in markdown with ![internal_image_key](internal_image_key)
            # Escape ocr_img_id for regex, as it might contain special characters
            escaped_ocr_img_id = re.escape(ocr_img_id)
            # Regex to find ![any alt text](ocr_img_id)
            markdown = re.sub(
                rf"!\[[^\]]*\]\({escaped_ocr_img_id}\)",
                f"![{internal_image_key}]({internal_image_key})", # Use internal key for both alt and ref
                markdown,
            )
        md_segments.append(markdown)

    return "\n\n---\n\n".join(md_segments), image_store


# ──────────────────────────────────────────────────────────────────────────────
# LLM helpers
def get_llm(model_name: str) -> Optional[AzureChatOpenAI]:
    conf = AZURE.get(model_name)
    if not conf or not conf.get("endpoint") or not conf.get("version") or not conf.get("deployment") or not AZURE.get("key"):
        logging.error(f"Azure OpenAI configuration missing or incomplete for model: {model_name}")
        return None

    # logging.info(f"Initializing LLM: {model_name} with endpoint: {conf['endpoint']}")
    params = dict(
        azure_endpoint=conf["endpoint"],
        api_key=AZURE["key"],
        api_version=conf["version"],
        azure_deployment=conf["deployment"],
        # model=model_name, # model_name is often implicit in deployment, but can be specified
        temperature=0, # Keep temperature at 0 for structured extraction
        callbacks=[OpenAICallbackHandler()],
    )
    # "reasoning_effort" is not a standard Langchain AzureChatOpenAI parameter.
    # If it's specific to a custom deployment or version, it might need special handling.
    # For now, removing it to ensure compatibility with standard Langchain.
    # if model_name in {"o3-mini", "o4-mini"}:
    #     params["reasoning_effort"] = "medium"
    #     params["temperature"] = 1 # As per original code for these models

    try:
        return AzureChatOpenAI(**params)
    except Exception as e:
        logging.error("LLM init error for %s: %s", model_name, e)
        return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=10, max=60, jitter=5), reraise=True)
def invoke_llm(
    assignment_text: str,
    prompt_template_str: str,
    output_schema: Type[BaseModel], # Use Type[BaseModel] for Pydantic model classes
    model_name: str = "gpt-4.1",
) -> Optional[Dict[str, Any]]:
    llm = get_llm(model_name)
    if not llm:
        logging.error(f"Failed to get LLM instance for model: {model_name}")
        return None
    try:
        parser = JsonOutputParser(pydantic_object=output_schema)

        # Format the prompt template with the assignment text
        # The original prompt_lib.py uses {format_instructions} which langchain populates
        # If your prompt_lib.py prompt already includes format instructions or is designed
        # for direct use, this is fine. Otherwise, you might need:
        # prompt_template = ChatPromptTemplate.from_template(
        #     template=prompt_template_str,
        #     partial_variables={"format_instructions": parser.get_format_instructions()}
        # )
        # messages = prompt_template.format_messages(assignment_text=assignment_text)

        # Simpler formatting if prompt_template_str is basic:
        prompt_content = prompt_template_str.format(
            assignment_text=assignment_text,
            format_instructions=parser.get_format_instructions() # Add format instructions
        )
        messages = [HumanMessage(content=prompt_content)]

        chain = llm | parser # No need for ChatPromptTemplate if messages are constructed directly

        logging.info(f"Invoking LLM {model_name} for assignment structuring...")
        response = chain.invoke(messages) # Pass messages to invoke for newer Langchain versions

        # logging.info("LLM response received (first 100 chars): %s", json.dumps(response, indent=2)[:100])
        return response # response should already be a dict parsed by JsonOutputParser
    except Exception as e:
        logging.error("LLM invocation error during assignment structuring: %s", e)
        import traceback
        traceback.print_exc()
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Component de-duplication
def deduplicate_components(
    structured: Dict[str, Any],
    image_map: Dict[str, Dict[str, str]], # image_map: internal_key -> {base64, extension}
) -> Tuple[Dict[str, Any], Dict[str, Any]]:

    # Ensure ComponentType is the Enum, not the string "ComponentType"
    # This should be handled by correct import from .output
    pools = {ct: IdPool(ct.value) for ct in ComponentType}
    common_components_pool: Dict[str, Any] = {} # Stores the actual component data, keyed by new CID
    dedup_map: Dict[str, str] = {}  # composite_key (type:hash or type:ref) -> new_cid

    def _get_composite_key(ctype: ComponentType, original_key_or_data: Any) -> str:
        """Generates a key for deduplication. For images/charts, it's based on original_key. For others, hash of data."""
        if ctype == ComponentType.IMAGE or ctype == ComponentType.CHART:
            # original_key_or_data is the reference like "image_1" from markdown_from_ocr's image_map
            return f"{ctype.value}:{original_key_or_data}"
        else:
            # original_key_or_data is the actual component data (e.g., text string, table markdown)
            return f"{ctype.value}:{generate_hash(original_key_or_data)}"

    def _record_component(
        ctype: ComponentType,
        original_key_or_data: Any, # For IMAGE/CHART, this is the key from image_map (e.g. "image_1")
                                   # For TEXT/TABLE/EQUATION, this is the actual data (e.g. text string)
        payload_supplier # A function that returns the payload if this is a new component
    ) -> str: # Returns the new Component ID (CID)

        composite_key = _get_composite_key(ctype, original_key_or_data)

        if composite_key not in dedup_map:
            new_cid = pools[ctype].next()
            dedup_map[composite_key] = new_cid

            # The payload for common_components_pool should be the final storable form
            # For images/charts, this comes from image_map. For others, it's the data itself.
            if ctype == ComponentType.IMAGE or ctype == ComponentType.CHART:
                # original_key_or_data is the key for image_map
                img_data_from_map = image_map.get(str(original_key_or_data))
                if not img_data_from_map:
                    logging.error(f"Consistency error: Image key {original_key_or_data} not found in image_map during deduplication.")
                    # Handle error: perhaps store a placeholder or skip
                    # For now, let's create a placeholder to avoid crashing
                    common_components_pool[new_cid] = {"component_type": ctype.value, "error": "source_data_missing", "original_key": original_key_or_data}
                else:
                    common_components_pool[new_cid] = {"component_type": ctype.value, **img_data_from_map}
            else:
                # For TEXT, TABLE, EQUATION, the payload is constructed from original_key_or_data
                # The payload_supplier is not strictly needed here if original_key_or_data is the content
                common_components_pool[new_cid] = {"component_type": ctype.value, "component": {"type": "text", "data": original_key_or_data}}

        return dedup_map[composite_key]

    modified_structured_assessment = json.loads(json.dumps(structured)) # Deep copy

    for q_idx, q_content in enumerate(modified_structured_assessment.get("questions", [])):
        new_question_context = []
        for comp_wrapper in q_content.get("question_context", []):
            try:
                # component_type_str is from LLM output, e.g., "image", "text"
                component_type_str = comp_wrapper.get("component_type")
                llm_component_data = comp_wrapper.get("component", {}) # This is the component object from LLM

                # Validate component_type_str against our Enum
                try:
                    ctype_enum_val = ComponentType(component_type_str)
                except ValueError:
                    logging.warning(f"Invalid component_type '{component_type_str}' in Q{q_idx}. Skipping this context item.")
                    new_question_context.append(comp_wrapper) # Keep as is if invalid
                    continue

                new_cid = ""

                if ctype_enum_val == ComponentType.IMAGE or ctype_enum_val == ComponentType.CHART:
                    # LLM output for image/chart should be: {"type": "reference", "reference": "image_X"}
                    # where "image_X" is the key from markdown_from_ocr's image_map
                    if llm_component_data.get("type") == "reference" and isinstance(llm_component_data.get("reference"), str):
                        image_map_key = llm_component_data["reference"]
                        if image_map_key not in image_map:
                            logging.warning(f"LLM referenced image key '{image_map_key}' not found in OCR image_map for Q{q_idx}. Keeping original.")
                            new_question_context.append(comp_wrapper) # Keep original if ref is broken
                            continue
                        # The original_key_or_data for _record_component is image_map_key
                        new_cid = _record_component(ctype_enum_val, image_map_key, lambda: image_map.get(image_map_key))
                    else:
                        logging.warning(f"Malformed IMAGE/CHART component from LLM for Q{q_idx}: {llm_component_data}. Keeping original.")
                        new_question_context.append(comp_wrapper)
                        continue

                elif ctype_enum_val == ComponentType.TEXT:
                    # LLM output for text: {"type": "text", "data": "actual text..."}
                    if llm_component_data.get("type") == "text" and isinstance(llm_component_data.get("data"), str):
                        text_data = llm_component_data["data"]
                        # The original_key_or_data for _record_component is text_data itself
                        new_cid = _record_component(ctype_enum_val, text_data, lambda: {"component": {"type": "text", "data": text_data}})
                    else:
                        logging.warning(f"Malformed TEXT component from LLM for Q{q_idx}: {llm_component_data}. Keeping original.")
                        new_question_context.append(comp_wrapper)
                        continue

                elif ctype_enum_val in [ComponentType.TABLE, ComponentType.EQUATION]:
                     # LLM output for table/equation: {"type": "text", "data": "markdown_table_or_equation_string"}
                    if llm_component_data.get("type") == "text" and isinstance(llm_component_data.get("data"), str):
                        content_data = llm_component_data["data"]
                        # The original_key_or_data for _record_component is content_data itself
                        new_cid = _record_component(ctype_enum_val, content_data, lambda: {"component": {"type": "text", "data": content_data}})
                    else:
                        logging.warning(f"Malformed {ctype_enum_val.value.upper()} component from LLM for Q{q_idx}: {llm_component_data}. Keeping original.")
                        new_question_context.append(comp_wrapper)
                        continue
                else:
                    # Should not happen if ctype_enum_val is validated
                    logging.error(f"Unhandled component type '{ctype_enum_val}' during deduplication for Q{q_idx}.")
                    new_question_context.append(comp_wrapper)
                    continue

                # Replace the original component wrapper with a reference to the common component
                new_question_context.append({
                    "component_type": ComponentType.REFERENCE.value, # This context item is now a reference
                    "component": {"type": "reference", "reference": new_cid}
                })

            except Exception as e:
                logging.error(f"Error processing component in Q{q_idx}: {comp_wrapper}. Error: {e}")
                new_question_context.append(comp_wrapper) # Add original back on error

        q_content["question_context"] = new_question_context

    return common_components_pool, modified_structured_assessment


# ──────────────────────────────────────────────────────────────────────────────
# Orchestration
@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=15, max=90, jitter=10), reraise=True)
def ingest_assignment(
    files: List[Path], # List of Path objects to uploaded files (PDF or images)
    llm_model: str = os.getenv("ASSIGNMENT_LLM_MODEL", "gpt-4.1"), # Get model from env or default
) -> Tuple[Dict[str, Any], Dict[str, Any]]:

    if not files:
        logging.error("No files provided for assignment ingestion.")
        # Return empty structures or raise error, depending on desired handling
        return {}, {}

    all_ocr_pages = []
    for file_path in files:
        if not file_path.exists():
            logging.warning(f"File not found: {file_path}, skipping.")
            continue
        logging.info(f"Processing file for OCR: {file_path.name}")
        ocr_result = extract_ocr(file_path)
        if ocr_result and "pages" in ocr_result:
            all_ocr_pages.extend(ocr_result["pages"])
        else:
            logging.warning(f"No pages extracted from OCR for file: {file_path.name}")

    if not all_ocr_pages:
        logging.error("OCR produced no pages from any of the provided files.")
        return {}, {} # Return empty dicts if no OCR content

    logging.info(f"Total pages from OCR: {len(all_ocr_pages)}")
    markdown_content, image_map = markdown_from_ocr(all_ocr_pages)

    if not markdown_content.strip():
        logging.warning("Markdown content from OCR is empty. Skipping LLM structuring.")
        structured_assessment = {"questions": []}
    else:
        logging.info("Invoking LLM for structuring assignment from Markdown...")
        structured_assessment = invoke_llm(
            assignment_text=markdown_content,
            prompt_template_str=assignment_extraction_prompt_template_reasoning_v9,
            output_schema=QuestionModelV3, # Pass the Pydantic model class itself
            model_name=llm_model,
        )
        if not structured_assessment:
            logging.error("LLM structuring failed to return data. Proceeding with empty assessment.")
            structured_assessment = {"questions": []}
            # Optionally, could return the raw markdown and image_map here for debugging or partial success
            # return {"raw_markdown": markdown_content, "image_map": image_map, "error": "LLM_failed"}, {}


    logging.info("Deduplicating components...")
    common_components, modified_assessment = deduplicate_components(structured_assessment, image_map)

    logging.info("Assignment ingestion process completed.")
    return modified_assessment, common_components


# ──────────────────────────────────────────────────────────────────────────────
# Save helpers & CLI (CLI part will be removed/commented for Flask app)

# MODIFIED: save_results now takes output_dir
def save_results(modified: Dict[str, Any], common: Dict[str, Any], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True) # Ensure output_dir exists

    (output_dir / "modified_assessment.json").write_text(
        json.dumps(modified, indent=4, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "common_components.json").write_text(
        json.dumps(common, indent=4, ensure_ascii=False), encoding="utf-8"
    )
    logging.info("✅ Assignment results saved to %s", output_dir.resolve())


# The main() and if __name__ == "__main__": block should be removed or commented out
# as this script will be imported as a module by the Flask app.

# def main():
#     # This is example usage, paths would come from Flask app
#     inputs = [
#         Path("path/to/your/test_file.pdf"),
#     ]
#     if not inputs[0].exists():
#         logging.error("Input file missing: %s", inputs[0])
#         return

#     # Example: Define where to save results for this standalone run
#     # For Flask, this output_dir would be job-specific
#     standalone_output_dir = Path("outputs_standalone_assignment")

#     modified, common = ingest_assignment(inputs, llm_model="gpt-4.1") # Use configured model
#     save_results(modified, common, standalone_output_dir)


# if __name__ == "__main__":
#     # Configure logging for standalone run
#     # logging.basicConfig(level=logging.DEBUG) # More verbose for standalone
#     # main()
#     pass # No standalone execution from Flask app
