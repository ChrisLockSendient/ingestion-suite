#!/usr/bin/env python3
"""
match_ms_to_question.py  –  token-aware matcher (2025-05)
========================================================

Usage (from another script or REPL):
    from match_ms_to_question import main

    # by path:
    main("assessment.json", "mark_schemes.json")

    # or, if you've already loaded JSON:
    main(questions_list, mark_schemes_list, threshold=0.65, top_k=5)
"""

from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any, List, Tuple, Dict, Union, Optional # Added Union

import numpy as np
from pydantic import BaseModel, Field # Added Field for potential future use
from rapidfuzz.fuzz import token_set_ratio, partial_ratio
from scipy.optimize import linear_sum_assignment
from tabulate import tabulate
import logging

# ──────────────────────── logging config ─────────────────────────
logging.basicConfig(
    level=logging.INFO, # Consider making this configurable via env var for Flask
    format="%(levelname)s:%(name)s:%(message)s"
)
log = logging.getLogger("ms_matcher") # Renamed logger for clarity

# ───────────────────────────── models ─────────────────────────────
# These Pydantic models should ideally be imported from a shared location
# if they are identical to those in assignment_ingestion/output.py or mark_scheme_ingestion/output.py
# For now, defining them here as per the original structure of this file.

class OneQuestionModelV3(BaseModel):
    question_id: str
    question: str
    question_type: str # Consider Enum if defined elsewhere
    total_marks_available: Optional[float] = None # Made optional with default None

class IngestedMarkSchemeModel(BaseModel):
    type: str # e.g., "generic", "levelled", "rubric"
    question_number: str
    question_text: Optional[str] = None
    marks_available: Optional[int] = None
    mark_scheme_information: Optional[str] = "" # Raw text of MS for this q
    # The 'mark_scheme' field (detailed structured MS) is not used by this matcher directly,
    # but would be part of the full IngestedMarkSchemeModel if loaded from the output of ingest_mark_scheme.py
    # For matching, only question_number, question_text, marks_available are primarily used from MS.

# ──────────────────────── tokenisation helper ─────────────────────
_ROMAN = [
    "xviii","xvii","xvi","xv","xiv","xiii","xii","xi",
    "viii","vii","vi","iv","ix","iii","ii","i"
]
def tokenize_id(raw: str) -> List[str]:
    """Convert any question ID into an ordered list of semantic tokens."""
    if not raw:
        return []
    s = raw.lower() # Start with lowercase
    # Replace common delimiters with a single '#'
    s = re.sub(r"[.\(\)\s_\-]+", "#", s)
    # Remove any characters that are not alphanumeric or '#'
    s = re.sub(r"[^0-9a-z#]+", "", s)

    toks_raw, buf = [], ""
    current_type = None # 'digit' or 'alpha'

    for ch in s:
        if ch == "#":
            if buf:
                toks_raw.append(buf)
            buf = ""
            current_type = None
        else:
            ch_type = 'digit' if ch.isdigit() else 'alpha'
            if not buf: # Starting a new buffer
                buf += ch
                current_type = ch_type
            elif ch_type == current_type: # Same type, append
                buf += ch
            else: # Type changed, finalize previous buffer and start new
                if buf:
                    toks_raw.append(buf)
                buf = ch
                current_type = ch_type
    if buf: # Append any remaining buffer
        toks_raw.append(buf)

    out: List[str] = []
    for tok in toks_raw:
        # No need to lower again as 's' was already lowered
        if tok.isdigit():
            # Convert to int then str to remove leading zeros, e.g., "01" -> "1"
            out.append(str(int(tok)))
            continue

        # Roman numeral splitting (more robustly handle cases like "aiv" vs "a" + "iv")
        # This part can be complex if prefixes mix with roman numerals.
        # The original logic splits if a known roman numeral is a suffix.
        found_roman_suffix = False
        for roman in _ROMAN: # Check longer roman numerals first
            if tok.endswith(roman):
                prefix = tok[:-len(roman)]
                if prefix: # If there's a part before the roman numeral
                    # Check if prefix is purely alpha or purely digit to avoid splitting mid-token like "qiv" into "q" + "iv"
                    # This check might need refinement based on typical ID patterns.
                    # For now, assume if prefix exists, it's a separate part.
                    out.append(prefix)
                out.append(roman)
                found_roman_suffix = True
                break
        if not found_roman_suffix:
            out.append(tok)

    return [t for t in out if t] # Filter out any empty strings

# ───────────────────────── text helpers ──────────────────────────
_WORD_RE = re.compile(r"[a-z0-9]+") # Find alphanumeric sequences
def canonical_text(t: Optional[str]) -> str:
    """Converts text to a canonical form for comparison: lowercase, alphanumeric, limited length."""
    if not t:
        return ""
    # Take first 120 chars of the lowercased, tokenized string
    return " ".join(_WORD_RE.findall(t.lower()))[:120]

def text_similarity(a: Optional[str], b: Optional[str]) -> float:
    """
    Combined similarity using token_set_ratio, partial_ratio, and subset-Jaccard.
    Returns max of the three on [0,1].
    """
    if not a or not b: # If either string is empty or None
        return 0.0

    a_can = canonical_text(a)
    b_can = canonical_text(b)

    if not a_can or not b_can: # If canonical forms are empty
        return 0.0

    tsr_score  = token_set_ratio(a_can, b_can) / 100.0
    pr_score   = partial_ratio(a_can, b_can) / 100.0

    # Subset Jaccard: proportion of shorter text's tokens found in longer text's tokens
    tokens_a, tokens_b = set(a_can.split()), set(b_can.split())
    if not tokens_a or not tokens_b: # Avoid division by zero if one set is empty
        jaccard_subset_score = 0.0
    else:
        intersection_len = len(tokens_a.intersection(tokens_b))
        min_len = min(len(tokens_a), len(tokens_b))
        jaccard_subset_score = intersection_len / max(1, min_len) # max(1, min_len) to avoid div by zero if min_len is 0

    return max(tsr_score, pr_score, jaccard_subset_score)

def mark_proximity(q_marks: Optional[float], ms_marks: Optional[int]) -> float:
    """Calculates similarity of marks. Returns 0.0 if either is None or ms_marks is 0."""
    if q_marks is None or ms_marks is None or ms_marks == 0:
        return 0.0
    # Normalize difference by ms_marks
    return 1.0 - abs(q_marks - float(ms_marks)) / float(ms_marks)


# ───────────────────────── scoring weights ───────────────────────
# These weights determine the importance of each matching signal.
WEIGHTS = {
    "token_exact": 0.35, # Exact match of tokenized IDs
    "root":        0.20, # Match of the first token (often main question number)
    "prefix":      0.10, # Longest common prefix of tokenized IDs
    "jaccard":     0.05, # Jaccard similarity of ID token sets
    "text":        0.25, # Text similarity between question and MS text
    "marks":       0.05, # Proximity of marks available
    "type_hint":   0.00, # (Currently unused) Hint based on question type vs MS type
}

def token_signals(tokens_q: List[str], tokens_ms: List[str]) -> Tuple[float, float, float, float]:
    """Calculates various similarity signals based on tokenized IDs."""
    exact_match_score = 1.0 if tokens_q == tokens_ms else 0.0

    root_match_score = 0.0
    if tokens_q and tokens_ms and tokens_q[0] == tokens_ms[0] and tokens_q[0].isdigit():
        root_match_score = 1.0

    lcp_len = 0
    for token_a, token_b in zip(tokens_q, tokens_ms):
        if token_a == token_b:
            lcp_len += 1
        else:
            break
    max_len = max(len(tokens_q), len(tokens_ms), 1) # Avoid division by zero
    prefix_match_score = lcp_len / max_len

    set_q, set_ms = set(tokens_q), set(tokens_ms)
    intersection_len = len(set_q.intersection(set_ms))
    union_len = len(set_q.union(set_ms))
    jaccard_score = intersection_len / max(1, union_len) # Avoid division by zero

    return exact_match_score, root_match_score, prefix_match_score, jaccard_score

def pair_score(q: OneQuestionModelV3, ms: IngestedMarkSchemeModel) -> float:
    """Calculates the overall match score between a question and a mark scheme item."""
    tokens_q = tokenize_id(q.question_id)
    tokens_ms = tokenize_id(ms.question_number) # MS uses 'question_number' for its ID

    exact_sig, root_sig, prefix_sig, jaccard_sig = token_signals(tokens_q, tokens_ms)

    marks_similarity = mark_proximity(q.total_marks_available, ms.marks_available)

    # Type hint (currently weighted at 0, but logic kept for potential future use)
    type_hint_similarity = 0.0
    if q.question_type == "multiple_choice" and ms.type == "generic":
        type_hint_similarity = 1.0

    # Text similarity: use question text from assessment and question_text or mark_scheme_information from MS
    q_text_content = q.question.strip() if q.question else ""
    # Prefer ms.question_text if available, fallback to ms.mark_scheme_information
    ms_text_content = (ms.question_text or ms.mark_scheme_information or "").strip()

    has_comparable_text = bool(q_text_content and ms_text_content)
    text_sim_score = text_similarity(q_text_content, ms_text_content) if has_comparable_text else 0.0

    # Adjust weights if text is not comparable (e.g., one is empty)
    current_weights = WEIGHTS.copy()
    if not has_comparable_text:
        # If no text to compare, remove text weight and re-normalize others
        if "text" in current_weights:
            current_weights.pop("text")

    total_weight = sum(current_weights.values())
    if total_weight == 0: return 0.0 # Avoid division by zero if all weights become zero

    score = (
        current_weights.get("token_exact", 0) * exact_sig +
        current_weights.get("root", 0)        * root_sig  +
        current_weights.get("prefix", 0)      * prefix_sig +
        current_weights.get("jaccard", 0)     * jaccard_sig +
        (current_weights.get("text", 0)       * text_sim_score if has_comparable_text else 0) +
        current_weights.get("marks", 0)       * marks_similarity +
        current_weights.get("type_hint", 0)   * type_hint_similarity
    ) / total_weight

    if log.isEnabledFor(logging.DEBUG) and has_comparable_text :
        text_contribution_val = (current_weights.get("text", 0) * text_sim_score) / total_weight
        log.debug(
            "TextSim Q_ID=%s MS_ID=%s | Q_text='%.30s...' MS_text='%.30s...' | Sim=%.3f Contrib=%.3f",
            q.question_id, ms.question_number, q_text_content, ms_text_content, text_sim_score, text_contribution_val
        )
    return score

def text_contribution(q: OneQuestionModelV3, ms: IngestedMarkSchemeModel) -> Tuple[float, float]:
    """Helper to get text similarity and its contribution to the score for verbose output."""
    q_text_content = q.question.strip() if q.question else ""
    ms_text_content = (ms.question_text or ms.mark_scheme_information or "").strip()

    if not (q_text_content and ms_text_content):
        return 0.0, 0.0

    s_text = text_similarity(q_text_content, ms_text_content)

    # Calculate contribution based on whether text weight is active
    current_weights = WEIGHTS.copy()
    total_w = sum(current_weights.values())
    if total_w == 0: return s_text, 0.0

    contrib = (current_weights.get("text", 0) * s_text) / total_w
    return s_text, contrib

def build_score_matrix(questions_list: List[OneQuestionModelV3], mark_schemes_list: List[IngestedMarkSchemeModel]) -> np.ndarray:
    """Builds a matrix of pair_score between all questions and mark schemes."""
    num_questions = len(questions_list)
    num_mark_schemes = len(mark_schemes_list)

    score_matrix = np.zeros((num_questions, num_mark_schemes), dtype=float)

    for i, q_item in enumerate(questions_list):
        for j, ms_item in enumerate(mark_schemes_list):
            score_matrix[i, j] = pair_score(q_item, ms_item)

    return score_matrix

def pad_with_dummies(score_matrix: np.ndarray, threshold_value: float) -> Tuple[np.ndarray, int, int]:
    """Pads the score matrix to be square for the assignment algorithm, using a low dummy score."""
    nq, nms = score_matrix.shape
    dim = max(nq, nms)

    # Padded matrix filled with a score slightly below threshold to make dummies unattractive
    padded_matrix = np.full((dim, dim), threshold_value - 1e-6)
    padded_matrix[:nq, :nms] = score_matrix # Copy original scores

    return padded_matrix, nq, nms

def get_best_col_and_score(row_scores: np.ndarray) -> Tuple[int, float]:
    """Finds the column index and score of the best match in a row."""
    if row_scores.size == 0:
        return -1, 0.0 # No scores to check
    best_j_index = int(np.argmax(row_scores))
    return best_j_index, float(row_scores[best_j_index])

def match(
    questions_list: List[OneQuestionModelV3],
    mark_schemes_list: List[IngestedMarkSchemeModel],
    threshold: float = 0.60,
    top_k: int = 3,
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """
    Core matching logic. Returns a list of match dictionaries.
    If verbose=True, prints detailed scoring tables to the log.
    """
    if not questions_list or not mark_schemes_list:
        log.info("Empty questions list or mark schemes list provided for matching.")
        return []

    log.info(f"Starting matching: {len(questions_list)} questions, {len(mark_schemes_list)} mark schemes. Threshold={threshold}")

    score_matrix = build_score_matrix(questions_list, mark_schemes_list)

    if verbose and log.isEnabledFor(logging.INFO): # Use INFO for table output if verbose
        log.info("\n=== Top candidate scores per question (before assignment) ===")
        for i, q_item in enumerate(questions_list):
            # Get top_k scores and their original indices for this question row
            if score_matrix.shape[1] == 0: # No mark schemes
                log.info(f"\nQuestion {q_item.question_id}: No mark schemes to compare against.")
                continue

            top_indices = np.argsort(score_matrix[i, :])[::-1][:top_k] # Sort descending

            table_rows = []
            for j_idx in top_indices:
                if j_idx < len(mark_schemes_list): # Ensure index is valid
                    ms_item = mark_schemes_list[j_idx]
                    s_text_val, d_text_val = text_contribution(q_item, ms_item)
                    table_rows.append([
                        ms_item.question_number,
                        f"{score_matrix[i, j_idx]:.3f}",
                        f"{s_text_val:.3f}",
                        f"{d_text_val:.3f}"
                    ])
            if table_rows:
                log.info(f"\nQuestion {q_item.question_id} (Text: '{canonical_text(q_item.question)[:50]}...')")
                log.info(tabulate(
                    table_rows,
                    headers=["Candidate MS ID", "Score", "Text Sim.", "Δ(Text)"],
                    tablefmt="grid"
                ))
            else:
                 log.info(f"\nQuestion {q_item.question_id}: No valid candidates to display.")


    # Hungarian algorithm for optimal assignment
    # We want to maximize scores, so we use (1.0 - score) for cost minimization.
    cost_matrix, num_q_orig, num_ms_orig = pad_with_dummies(1.0 - score_matrix, 1.0 - threshold)
    row_indices, col_indices = linear_sum_assignment(cost_matrix)

    final_matches: List[Dict[str, Any]] = []
    assigned_question_indices = set()

    for r_idx, c_idx in zip(row_indices, col_indices):
        # Only consider assignments within the original matrix dimensions
        if r_idx < num_q_orig and c_idx < num_ms_orig:
            original_score = score_matrix[r_idx, c_idx]
            if original_score >= threshold:
                final_matches.append({
                    "question_id": questions_list[r_idx].question_id,
                    "mark_scheme_question_number": mark_schemes_list[c_idx].question_number,
                    "score": round(original_score, 3)
                })
                assigned_question_indices.add(r_idx)
            # else: assignment below threshold, will be handled as unmatched

    # Handle questions not assigned an above-threshold match by the algorithm
    for i, q_item in enumerate(questions_list):
        if i not in assigned_question_indices:
            # Find the best possible score for this unmatched question, even if below threshold
            if score_matrix.shape[1] > 0: # If there are mark schemes to compare against
                best_ms_idx, best_score_for_q = get_best_col_and_score(score_matrix[i, :])
                note = "no match ≥ threshold" if best_score_for_q < threshold else "optimal assignment was lower priority"
                final_matches.append({
                    "question_id": q_item.question_id,
                    "mark_scheme_question_number": mark_schemes_list[best_ms_idx].question_number if best_ms_idx != -1 else None, # Best attempt
                    "score": round(best_score_for_q, 3),
                    "note": note
                })
            else: # No mark schemes at all
                 final_matches.append({
                    "question_id": q_item.question_id,
                    "mark_scheme_question_number": None,
                    "score": 0.0,
                    "note": "no mark schemes to match against"
                })

    log.info(f"Matching process completed. Found {len([m for m in final_matches if m.get('note') is None])} confident matches.")
    return final_matches

# ─────────────────────────── public API (modified for Flask) ──────────────────────────
# MODIFIED: main function to be callable by Flask app
def main(
    assessment_source: Union[str, Path, List[Dict[str, Any]], Dict[str, Any]],
    mark_scheme_source: Union[str, Path, List[Dict[str, Any]], Dict[str, Any]],
    threshold: float = 0.60,
    top_k: int = 3,
    verbose: bool = True # Flask app will likely set this to False
) -> List[Dict[str, Any]]: # Ensure it returns the list of matches
    """
    Loads assessment questions and mark schemes, runs the matching algorithm,
    and returns the list of match results.
    Sources can be file paths or pre-loaded data (list of dicts or dict containing the list).
    """

    # --- Load Assessment Data ---
    qs_data_list: List[Dict[str, Any]]
    if isinstance(assessment_source, (str, Path)):
        log.info(f"Loading assessment data from path: {assessment_source}")
        with open(assessment_source, 'r', encoding='utf-8') as f:
            loaded_ass_data = json.load(f)
        # Handle if root is list of questions or a dict with 'questions' key
        qs_data_list = loaded_ass_data.get("questions", loaded_ass_data) if isinstance(loaded_ass_data, dict) else loaded_ass_data
    elif isinstance(assessment_source, dict): # Pre-loaded dict
        qs_data_list = assessment_source.get("questions", [])
    elif isinstance(assessment_source, list): # Pre-loaded list
        qs_data_list = assessment_source
    else:
        log.error("Invalid assessment_source type.")
        return []

    # --- Load Mark Scheme Data ---
    ms_data_list: List[Dict[str, Any]]
    if isinstance(mark_scheme_source, (str, Path)):
        log.info(f"Loading mark scheme data from path: {mark_scheme_source}")
        with open(mark_scheme_source, 'r', encoding='utf-8') as f:
            loaded_ms_data = json.load(f)
        # Handle if root is list of mark_schemes or a dict with 'mark_schemes' key
        ms_data_list = loaded_ms_data.get("mark_schemes", loaded_ms_data) if isinstance(loaded_ms_data, dict) else loaded_ms_data
    elif isinstance(mark_scheme_source, dict): # Pre-loaded dict
        ms_data_list = mark_scheme_source.get("mark_schemes", [])
    elif isinstance(mark_scheme_source, list): # Pre-loaded list
        ms_data_list = mark_scheme_source
    else:
        log.error("Invalid mark_scheme_source type.")
        return []

    # Validate that we have lists of dictionaries
    if not isinstance(qs_data_list, list) or not all(isinstance(item, dict) for item in qs_data_list):
        log.error(f"Assessment data is not in the expected list of dictionaries format. Type: {type(qs_data_list)}")
        return []
    if not isinstance(ms_data_list, list) or not all(isinstance(item, dict) for item in ms_data_list):
        log.error(f"Mark scheme data is not in the expected list of dictionaries format. Type: {type(ms_data_list)}")
        return []

    # Convert raw dicts to Pydantic models for validation and type safety
    try:
        questions = [OneQuestionModelV3(**q) for q in qs_data_list]
        schemes   = [IngestedMarkSchemeModel(**s) for s in ms_data_list]
    except Exception as e:
        log.error(f"Pydantic validation error during data loading for matching: {e}")
        log.error(f"Problematic assessment data (first item if list): {qs_data_list[0] if qs_data_list else 'N/A'}")
        log.error(f"Problematic mark scheme data (first item if list): {ms_data_list[0] if ms_data_list else 'N/A'}")
        return [] # Return empty on validation error

    match_results = match(questions, schemes, threshold=threshold, top_k=top_k, verbose=verbose)

    # The Flask app (caller) will be responsible for saving these results.
    return match_results


# Remove or comment out the if __name__ == "__main__": block
# This is for when the script is run directly, not when imported by Flask.
# if __name__ == "__main__":
#     # Example for standalone testing (paths need to be valid)
#     # logging.getLogger().setLevel(logging.DEBUG) # More verbose for testing
#     # test_assessment_path = Path("path/to/your/test_assessment.json")
#     # test_ms_path = Path("path/to/your/test_mark_scheme.json")
#     # if test_assessment_path.exists() and test_ms_path.exists():
#     #     results = main(test_assessment_path, test_ms_path, verbose=True)
#     #     log.info("\n=== Final Matches (Standalone Test) ===")
#     #     log.info(json.dumps(results, indent=2))
#     # else:
#     #     log.error("Test files not found for standalone run.")
#     pass
