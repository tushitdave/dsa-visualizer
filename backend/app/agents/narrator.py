
import json
from app.utils.llm_provider import llm
from app.utils.logger import get_logger, log_error_with_context

logger = get_logger("narrator")

def _post_process_narrative(narrative: dict, raw_trace: list) -> dict:
    """
    Post-process narrator output to ensure data quality and consistency

    Args:
        narrative: LLM-generated narrative
        raw_trace: Original trace data for reference

    Returns:
        Enhanced narrative with validated data structures
    """
    frames = narrative.get('frames', [])

    # Extract input data from first trace entry if available
    input_data = None
    if raw_trace and len(raw_trace) > 0:
        first_vars = raw_trace[0].get('vars', {})
        # Try to find array/list-like data
        for key, value in first_vars.items():
            if isinstance(value, (list, str)) and len(value) > 0:
                input_data = list(value) if isinstance(value, str) else value
                break

    for frame_idx, frame in enumerate(frames):
        state = frame.get('state', {})
        data = state.get('data', {})

        # Ensure input data is present in every frame if we found it
        if input_data and not any('INPUT' in key.upper() for key in data.keys()):
            # Add input data with a generic name if missing
            if isinstance(input_data, list) and all(isinstance(x, str) and len(x) == 1 for x in input_data):
                data['INPUT_S'] = input_data
            else:
                data['INPUT_DATA'] = input_data

        # Ensure data has at least some content
        if not data or len(data) == 0:
            # Fallback to raw trace data for this frame
            if frame_idx < len(raw_trace):
                data = raw_trace[frame_idx].get('vars', {})

        # Validate highlights reference existing keys
        highlights = state.get('highlights', [])
        valid_highlights = []
        for h in highlights:
            # Check if highlight refers to a valid key or index
            base_key = h.split('[')[0] if '[' in h else h
            if base_key in data:
                valid_highlights.append(h)

        state['highlights'] = valid_highlights
        state['data'] = data
        frame['state'] = state

    narrative['frames'] = frames
    return narrative

async def run_narrator(trace_data: list, algo_name: str, normalized_data: dict = None, blueprint: dict = None) -> dict:
    """
    Transform raw execution trace into educational narrative

    Args:
        trace_data: Raw trace from tracer agent
        algo_name: Algorithm name
        normalized_data: Original problem analysis (includes example_inputs, objectives, constraints)
        blueprint: Algorithm selection rationale (includes options and trade-offs)

    Returns:
        Complete trace data with frames, commentary, and quizzes
    """
    logger.info(f"Generating narrative for: {algo_name}")

    # Log context availability
    if normalized_data:
        logger.info("✓ Has normalized_data context (problem objectives, example inputs)")
        if normalized_data.get('example_inputs'):
            logger.info(f"  - Example inputs: {normalized_data['example_inputs'][0].get('input_vars', {})}")
    else:
        logger.warning("⚠️  No normalized_data context available")

    if blueprint:
        logger.info("✓ Has blueprint context (algorithm selection rationale)")
    else:
        logger.warning("⚠️  No blueprint context available")

    if not trace_data:
        logger.warning("⚠️  No trace data provided")
        return {
            "title": f"{algo_name} (No Execution Trace)",
            "strategy": algo_name,
            "strategy_details": "No execution trace was captured to narrate.",
            "complexity": {
                "algorithm_name": algo_name,
                "time": {
                    "best": "N/A",
                    "average": "N/A",
                    "worst": "N/A",
                    "explanation": "No execution trace was captured.",
                    "comparison_data": []
                },
                "space": {
                    "complexity": "N/A",
                    "explanation": "No execution trace was captured.",
                    "variables": []
                }
            },
            "frames": []
        }

    logger.info(f"Processing {len(trace_data)} trace steps")

    # Limit trace data sent to LLM to avoid token limits
    trace_preview = trace_data[:20]
    logger.debug(f"Sending first {len(trace_preview)} steps to LLM")

    # Build context sections for richer commentary
    problem_context = ""
    if normalized_data:
        objective = normalized_data.get('objective', 'N/A')
        example_inputs = normalized_data.get('example_inputs', [])

        problem_context = f"""
    ═══════════════════════════════════════════════════════════════
    📋 PROBLEM CONTEXT (Use this to enrich your commentary!)
    ═══════════════════════════════════════════════════════════════

    Problem Objective: {objective}

    Example Inputs from Problem Statement:
    {json.dumps(example_inputs, indent=2) if example_inputs else 'No specific examples provided'}

    In your commentary, reference these example inputs!
    Example: "We're processing the input '42' from Example 1..."

    ═══════════════════════════════════════════════════════════════
    """

    algorithm_context = ""
    if blueprint:
        analysis = blueprint.get('analysis_summary', '')
        algorithm_context = f"""
    ═══════════════════════════════════════════════════════════════
    🎯 ALGORITHM SELECTION CONTEXT
    ═══════════════════════════════════════════════════════════════

    Why This Algorithm Was Chosen:
    {analysis}

    Use this in strategy_details to explain the algorithm selection!

    ═══════════════════════════════════════════════════════════════
    """

    system_instruction = """You are an expert Algorithms Professor creating educational algorithm visualizations.
    Your goal is to synthesize raw execution traces into clear, hierarchical, step-by-step visualizations
    that help students understand algorithm logic through rich visual representations."""

    prompt = f"""
    Algorithm: {algo_name}
    Raw Execution Trace: {json.dumps(trace_preview, indent=2)}

    {problem_context}

    {algorithm_context}

    CRITICAL REQUIREMENTS:

    1. **DATA SYNTHESIS** - Transform raw variables into LOGICAL CONTAINERS:
       ❌ BAD: {{"start": 0, "end": 0, "i": 1}}  (flat, meaningless)
       ✅ GOOD: {{
         "INPUT_S": ["b","a","b","a","d"],
         "POINTERS": {{"start": 0, "end": 0}},
         "CURRENT_INDEX": 1
       }}

       - ALWAYS include the input array/data structure in EVERY frame
       - Group related variables into descriptive containers
       - Use UPPERCASE names for primary containers (INPUT_S, POINTERS, BEST_RANGE, etc.)

    2. **STEP CONSOLIDATION** - Create 10-15 LOGICAL steps (not 20+ micro-steps):
       - Merge consecutive variable updates into single meaningful step
       - Each step should represent a significant algorithm operation
       - Don't create separate steps for every variable change

       Example consolidation:
       Raw trace steps: [{{"i": 0}}, {{"s[i]": "b"}}, {{"start": 0}}, {{"end": 0}}]
       → Consolidated frame: "Initialize: Set pointers and begin iteration at index 0"

    3. **VISUAL TYPE MAPPING**:
       - Use "array" for: strings, lists, arrays, single container displays
       - Use "heap" for: binary heaps, priority queues
       - Use "map" for: hash maps, dictionaries with many key-value pairs

    4. **NESTED DATA STRUCTURES** - Create hierarchy for better visualization:
       {{
         "INPUT_S": ["b", "a", "b", "a", "d"],        // Top-level array
         "ALGORITHM_STATE": {{                          // Nested container
           "left": 0,
           "right": 4,
           "center": 2
         }},
         "RESULT": {{
           "best_length": 3,
           "best_start": 1
         }}
       }}

    5. **QUIZ GENERATION** - Create interactive quizzes at EVERY CRITICAL STEP:
       - Place a quiz before EVERY major algorithm decision or state change
       - Aim for a quiz every 2-3 steps (5-7 quizzes total for a 15-step trace)
       - Question format: "What should happen next?" or "Why does this work?"
       - 3-4 options with ONE correct answer
       - Make learners PREDICT the next action before revealing it
       - Questions should test UNDERSTANDING, not memorization

       QUIZ PLACEMENT EXAMPLES:
       - Before expanding/moving pointers: "What should we do next?"
       - Before swapping elements: "Should we swap these values?"
       - Before updating result: "Is this a better solution?"
       - At state transitions: "What state should we move to?"

    EXAMPLE OUTPUT FORMAT (String Algorithm):
    {{
      "title": "{algo_name} Visualization",
      "strategy": "{algo_name}",
      "strategy_details": "Detailed explanation of algorithm approach, complexity analysis, and why this strategy works.",
      "complexity": {{
        "algorithm_name": "{algo_name}",
        "time": {{
          "best": "O(1)",
          "average": "O(n)",
          "worst": "O(n)",
          "explanation": "Detailed explanation of why this algorithm has this time complexity. Reference the specific operations being performed.",
          "comparison_data": [
            {{"n": 100, "optimized": 10, "naive": 100}},
            {{"n": 1000, "optimized": 20, "naive": 1000}},
            {{"n": 10000, "optimized": 30, "naive": 10000}},
            {{"n": 100000, "optimized": 40, "naive": 100000}},
            {{"n": 1000000, "optimized": 50, "naive": 1000000}}
          ]
        }},
        "space": {{
          "complexity": "O(1)",
          "explanation": "Description of memory usage and auxiliary space needed.",
          "variables": ["var1", "var2", "var3"]
        }},
        "best_case_desc": "When this algorithm performs optimally",
        "average_case_desc": "Typical performance for random inputs",
        "worst_case_desc": "When this algorithm performs worst",
        "math_insight": "Mathematical formula or derivation (optional)",
        "key_takeaway": "A memorable summary of why this algorithm is efficient (optional)"
      }},
      "frames": [
        {{
          "step_id": 0,
          "commentary": "## Step 1: Initialize Variables\\n\\nWe begin by setting up our input string and tracking pointers...",
          "state": {{
            "visual_type": "array",
            "data": {{
              "INPUT_S": ["b", "a", "b", "a", "d"],
              "POINTERS": {{
                "start": 0,
                "end": 0
              }},
              "BEST_RANGE": {{
                "length": 1,
                "start_idx": 0
              }}
            }},
            "highlights": ["INPUT_S", "POINTERS"]
          }},
          "quiz": null
        }},
        {{
          "step_id": 1,
          "commentary": "## Step 2: Expand Around Center\\n\\nWe check if characters match...",
          "state": {{
            "visual_type": "array",
            "data": {{
              "INPUT_S": ["b", "a", "b", "a", "d"],
              "CHECKING": {{
                "left": 0,
                "right": 2,
                "current_center": 1
              }},
              "BEST_RANGE": {{
                "length": 3,
                "start_idx": 0
              }}
            }},
            "highlights": ["INPUT_S[0]", "INPUT_S[2]", "CHECKING"]
          }},
          "quiz": {{
            "question": "Why do we expand around each center instead of checking all substrings?",
            "options": [
              "It reduces time complexity from O(n³) to O(n²)",
              "It uses less memory",
              "It's easier to implement",
              "It handles edge cases better"
            ],
            "correct": 0
          }}
        }},
        {{
          "step_id": 2,
          "commentary": "## Step 3: Check Next Character\\n\\nNow we need to decide what to do with the next character...",
          "state": {{
            "visual_type": "array",
            "data": {{
              "INPUT_S": ["b", "a", "b", "a", "d"],
              "CURRENT_POS": 3,
              "TEMP_RESULT": "aba"
            }},
            "highlights": ["INPUT_S[3]", "CURRENT_POS"]
          }},
          "quiz": {{
            "question": "The next character is 'a'. What should we do?",
            "options": [
              "Include it in the current palindrome",
              "Start a new palindrome from here",
              "Compare it with the center character",
              "Skip it and move to next position"
            ],
            "correct": 2
          }}
        }}
      ]
    }}

    ADDITIONAL QUIZ EXAMPLES FOR DIFFERENT ALGORITHM TYPES:

    For State Machine algorithms:
    {{
      "quiz": {{
        "question": "Current state is START and we see digit '5'. What state should we transition to?",
        "options": [
          "DIGIT state - digits can start a number",
          "SIGN state - we need a sign first",
          "DECIMAL state - jump to decimal",
          "REJECT - invalid input"
        ],
        "correct": 0
      }}
    }}

    For Hash Map algorithms:
    {{
      "quiz": {{
        "question": "We found value 3 at index 2. What should we store in the hash map?",
        "options": [
          "Store {{'3': 2}} - map value to index",
          "Store {{2: '3'}} - map index to value",
          "Store nothing - wait for duplicates",
          "Store {{'3': [2]}} - map value to list of indices"
        ],
        "correct": 0
      }}
    }}

    For Two Pointer algorithms:
    {{
      "quiz": {{
        "question": "Left pointer at 0, right at 5. arr[0]=1, arr[5]=9. Sum=10, target=8. What next?",
        "options": [
          "Move left pointer right (sum too large)",
          "Move right pointer left (sum too large)",
          "Move both pointers (found answer)",
          "Return false (no solution)"
        ],
        "correct": 1
      }}
    }}

    NOW SYNTHESIZE THE PROVIDED TRACE INTO 10-15 HIGH-QUALITY VISUALIZATION FRAMES:
    - Transform raw variables into logical containers
    - ALWAYS include the input array
    - Consolidate micro-steps into meaningful operations
    - Create rich, nested data structures
    - Add 5-7 educational quizzes at critical decision points
    - IMPORTANT: Each quiz should appear BEFORE the step that reveals the answer
      (e.g., Step 3 asks "What happens next?", Step 4 shows the answer)

    QUIZ REQUIREMENT: You MUST include quizzes frequently throughout the trace.
    Learners should actively predict what happens next at each major algorithm step.

    Output valid JSON only.
    """

    try:
        logger.debug("Calling LLM (Pro tier) for narrative generation...")
        response_text = await llm.call(prompt, system_instruction=system_instruction, json_mode=True, model_tier="pro")

        narrative = json.loads(response_text)

        # Post-process frames to ensure quality
        narrative = _post_process_narrative(narrative, trace_data)

        frames_count = len(narrative.get('frames', []))
        logger.info(f"✓ Generated {frames_count} narrative frames")

        quizzes = [f for f in narrative.get('frames', []) if f.get('quiz')]
        logger.info(f"📝 Created {len(quizzes)} quizzes")

        return narrative

    except Exception as e:
        logger.error("❌ Narrative generation failed, creating simplified fallback")
        log_error_with_context(logger, e, {"algo_name": algo_name, "trace_steps": len(trace_data)})

        # Return a skeleton based on the trace data
        frames = []
        for i, t in enumerate(trace_data[:10]):
            frames.append({
                "step_id": i,
                "commentary": f"Step {i}: {t.get('step', 'Processing...')}",
                "state": {
                    "visual_type": "array",
                    "data": t.get("vars", {}),
                    "highlights": t.get("highlights", [])
                },
                "quiz": None
            })

        logger.info(f"Generated simplified fallback with {len(frames)} frames")

        return {
            "title": f"{algo_name} (Simplified View)",
            "strategy": algo_name,
            "strategy_details": "Synthesis engine encountered an error. Showing raw trace execution.",
            "complexity": {
                "algorithm_name": algo_name,
                "time": {
                    "best": "O(?)",
                    "average": "O(?)",
                    "worst": "O(?)",
                    "explanation": "Complexity analysis not available due to processing error.",
                    "comparison_data": []
                },
                "space": {
                    "complexity": "O(?)",
                    "explanation": "Space analysis not available.",
                    "variables": []
                }
            },
            "frames": frames
        }
