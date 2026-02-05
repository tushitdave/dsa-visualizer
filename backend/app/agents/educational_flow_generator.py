"""
Educational Flow Generator Agent
Generates step-by-step learning journey for DSA problems
"""

import json
from typing import Dict, Any, List
from app.utils.llm_provider import LLMProvider
from app.utils.logger import get_logger

logger = get_logger("educational_flow")

llm = LLMProvider()


async def generate_educational_flow_with_provider(llm_provider, problem_text: str, context_toggles: List[str]) -> Dict[str, Any]:
    """
    Generate a complete 3-phase educational flow using provided LLM provider.

    Args:
        llm_provider: LLM provider instance (from Pipeline)
        problem_text: Raw problem statement from user
        context_toggles: System constraints

    Returns:
        Complete educational flow with all phases
    """
    logger.info("Starting Educational Flow Generation with custom provider...")

    phase1 = await _generate_phase_understand_with_provider(llm_provider, problem_text)
    phase2 = await _generate_phase_analyze_with_provider(llm_provider, problem_text, phase1)
    phase3 = await _generate_phase_explore_with_provider(llm_provider, phase1, phase2, context_toggles)

    return {
        "learning_mode": True,
        "total_phases": 3,
        "phases": [phase1, phase2, phase3],
        "current_phase": 0
    }


async def _generate_phase_understand_with_provider(llm_provider, problem_text: str) -> Dict[str, Any]:
    """Phase 1 with custom provider"""
    logger.info("  Phase 1: Understanding the problem...")

    system_instruction = """You are an expert DSA teacher helping a student understand a problem.
Your task: Identify objective, break down input/output, list constraints, provide key insights."""

    prompt = f"""Given this DSA problem:

{problem_text}

Generate a JSON response that helps a learner UNDERSTAND the problem:

{{
  "phase": "understand_problem",
  "phase_number": 1,
  "phase_title": "Understanding the Problem",
  "content": {{
    "problem_statement": "The original problem text",
    "breakdown": {{
      "objective": "Clear statement of what we're solving",
      "input": "Description of input data",
      "output": "Description of expected output",
      "constraints": ["List of constraints"]
    }},
    "key_insights": ["Insight 1", "Insight 2"]
  }}
}}"""

    try:
        response = await llm_provider.call(prompt, system_instruction, json_mode=True)
        return json.loads(response)
    except Exception as e:
        logger.error(f"Error in Phase 1: {e}")
        return {"phase": "understand_problem", "phase_number": 1, "phase_title": "Understanding the Problem",
                "content": {"problem_statement": problem_text, "breakdown": {"objective": "Solve the given problem", "input": "See problem", "output": "See problem", "constraints": []}, "key_insights": ["Analyzing..."]}}


async def _generate_phase_analyze_with_provider(llm_provider, problem_text: str, phase1: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 2 with custom provider"""
    logger.info("  Phase 2: Analyzing input structure...")

    system_instruction = """You are an expert DSA teacher analyzing input structure.
Identify data structure type, extract sample values, identify key properties."""

    prompt = f"""Given: {json.dumps(phase1, indent=2)}

Generate JSON for input analysis:
{{
  "phase": "analyze_input",
  "phase_number": 2,
  "phase_title": "Analyzing Input Structure",
  "content": {{
    "data_structure_type": "array|tree|graph|string|linked_list",
    "sample_input": {{"visual_type": "array", "values": [], "display_format": "horizontal"}},
    "properties": ["Property 1", "Property 2"],
    "why_properties_matter": ["Why 1 matters", "Why 2 matters"]
  }}
}}"""

    try:
        response = await llm_provider.call(prompt, system_instruction, json_mode=True)
        return json.loads(response)
    except Exception as e:
        logger.error(f"Error in Phase 2: {e}")
        return {"phase": "analyze_input", "phase_number": 2, "phase_title": "Analyzing Input Structure",
                "content": {"data_structure_type": "array", "sample_input": {"visual_type": "array", "values": [], "display_format": "horizontal"},
                           "properties": ["Analyzing..."], "why_properties_matter": ["Understanding input is crucial"]}}


async def _generate_phase_explore_with_provider(llm_provider, phase1: Dict[str, Any], phase2: Dict[str, Any], context_toggles: List[str]) -> Dict[str, Any]:
    """Phase 3 with custom provider"""
    logger.info("  Phase 3: Exploring possible approaches...")

    system_instruction = """You are an expert DSA teacher exploring algorithmic approaches.
Suggest 2-3 algorithms with pros/cons and recommend the best."""

    constraints_text = ", ".join(context_toggles) if context_toggles else "None"

    prompt = f"""Given:
- Problem: {json.dumps(phase1.get('content', {}).get('breakdown', {}), indent=2)}
- Input: {json.dumps(phase2.get('content', {}), indent=2)}
- Constraints: {constraints_text}

Generate JSON with approaches:
{{
  "phase": "explore_approaches",
  "phase_number": 3,
  "phase_title": "Exploring Possible Approaches",
  "content": {{
    "approaches": [
      {{"name": "Approach Name", "description": "...", "complexity": {{"time": "O(?)", "space": "O(?)"}}, "meets_constraints": true, "pros": [], "cons": [], "suitable_for": "..."}}
    ],
    "recommended": {{"approach_name": "Best Approach", "reason": "Why", "key_insight": "Key insight"}}
  }}
}}"""

    try:
        response = await llm_provider.call(prompt, system_instruction, json_mode=True)
        return json.loads(response)
    except Exception as e:
        logger.error(f"Error in Phase 3: {e}")
        return {"phase": "explore_approaches", "phase_number": 3, "phase_title": "Exploring Possible Approaches",
                "content": {"approaches": [{"name": "Standard Approach", "description": "Common solution", "complexity": {"time": "O(n)", "space": "O(n)"}, "meets_constraints": True, "pros": ["Efficient"], "cons": [], "suitable_for": "Most cases"}],
                           "recommended": {"approach_name": "Standard Approach", "reason": "Balanced complexity", "key_insight": "We'll explore together"}}}


async def generate_educational_flow(problem_text: str, context_toggles: List[str]) -> Dict[str, Any]:
    """
    Generate a complete 7-phase educational flow for a DSA problem

    Args:
        problem_text: Raw problem statement from user
        context_toggles: System constraints (embedded, high_throughput, etc.)

    Returns:
        Complete educational flow with all phases
    """

    print("🎓 Starting Educational Flow Generation...")

    # Generate all phases
    phase1 = await generate_phase_understand(problem_text)
    phase2 = await generate_phase_analyze(problem_text, phase1)
    phase3 = await generate_phase_explore(phase1, phase2, context_toggles)

    return {
        "learning_mode": True,
        "total_phases": 3,
        "phases": [phase1, phase2, phase3],
        "current_phase": 0
    }


async def generate_phase_understand(problem_text: str) -> Dict[str, Any]:
    """
    PHASE 1: Understand the Problem
    Help learner break down and understand what's being asked
    """

    print("  📋 Phase 1: Understanding the problem...")

    system_instruction = """
You are an expert DSA teacher helping a student understand a problem.

Your task:
1. Identify the objective (what are we trying to solve?)
2. Break down the input structure
3. Break down the output structure
4. List all constraints (time, space, system)
5. Provide 2-3 key insights that help understand the problem

Be clear, encouraging, and educational.
"""

    prompt = f"""
Given this DSA problem:

{problem_text}

Generate a JSON response that helps a learner UNDERSTAND the problem:

{{
  "phase": "understand_problem",
  "phase_number": 1,
  "phase_title": "Understanding the Problem",
  "content": {{
    "problem_statement": "The original problem text",
    "breakdown": {{
      "objective": "Clear statement of what we're solving",
      "input": "Description of input data",
      "output": "Description of expected output",
      "constraints": ["List of constraints"]
    }},
    "key_insights": [
      "Insight 1 about the problem",
      "Insight 2 about the problem"
    ]
  }}
}}

Remember: Be educational and clear. This is for a learner!
"""

    try:
        response = await llm.call(prompt, system_instruction, json_mode=True, model_tier="pro")
        result = json.loads(response)
        return result
    except Exception as e:
        print(f"  ❌ Error in Phase 1: {e}")
        # Return fallback
        return {
            "phase": "understand_problem",
            "phase_number": 1,
            "phase_title": "Understanding the Problem",
            "content": {
                "problem_statement": problem_text,
                "breakdown": {
                    "objective": "Solve the given problem",
                    "input": "See problem statement",
                    "output": "See problem statement",
                    "constraints": []
                },
                "key_insights": [
                    "Let's analyze this step by step",
                    "We'll explore different approaches"
                ]
            }
        }


async def generate_phase_analyze(problem_text: str, phase1: Dict[str, Any]) -> Dict[str, Any]:
    """
    PHASE 2: Analyze Input Structure
    Help learner understand the data structures involved
    """

    print("  🔍 Phase 2: Analyzing input structure...")

    system_instruction = """
You are an expert DSA teacher helping a student analyze the input structure.

Your task:
1. Identify the data structure type (array, linked list, tree, graph, string, etc.)
2. Extract actual values if provided in the problem
3. Identify key properties of the input
4. Explain why these properties matter

Be visual and concrete. Use examples.
"""

    prompt = f"""
Given this problem understanding:

{json.dumps(phase1, indent=2)}

Generate a JSON response that helps a learner ANALYZE the input:

{{
  "phase": "analyze_input",
  "phase_number": 2,
  "phase_title": "Analyzing Input Structure",
  "content": {{
    "data_structure_type": "array|tree|graph|string|linked_list|etc",
    "sample_input": {{
      "visual_type": "array|tree|etc",
      "values": [actual values if available],
      "display_format": "how to display it"
    }},
    "properties": [
      "Property 1: Length is 8",
      "Property 2: Values range from 1-8",
      "Property 3: Some duplicates exist"
    ],
    "why_properties_matter": [
      "Why property 1 is important",
      "Why property 2 is important"
    ]
  }}
}}

If the problem contains explicit input values like [1,2,3] or a tree diagram, extract them!
"""

    try:
        response = await llm.call(prompt, system_instruction, json_mode=True, model_tier="pro")
        result = json.loads(response)
        return result
    except Exception as e:
        print(f"  ❌ Error in Phase 2: {e}")
        return {
            "phase": "analyze_input",
            "phase_number": 2,
            "phase_title": "Analyzing Input Structure",
            "content": {
                "data_structure_type": "array",
                "sample_input": {
                    "visual_type": "array",
                    "values": [],
                    "display_format": "horizontal"
                },
                "properties": ["Analyzing input structure..."],
                "why_properties_matter": ["Understanding input is crucial for choosing the right algorithm"]
            }
        }


async def generate_phase_explore(phase1: Dict[str, Any], phase2: Dict[str, Any], context_toggles: List[str]) -> Dict[str, Any]:
    """
    PHASE 3: Explore Possible Approaches
    Show 2-3 different algorithms with pros/cons
    """

    print("  💭 Phase 3: Exploring possible approaches...")

    system_instruction = """
You are an expert DSA teacher helping a student explore different algorithmic approaches.

Your task:
1. Suggest 2-3 different algorithms to solve the problem
2. For each approach, provide:
   - Clear name
   - Time complexity
   - Space complexity
   - Whether it meets constraints
   - Pros and cons
3. Recommend the BEST approach and explain why

Consider the system constraints provided.
"""

    constraints_text = ", ".join(context_toggles) if context_toggles else "None"

    prompt = f"""
Given:
- Problem understanding: {json.dumps(phase1.get('content', {}).get('breakdown', {}), indent=2)}
- Input analysis: {json.dumps(phase2.get('content', {}), indent=2)}
- System constraints: {constraints_text}

Generate a JSON response with 2-3 algorithmic approaches:

{{
  "phase": "explore_approaches",
  "phase_number": 3,
  "phase_title": "Exploring Possible Approaches",
  "content": {{
    "approaches": [
      {{
        "name": "Brute Force",
        "description": "Simple but slow approach",
        "complexity": {{
          "time": "O(n²)",
          "space": "O(1)"
        }},
        "meets_constraints": false,
        "pros": ["Easy to understand", "No extra space"],
        "cons": ["Too slow for large inputs"],
        "suitable_for": "Small datasets or learning"
      }},
      {{
        "name": "Optimized Approach",
        "description": "Better algorithm using X technique",
        "complexity": {{
          "time": "O(n)",
          "space": "O(1)"
        }},
        "meets_constraints": true,
        "pros": ["Fast", "Space efficient"],
        "cons": ["Slightly complex"],
        "suitable_for": "Production use"
      }}
    ],
    "recommended": {{
      "approach_name": "Optimized Approach",
      "reason": "Meets all constraints and has optimal complexity",
      "key_insight": "The key insight that makes this work"
    }}
  }}
}}

Provide real, practical approaches. If constraints include "low_memory", recommend space-efficient algorithms.
"""

    try:
        response = await llm.call(prompt, system_instruction, json_mode=True, model_tier="pro")
        result = json.loads(response)
        return result
    except Exception as e:
        print(f"  ❌ Error in Phase 3: {e}")
        return {
            "phase": "explore_approaches",
            "phase_number": 3,
            "phase_title": "Exploring Possible Approaches",
            "content": {
                "approaches": [
                    {
                        "name": "Standard Approach",
                        "description": "Common solution to this problem",
                        "complexity": {"time": "O(n)", "space": "O(n)"},
                        "meets_constraints": True,
                        "pros": ["Efficient", "Well-known pattern"],
                        "cons": ["Requires understanding of data structures"],
                        "suitable_for": "Most cases"
                    }
                ],
                "recommended": {
                    "approach_name": "Standard Approach",
                    "reason": "Balanced time and space complexity",
                    "key_insight": "We'll explore this together"
                }
            }
        }


# Future phases (designed for interactive learning):

async def generate_phase_choose(phase3: Dict[str, Any]) -> Dict[str, Any]:
    """
    PHASE 4: Choose the Best Strategy (Interactive)
    Let the learner choose and get feedback
    """
    # This will be interactive in the UI
    # Just return the quiz structure
    return {
        "phase": "choose_strategy",
        "phase_number": 4,
        "phase_title": "Choose Your Strategy",
        "content": {
            "question": "Based on what we learned, which approach should we use?",
            "options": [
                approach["name"]
                for approach in phase3.get("content", {}).get("approaches", [])
            ],
            "correct_answer": phase3.get("content", {}).get("recommended", {}).get("approach_name", ""),
            "feedback": "Great thinking! Let's design the solution."
        }
    }


async def generate_phase_design(recommended_approach: str, problem_context: Dict) -> Dict[str, Any]:
    """
    PHASE 5: Design the Solution Architecture
    Show flowchart, variables, pseudocode
    """
    # To be implemented
    pass


async def generate_phase_build(design: Dict[str, Any]) -> Dict[str, Any]:
    """
    PHASE 6: Build the Code Step-by-Step
    Show code construction line by line
    """
    # To be implemented
    pass
