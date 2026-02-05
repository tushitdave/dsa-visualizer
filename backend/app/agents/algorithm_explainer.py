"""
Algorithm Explainer Agent

Generates comprehensive, educational algorithm explanations using LLM.
Produces structured JSON data for the Algorithm Deep Dive feature.
"""

import json
import os
import re
from typing import Optional
from app.utils.llm_provider import llm
from app.utils.logger import get_logger

logger = get_logger("algorithm_explainer")

# Cache directory for generated algorithms
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'public', 'algorithms')


def normalize_algorithm_id(name: str) -> str:
    """Convert algorithm name to snake_case file ID."""
    # Convert to lowercase
    normalized = name.lower()
    # Replace spaces and special chars with underscores
    normalized = re.sub(r'[^a-z0-9]+', '_', normalized)
    # Remove leading/trailing underscores
    normalized = normalized.strip('_')
    # Remove common suffixes
    for suffix in ['_approach', '_algorithm', '_technique', '_method', '_optimization']:
        if normalized.endswith(suffix) and len(normalized) > len(suffix):
            normalized = normalized[:-len(suffix)]
    return normalized


def load_cached_algorithm(algorithm_id: str) -> Optional[dict]:
    """Try to load algorithm from cache."""
    cache_path = os.path.join(CACHE_DIR, f"{algorithm_id}.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cached algorithm: {e}")
    return None


def save_to_cache(algorithm_id: str, data: dict) -> bool:
    """Save generated algorithm to cache."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_path = os.path.join(CACHE_DIR, f"{algorithm_id}.json")
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved algorithm to cache: {cache_path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to save to cache: {e}")
        return False


async def generate_algorithm_explanation(algorithm_name: str, problem_context: str = "") -> dict:
    """
    Generate comprehensive algorithm explanation using LLM.

    Args:
        algorithm_name: Name of the algorithm (e.g., "Binary Search", "Monotonic Stack")
        problem_context: Optional problem context to make examples more relevant

    Returns:
        Structured algorithm data matching our JSON schema
    """

    algorithm_id = normalize_algorithm_id(algorithm_name)

    # Check cache first
    cached = load_cached_algorithm(algorithm_id)
    if cached:
        logger.info(f"Using cached algorithm data for: {algorithm_name}")
        return cached

    logger.info(f"Generating algorithm explanation via LLM for: {algorithm_name}")

    # Build the comprehensive prompt
    prompt = f"""You are an expert computer science educator. Generate a comprehensive, educational explanation for the algorithm: "{algorithm_name}"

{"PROBLEM CONTEXT (use this to make examples relevant): " + problem_context if problem_context else ""}

Return a valid JSON object with this EXACT structure. Be thorough and educational like a textbook explanation.

{{
  "algorithm_id": "{algorithm_id}",
  "name": "{algorithm_name}",
  "display_name": "{algorithm_name}",
  "category": "Category name (e.g., 'Divide and Conquer', 'Dynamic Programming', 'Greedy', 'Graph Traversal', 'Monotonic Stack', etc.)",
  "tags": ["tag1", "tag2", "tag3", "tag4"],

  "overview": {{
    "core_idea": "A clear, concise explanation of what this algorithm does and WHY it works. 2-3 sentences.",
    "when_to_use": [
      "Specific condition 1 when this algorithm is ideal",
      "Specific condition 2",
      "Specific condition 3",
      "Specific condition 4"
    ],
    "real_world_analogy": "A relatable, memorable analogy that helps understand the algorithm. Like explaining to a smart 12-year-old."
  }},

  "visual_explanation": {{
    "steps": [
      {{
        "title": "Step 1 title",
        "description": "What happens in this step and why",
        "array": [2, 1, 5, 6, 2, 3],
        "highlight": "init"
      }},
      {{
        "title": "Step 2 title",
        "description": "Detailed explanation of the operation",
        "array": [2, 1, 5, 6, 2, 3],
        "highlight": "process"
      }}
    ]
  }},

  "pseudocode": {{
    "language": "generic",
    "code": "function algorithmName(input):\\n    // Line 1: Initialize\\n    variable = initial_value\\n    \\n    // Line 2: Main logic\\n    for each element in input:\\n        process(element)\\n    \\n    return result",
    "annotations": [
      {{"line": 1, "text": "Clear explanation of what this line does"}},
      {{"line": 2, "text": "Explanation of initialization"}},
      {{"line": 5, "text": "Explain the loop logic"}},
      {{"line": 6, "text": "Explain processing step"}},
      {{"line": 8, "text": "Explain return value"}}
    ],
    "variables": [
      {{"name": "variableName", "description": "What this variable stores"}},
      {{"name": "anotherVar", "description": "Purpose of this variable"}}
    ],
    "key_operations": [
      "First key operation description",
      "Second key operation description",
      "Third key operation description"
    ],
    "return_values": [
      {{"value": "result", "condition": "When successful"}},
      {{"value": "-1 or null", "condition": "When not found/failed"}}
    ],
    "flow_steps": [
      "Initialize",
      "Process",
      "Check Condition",
      "Update State",
      "Return Result"
    ]
  }},

  "complexity": {{
    "time": {{
      "best": "O(?)",
      "average": "O(?)",
      "worst": "O(?)",
      "explanation": "Detailed explanation of WHY this is the time complexity. Explain the reasoning.",
      "comparison_data": [
        {{"n": 10, "optimized": 10, "bruteforce": 100}},
        {{"n": 100, "optimized": 100, "bruteforce": 10000}},
        {{"n": 1000, "optimized": 1000, "bruteforce": 1000000}},
        {{"n": 10000, "optimized": 10000, "bruteforce": 100000000}}
      ]
    }},
    "space": {{
      "complexity": "O(?)",
      "explanation": "Explain what extra space is used and why."
    }}
  }},

  "variations": [
    {{
      "name": "Variation 1 Name",
      "description": "How this variation differs from the main algorithm",
      "use_case": "When to use this variation",
      "example": {{
        "input": "Example input",
        "output": "Expected output"
      }},
      "key_change": "What code/logic changes for this variation"
    }},
    {{
      "name": "Variation 2 Name",
      "description": "Description",
      "use_case": "Use case",
      "example": {{
        "input": "Input",
        "output": "Output"
      }},
      "key_change": "Key modification"
    }}
  ],

  "common_pitfalls": [
    {{
      "title": "Pitfall 1: Descriptive title",
      "problem": "What goes wrong and when",
      "bad_code": "// The incorrect way\\nincorrect_code_here",
      "good_code": "// The correct way\\ncorrect_code_here",
      "explanation": "Why the bad code fails and why the fix works"
    }},
    {{
      "title": "Pitfall 2: Another common mistake",
      "problem": "Description of the issue",
      "bad_code": "bad_example",
      "good_code": "good_example",
      "explanation": "Explanation"
    }},
    {{
      "title": "Pitfall 3: Edge case issue",
      "problem": "What edge case is missed",
      "bad_code": "code_missing_edge_case",
      "good_code": "code_handling_edge_case",
      "explanation": "Why edge cases matter"
    }}
  ],

  "practice_exercise": {{
    "title": "Hands-on Practice: [Descriptive Title]",
    "description": "Walk through the algorithm step by step on this example.",
    "array": [3, 1, 4, 1, 5, 9, 2, 6],
    "target": "relevant target or goal",
    "steps": [
      {{
        "question": "Question about the first step?",
        "hint": "A helpful hint without giving away the answer",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct": 0,
        "explanation": "Detailed explanation of why this is correct and what happens"
      }},
      {{
        "question": "Question about the next step?",
        "hint": "Another helpful hint",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct": 1,
        "explanation": "Explanation of this step"
      }},
      {{
        "question": "Question about an important decision point?",
        "hint": "Think about the algorithm's core logic",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct": 2,
        "explanation": "Explanation"
      }},
      {{
        "question": "Final question about the result?",
        "hint": "Review what we've done so far",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct": 0,
        "explanation": "Final explanation and summary"
      }}
    ]
  }},

  "pro_tips": [
    "Practical tip 1 that helps in coding interviews",
    "Tip 2 about common optimizations",
    "Tip 3 about recognizing when to use this algorithm",
    "Tip 4 about debugging or testing",
    "Tip 5 about related patterns"
  ],

  "related_problems": [
    "Problem Name 1 (LeetCode/Platform number if applicable)",
    "Problem Name 2",
    "Problem Name 3",
    "Problem Name 4",
    "Problem Name 5"
  ]
}}

IMPORTANT GUIDELINES:
1. Make the explanation EDUCATIONAL - assume the learner is seeing this algorithm for the first time
2. Use CONCRETE examples with actual numbers, not abstract descriptions
3. The visual_explanation steps should walk through a complete example with actual data
4. The practice_exercise should be INTERACTIVE - questions that test understanding
5. Pitfalls should show ACTUAL code examples (bad vs good)
6. The real_world_analogy should be memorable and accurate
7. Ensure the JSON is valid - escape quotes properly, use \\n for newlines in code strings
8. The comparison_data should show realistic operation counts (optimized vs brute force)

Return ONLY the JSON object, no markdown code blocks or extra text."""

    try:
        # Call LLM using the singleton
        system_instruction = "You are an expert computer science educator specializing in algorithms and data structures."
        response = await llm.call(prompt, system_instruction=system_instruction, json_mode=True)

        # Clean up response - remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Parse JSON
        algorithm_data = json.loads(cleaned)

        # Ensure algorithm_id is set correctly
        algorithm_data['algorithm_id'] = algorithm_id

        # Save to cache for future use
        save_to_cache(algorithm_id, algorithm_data)

        logger.info(f"Successfully generated algorithm explanation for: {algorithm_name}")
        return algorithm_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Response was: {response[:500]}...")
        raise ValueError(f"Failed to generate valid algorithm data: {e}")
    except Exception as e:
        logger.error(f"Error generating algorithm explanation: {e}")
        raise


async def get_algorithm_explanation_with_provider(llm_provider, algorithm_name: str, problem_context: str = "") -> dict:
    """
    Get algorithm explanation using provided LLM provider.

    Args:
        llm_provider: LLM provider instance (from Pipeline)
        algorithm_name: Name of the algorithm
        problem_context: Optional problem to make examples relevant

    Returns:
        Algorithm explanation data
    """
    algorithm_id = normalize_algorithm_id(algorithm_name)

    # Check cache first
    cached = load_cached_algorithm(algorithm_id)
    if cached:
        logger.info(f"Using cached algorithm data for: {algorithm_name}")
        return cached

    logger.info(f"Generating algorithm explanation via LLM for: {algorithm_name}")

    # Build prompt (simplified version)
    prompt = f"""Generate a comprehensive educational explanation for the algorithm: "{algorithm_name}"

{"PROBLEM CONTEXT: " + problem_context if problem_context else ""}

Return a valid JSON object with: algorithm_id, name, category, tags, overview (core_idea, when_to_use, real_world_analogy),
visual_explanation (steps with array examples), pseudocode (code, annotations, variables),
complexity (time with best/average/worst, space), variations, common_pitfalls, practice_exercise, pro_tips, related_problems.

Be educational and use concrete examples."""

    try:
        system_instruction = "You are an expert computer science educator specializing in algorithms."
        response = await llm_provider.call(prompt, system_instruction=system_instruction, json_mode=True)

        cleaned = response.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        algorithm_data = json.loads(cleaned)
        algorithm_data['algorithm_id'] = algorithm_id

        save_to_cache(algorithm_id, algorithm_data)
        logger.info(f"Generated algorithm explanation for: {algorithm_name}")
        return algorithm_data

    except Exception as e:
        logger.error(f"Error generating algorithm explanation: {e}")
        raise


async def get_algorithm_explanation(algorithm_name: str, problem_context: str = "") -> dict:
    """
    Main entry point - get algorithm explanation from cache or generate.

    Args:
        algorithm_name: Name of the algorithm
        problem_context: Optional problem to make examples relevant

    Returns:
        Algorithm explanation data
    """
    algorithm_id = normalize_algorithm_id(algorithm_name)

    # Try multiple possible cache file names
    possible_ids = [
        algorithm_id,
        algorithm_id.replace('_based', ''),
        algorithm_id + '_optimization',
        algorithm_id + '_technique',
    ]

    # Also try common mappings
    mappings = {
        'monotonic_stack': 'stack_based_optimization',
        'stack': 'stack_based_optimization',
        'two_pointers': 'two_pointer',
        'hashmap': 'hash_map',
        'hash_table': 'hash_map',
        'binary_search_tree': 'binary_search',
        'morris_traversal_for_constant_space': 'morris_traversal',
        'morris_traversal_space_optimized': 'morris_traversal',
        'optimized_in_order_traversal': 'morris_traversal',
        'constant_space_traversal': 'morris_traversal',
    }

    if algorithm_id in mappings:
        possible_ids.insert(0, mappings[algorithm_id])

    # Try to load from cache
    for pid in possible_ids:
        cached = load_cached_algorithm(pid)
        if cached:
            logger.info(f"Found cached algorithm data: {pid}")
            return cached

    # Generate new explanation
    return await generate_algorithm_explanation(algorithm_name, problem_context)
