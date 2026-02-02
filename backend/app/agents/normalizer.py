
import re
import json
from typing import List, Optional
from app.utils.llm_provider import llm
from app.utils.logger import get_logger, log_error_with_context

logger = get_logger("normalizer")

def privacy_shield(text: str) -> tuple[str, bool]:
    """
    Remove PII from user input using regex patterns

    Args:
        text: User input text

    Returns:
        Tuple of (sanitized_text, was_changed)
    """
    sanitized_text = text
    was_changed = False

    patterns = {
        r"sk-[a-zA-Z0-9]{32,}": "<API_KEY_REDACTED>",
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}": "<EMAIL_REDACTED>",
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b": "<IP_REDACTED>"
    }

    for pattern, replacement in patterns.items():
        if re.search(pattern, sanitized_text):
            sanitized_text = re.sub(pattern, replacement, sanitized_text)
            was_changed = True
            logger.warning(f"🔒 PII detected and redacted: {pattern}")

    return sanitized_text, was_changed

async def run_normalizer(text: str, toggles: List[str]) -> dict:
    """
    Normalize and classify user input

    Args:
        text: User problem description
        toggles: Context toggles (e.g., ['embedded', 'low_latency'])

    Returns:
        Normalized problem data dictionary
    """
    logger.info(f"Normalizing input (length: {len(text)} chars)")
    logger.debug(f"Context toggles: {toggles}")

    # Privacy shield
    safe_text, sanitized = privacy_shield(text)

    if sanitized:
        logger.warning("⚠️  PII was detected and removed from input")

    system_instruction = "You are the Gatekeeper for AlgoInsight. Your goal is to parse user intent and constraints into a structured format."
    prompt = f"""
    Analyze this problem statement and context toggles: {toggles}

    Problem: {safe_text}

    Classify the intent into LEARN, DEBUG, or PRODUCTION.
    Separate math constraints (size, range) from system constraints (latency, memory).
    CRITICALLY IMPORTANT: Extract ALL example inputs from the problem statement.

    Return a JSON matching this structure:
    {{
        "objective": "...",
        "input_structure": "...",
        "output_structure": "...",
        "math_constraints": [],
        "system_constraints": [],
        "intent": "...",
        "main_dsa_topic": "...",
        "was_sanitized": {str(sanitized).lower()},
        "example_inputs": [
            {{
                "input_vars": {{"s": "42"}},
                "expected_output": 42,
                "description": "Example 1: Basic string to integer conversion"
            }}
        ]
    }}

    EXAMPLE INPUT EXTRACTION RULES:
    - Look for "Example 1:", "Example 2:", "Input:", etc.
    - Extract the EXACT input values (e.g., if it says s = "42", extract "42")
    - Extract the expected output
    - If problem has multiple examples, extract ALL of them
    - If no examples found, set example_inputs to empty array []

    Examples of proper extraction:
    - "Input: s = '42'" → {{"input_vars": {{"s": "42"}}, "expected_output": 42}}
    - "Input: nums = [2,7,11,15], target = 9" → {{"input_vars": {{"nums": [2,7,11,15], "target": 9}}, "expected_output": [0,1]}}
    - "Input: head = [1,2,3,4,5], k = 2" → {{"input_vars": {{"head": [1,2,3,4,5], "k": 2}}}}
    """

    try:
        logger.debug("Calling LLM for normalization...")
        response_text = await llm.call(prompt, system_instruction=system_instruction, json_mode=True, model_tier="flash")

        data = json.loads(response_text)
        data["was_sanitized"] = sanitized

        logger.info(f"Intent classified: {data.get('intent', 'Unknown')}")
        logger.info(f"DSA Topic: {data.get('main_dsa_topic', 'Unknown')}")
        logger.debug(f"System constraints: {data.get('system_constraints', [])}")

        return data

    except Exception as e:
        log_error_with_context(logger, e, {"text_length": len(text), "toggles": toggles})
        raise
