
import json
import random
from app.utils.llm_provider import llm
from app.utils.logger import get_logger, log_error_with_context

logger = get_logger("narrator")

# VERSION MARKER - This prints when module is loaded
print("=" * 60)
print("NARRATOR MODULE LOADED - VERSION 2026-02-04-v6 (Input Data Fix)")
print("=" * 60)


def _validate_quiz_answer(quiz: dict, frame_data: dict, commentary: str) -> dict:
    """
    Validate and correct quiz answers by checking against frame data.
    This ensures the correct answer actually matches the visible data.
    """
    import re

    print("=" * 60)
    print("QUIZ VALIDATION FUNCTION CALLED")
    print("=" * 60)

    if not quiz or 'options' not in quiz or 'correct' not in quiz:
        print("QUIZ VALIDATION: Quiz invalid, skipping")
        return quiz

    question = quiz.get('question', '').lower()
    options = quiz['options']
    current_correct = quiz['correct']

    print(f"QUIZ VALIDATION: Question: {question}")
    print(f"QUIZ VALIDATION: Options: {options}")
    print(f"QUIZ VALIDATION: Current correct index: {current_correct} = '{options[current_correct] if current_correct < len(options) else 'OUT OF BOUNDS'}'")
    print(f"QUIZ VALIDATION: Frame data: {frame_data}")
    print(f"QUIZ VALIDATION: Commentary: {commentary[:100]}...")

    logger.info(f"QUIZ VALIDATION: Question: {question[:60]}...")
    logger.info(f"QUIZ VALIDATION: Frame data keys: {list(frame_data.keys())}")

    # Build a map of key names to their values
    key_value_map = {}

    def extract_key_values(data, prefix=''):
        if isinstance(data, dict):
            for k, v in data.items():
                full_key = f"{prefix}_{k}" if prefix else k
                if isinstance(v, (int, float)):
                    key_value_map[k.lower()] = str(int(v) if isinstance(v, float) and v.is_integer() else v)
                    key_value_map[full_key.lower()] = str(int(v) if isinstance(v, float) and v.is_integer() else v)
                elif isinstance(v, list) and len(v) == 1 and isinstance(v[0], (int, float)):
                    # Single-element list like [5]
                    val = v[0]
                    key_value_map[k.lower()] = str(int(val) if isinstance(val, float) and val.is_integer() else val)
                    key_value_map[full_key.lower()] = str(int(val) if isinstance(val, float) and val.is_integer() else val)
                elif isinstance(v, list) and len(v) == 1 and isinstance(v[0], str) and v[0].isdigit():
                    key_value_map[k.lower()] = v[0]
                    key_value_map[full_key.lower()] = v[0]
                elif isinstance(v, dict):
                    extract_key_values(v, k)

    extract_key_values(frame_data)
    logger.info(f"QUIZ VALIDATION: Key-value map: {key_value_map}")

    # Extract all numeric values from frame data
    frame_values = set(key_value_map.values())

    # Also extract numbers from commentary (especially after = sign)
    commentary_results = re.findall(r'=\s*(\d+)', commentary)
    for num in commentary_results:
        frame_values.add(num)
    logger.info(f"QUIZ VALIDATION: All frame values: {frame_values}")

    # Try to match question keywords to frame data keys
    # e.g., "total candies" should match "TOTAL_CANDIES"
    question_words = re.findall(r'\b\w+\b', question.lower())

    # Check for direct key matches
    expected_value = None
    for key, value in key_value_map.items():
        key_words = key.replace('_', ' ').lower().split()
        # Check if key words appear in question
        if all(word in question_words for word in key_words):
            expected_value = value
            logger.info(f"QUIZ VALIDATION: Key '{key}' matches question, expected value: {value}")
            break

    # If we found an expected value, verify the answer
    if expected_value:
        print(f"QUIZ VALIDATION: Expected value from data: {expected_value}")
        # Find which option matches the expected value
        for idx, opt in enumerate(options):
            opt_str = str(opt).strip()
            print(f"QUIZ VALIDATION: Checking option {idx}: '{opt_str}' == '{expected_value}' ? {opt_str == expected_value}")
            if opt_str == expected_value:
                if idx != current_correct:
                    print(f"!!! QUIZ VALIDATION: CORRECTING answer from index {current_correct} ('{options[current_correct]}') to index {idx} ('{opt_str}')")
                    logger.warning(f"QUIZ VALIDATION: CORRECTING answer from '{options[current_correct]}' to '{opt_str}' (matches key value)")
                    quiz['correct'] = idx
                else:
                    print(f"QUIZ VALIDATION: Answer '{opt_str}' is already correct at index {idx}")
                    logger.info(f"QUIZ VALIDATION: Answer '{opt_str}' is already correct")
                print(f"QUIZ VALIDATION RESULT: correct = {quiz['correct']}")
                return quiz
        print(f"QUIZ VALIDATION: Expected value '{expected_value}' not found in options!")

    # Fallback: Check if question asks for a numeric value
    value_keywords = ['total', 'count', 'number', 'sum', 'result', 'answer', 'value',
                      'length', 'size', 'max', 'min', 'how many', 'what is', 'final']

    asks_for_value = any(kw in question for kw in value_keywords)

    if asks_for_value and frame_values:
        # Find which options match frame values
        matching_options = []
        for idx, opt in enumerate(options):
            opt_str = str(opt).strip()
            if opt_str in frame_values:
                matching_options.append((idx, opt_str))

        logger.info(f"QUIZ VALIDATION: Options matching frame values: {matching_options}")

        # If exactly one option matches a frame value, that's likely correct
        if len(matching_options) == 1:
            correct_idx, correct_val = matching_options[0]
            if correct_idx != current_correct:
                logger.warning(f"QUIZ VALIDATION: CORRECTING answer from '{options[current_correct]}' to '{correct_val}' (only match)")
                quiz['correct'] = correct_idx
        elif len(matching_options) > 1:
            # Multiple matches - prefer the one in commentary results
            for idx, val in matching_options:
                if val in commentary_results:
                    if idx != current_correct:
                        print(f"!!! QUIZ VALIDATION: CORRECTING answer to '{val}' (found in commentary)")
                        logger.warning(f"QUIZ VALIDATION: CORRECTING answer to '{val}' (found in commentary)")
                        quiz['correct'] = idx
                    break

    print(f"QUIZ VALIDATION FINAL: correct index = {quiz['correct']}, answer = '{quiz['options'][quiz['correct']]}'")
    print("=" * 60)
    return quiz


def _shuffle_quiz_options(quiz: dict) -> dict:
    """
    Shuffle quiz options randomly while keeping track of the correct answer.
    This prevents learners from always guessing option 1.

    Special options like "None of the above" are always kept at the end.
    """
    if not quiz or 'options' not in quiz or 'correct' not in quiz:
        return quiz

    options = list(quiz['options'])  # Make a copy
    correct_idx = quiz['correct']

    print(f"[SHUFFLE] Input options: {options}")
    print(f"[SHUFFLE] Input correct index: {correct_idx}")

    # Validate correct index
    if correct_idx < 0 or correct_idx >= len(options):
        correct_idx = 0

    # Options that should always appear at the end (position 4)
    end_option_patterns = [
        "none of the above",
        "all of the above",
        "cannot be determined",
        "not enough information",
        "skip this step",
        "this step is not needed",
        "continue without changes",
        "return an error",
        "restart the algorithm",
        "terminate early",
        "undo the previous",
        "alternative approach",
        "not applicable",
        "n/a"
    ]

    # Separate regular options from "end" options
    regular_options = []
    end_option_items = []

    for i, opt in enumerate(options):
        opt_lower = str(opt).lower().strip()
        is_end_option = any(pattern in opt_lower for pattern in end_option_patterns)

        print(f"[SHUFFLE] Option {i}: '{opt}' -> is_end_option: {is_end_option}")

        if is_end_option:
            end_option_items.append((opt, i == correct_idx))
        else:
            regular_options.append((opt, i == correct_idx))

    print(f"[SHUFFLE] Regular options: {[o[0] for o in regular_options]}")
    print(f"[SHUFFLE] End options: {[o[0] for o in end_option_items]}")

    # Shuffle only the regular options
    random.shuffle(regular_options)

    # Combine: regular options first, then end options
    combined = regular_options + end_option_items

    # Extract shuffled options and find new correct index
    shuffled_options = [opt for opt, _ in combined]
    new_correct_idx = next((i for i, (_, is_correct) in enumerate(combined) if is_correct), 0)

    quiz['options'] = shuffled_options
    quiz['correct'] = new_correct_idx

    print(f"[SHUFFLE] Output options: {shuffled_options}")
    print(f"[SHUFFLE] Output correct index: {new_correct_idx}")

    logger.debug(f"Shuffled quiz: correct moved from index {correct_idx} to {new_correct_idx}")

    return quiz


async def run_narrator_with_provider(llm_provider, trace_data: list, algo_name: str, normalized_data: dict = None, blueprint: dict = None) -> dict:
    """
    Transform raw execution trace into educational narrative using provided LLM provider.

    Args:
        llm_provider: LLM provider instance (from Pipeline)
        trace_data: Raw trace from tracer agent
        algo_name: Algorithm name
        normalized_data: Original problem analysis
        blueprint: Algorithm selection rationale

    Returns:
        Complete trace data with frames, commentary, and quizzes
    """
    logger.info(f"Generating narrative for: {algo_name}")

    if not trace_data:
        logger.warning("No trace data provided")
        return {
            "title": f"{algo_name} (No Execution Trace)",
            "strategy": algo_name,
            "strategy_details": "No execution trace was captured to narrate.",
            "complexity": {
                "algorithm_name": algo_name,
                "time": {"best": "N/A", "average": "N/A", "worst": "N/A", "explanation": "No execution trace.", "comparison_data": []},
                "space": {"complexity": "N/A", "explanation": "No execution trace.", "variables": []}
            },
            "frames": []
        }

    logger.info(f"Processing {len(trace_data)} trace steps")

    # Limit trace data sent to LLM
    trace_preview = trace_data[:20]

    # Build context sections
    problem_context = ""
    if normalized_data:
        objective = normalized_data.get('objective', 'N/A')
        example_inputs = normalized_data.get('example_inputs', [])
        problem_context = f"""
    PROBLEM CONTEXT:
    Problem Objective: {objective}
    Example Inputs: {json.dumps(example_inputs, indent=2) if example_inputs else 'No specific examples'}
    """

    algorithm_context = ""
    if blueprint:
        analysis = blueprint.get('analysis_summary', '')
        algorithm_context = f"""
    ALGORITHM SELECTION CONTEXT:
    Why This Algorithm Was Chosen: {analysis}
    """

    system_instruction = """You are an expert Algorithms Professor creating educational algorithm visualizations.
    Your goal is to synthesize raw execution traces into clear, step-by-step visualizations."""

    prompt = f"""
    Algorithm: {algo_name}
    Raw Execution Trace: {json.dumps(trace_preview, indent=2)}

    {problem_context}
    {algorithm_context}

    REQUIREMENTS:
    1. Create 10-15 LOGICAL frames (consolidate micro-steps)
    2. Include INPUT data in EVERY frame
    3. Add a quiz to EVERY frame - each step should test understanding
    4. Use descriptive variable containers (INPUT_S, POINTERS, etc.)

    Return JSON with: title, strategy, strategy_details, complexity, frames
    Each frame: step_id, commentary, state (visual_type, data, highlights), quiz (optional)
    """

    try:
        logger.info("Calling LLM for narrative generation...")
        response_text = await llm_provider.call(prompt, system_instruction=system_instruction, json_mode=True)

        narrative = json.loads(response_text)
        logger.info(f"LLM returned narrative with {len(narrative.get('frames', []))} frames")

        # Log first frame structure for debugging
        if narrative.get('frames'):
            first_frame = narrative['frames'][0]
            first_state = first_frame.get('state', {})
            first_data = first_state.get('data', {})
            logger.info(f"BEFORE POST-PROCESS - First frame:")
            logger.info(f"  - state keys: {list(first_state.keys()) if isinstance(first_state, dict) else 'not a dict'}")
            logger.info(f"  - data keys: {list(first_data.keys()) if isinstance(first_data, dict) else 'not a dict'}")
            logger.info(f"  - data empty: {not first_data or len(first_data) == 0}")

        # Log trace_data info
        logger.info(f"trace_data has {len(trace_data) if trace_data else 0} entries")
        if trace_data and len(trace_data) > 0:
            first_trace_vars = trace_data[0].get('vars', {})
            logger.info(f"First trace vars keys: {list(first_trace_vars.keys()) if first_trace_vars else 'EMPTY'}")

        try:
            narrative = _post_process_narrative(narrative, trace_data, normalized_data)
        except Exception as post_err:
            logger.error(f"Post-processing EXCEPTION: {post_err}")
            import traceback
            logger.error(traceback.format_exc())
            # Continue with unprocessed narrative but try to fix empty data manually
            for frame in narrative.get('frames', []):
                if 'state' not in frame:
                    frame['state'] = {'visual_type': 'array', 'data': {}, 'highlights': []}
                if not frame['state'].get('data'):
                    frame['state']['data'] = {'STEP': [frame.get('step_id', 0) + 1], 'STATUS': ['Processing']}

        frames_count = len(narrative.get('frames', []))
        logger.info(f"Generated {frames_count} narrative frames")

        # Verify frames have data - AFTER post-processing
        logger.info("AFTER POST-PROCESS - Checking frames:")
        for idx, frame in enumerate(narrative.get('frames', [])[:3]):  # Log first 3 frames
            frame_data = frame.get('state', {}).get('data', {})
            logger.info(f"  Frame {idx}: data keys = {list(frame_data.keys()) if frame_data else 'EMPTY'}")

        empty_count = sum(1 for f in narrative.get('frames', []) if not f.get('state', {}).get('data'))
        if empty_count > 0:
            logger.error(f"CRITICAL: {empty_count} frames still have empty data after post-processing!")
        else:
            logger.info(f"SUCCESS: All frames have data")

        quizzes = [f for f in narrative.get('frames', []) if f.get('quiz')]
        logger.info(f"Created {len(quizzes)} quizzes")

        # GUARANTEED QUIZ FIX - Ensure every quiz has a valid 'correct' field and is shuffled
        print("=" * 60)
        print("GUARANTEED QUIZ FIX - Running before return")
        print("=" * 60)
        for idx, frame in enumerate(narrative.get('frames', [])):
            quiz = frame.get('quiz')
            if quiz:
                print(f"Frame {idx} quiz keys: {list(quiz.keys())}")
                if 'correct' not in quiz or quiz['correct'] is None:
                    print(f"  FIXING: 'correct' missing, setting to 0")
                    quiz['correct'] = 0
                else:
                    try:
                        quiz['correct'] = int(quiz['correct'])
                    except:
                        quiz['correct'] = 0

                # Shuffle options if not already shuffled (correct is still 0)
                # This ensures variety in correct answer positions
                if quiz['correct'] == 0 and len(quiz.get('options', [])) > 1:
                    _shuffle_quiz_options(quiz)

                print(f"  FINAL correct value: {quiz['correct']}")

        return narrative

    except Exception as e:
        logger.error("Narrative generation failed, creating fallback")
        log_error_with_context(logger, e, {"algo_name": algo_name, "trace_steps": len(trace_data)})

        # Return fallback with proper data extraction
        frames = []

        # Try to extract input data from first trace entry
        input_data = None
        if trace_data and len(trace_data) > 0:
            first_vars = trace_data[0].get('vars', {})
            for key, value in first_vars.items():
                if isinstance(value, (list, str)) and len(value) > 0:
                    input_data = list(value) if isinstance(value, str) else value
                    break

        for i, t in enumerate(trace_data[:10]):
            vars_data = t.get("vars", {})
            highlights = t.get("highlights", [])
            step_desc = t.get('step', f'Processing step {i + 1}')

            # Ensure we have meaningful data
            if not vars_data or len(vars_data) == 0:
                # Create fallback data with step info
                vars_data = {'STEP': [i + 1], 'STATUS': [step_desc]}
                # Add input data if available
                if input_data:
                    vars_data['INPUT_DATA'] = input_data

            # Validate highlights reference existing keys
            valid_highlights = []
            for h in highlights:
                base_key = h.split('[')[0] if '[' in h else h
                if base_key in vars_data:
                    valid_highlights.append(h)

            frames.append({
                "step_id": i,
                "commentary": f"Step {i + 1}: {step_desc}",
                "state": {"visual_type": "array", "data": vars_data, "highlights": valid_highlights},
                "quiz": None
            })

        logger.info(f"Generated fallback with {len(frames)} frames")

        return {
            "title": f"{algo_name} (Simplified View)",
            "strategy": algo_name,
            "strategy_details": "Fallback view due to processing error.",
            "complexity": {"algorithm_name": algo_name, "time": {"best": "O(?)", "average": "O(?)", "worst": "O(?)", "explanation": "N/A", "comparison_data": []}, "space": {"complexity": "O(?)", "explanation": "N/A", "variables": []}},
            "frames": frames
        }

def _post_process_narrative(narrative: dict, raw_trace: list, normalized_data: dict = None) -> dict:
    """
    Post-process narrator output to ensure data quality and consistency
    VERSION: 2026-02-04-v2

    Args:
        narrative: LLM-generated narrative
        raw_trace: Original trace data for reference

    Returns:
        Enhanced narrative with validated data structures
    """
    # VERSION MARKER - This confirms the updated code is running
    logger.info("=" * 50)
    logger.info("POST-PROCESS v2026-02-04-v6 (Input Data Fix) STARTING")
    logger.info("=" * 50)

    frames = narrative.get('frames', [])

    # Ensure raw_trace is a list (handle None case)
    if raw_trace is None:
        raw_trace = []
        logger.warning("raw_trace is None, using empty list")

    logger.info(f"Post-processing {len(frames)} frames with {len(raw_trace)} raw trace entries")

    # Log first raw trace entry for debugging
    if raw_trace and len(raw_trace) > 0:
        first_trace = raw_trace[0]
        logger.info(f"First raw trace entry keys: {list(first_trace.keys())}")
        first_vars = first_trace.get('vars', {})
        logger.info(f"First raw trace vars: {list(first_vars.keys()) if first_vars else 'EMPTY'}")

    # Validate and fix quiz data
    for frame_idx, frame in enumerate(frames):
        quiz = frame.get('quiz')
        if quiz:
            logger.info(f"Frame {frame_idx} has quiz: {quiz.get('question', 'NO QUESTION')[:50]}...")
            logger.info(f"  ALL QUIZ KEYS: {list(quiz.keys())}")
            logger.info(f"  Raw correct value: {quiz.get('correct')} (type: {type(quiz.get('correct')).__name__})")
            logger.info(f"  Options count: {len(quiz.get('options', []))}")
            # Log any field that might contain the correct answer
            for key in quiz.keys():
                if key not in ['question', 'options']:
                    logger.info(f"  Field '{key}': {quiz[key]}")

            # Ensure 'correct' exists and is an integer
            original_correct = quiz.get('correct')

            # Check if 'correct' is missing or None
            if 'correct' not in quiz or quiz.get('correct') is None:
                logger.warning(f"  Quiz missing 'correct' field! Defaulting to 0")
                quiz['correct'] = 0
            else:
                try:
                    quiz['correct'] = int(quiz['correct'])
                except (ValueError, TypeError):
                    logger.warning(f"  Could not convert correct '{original_correct}' to int, defaulting to 0")
                    quiz['correct'] = 0  # Default to first option if invalid

            # Also check for 'answer' field (some LLMs use this instead)
            if quiz.get('correct') == 0 and 'answer' in quiz:
                try:
                    quiz['correct'] = int(quiz['answer'])
                    logger.info(f"  Used 'answer' field instead: {quiz['correct']}")
                except (ValueError, TypeError):
                    pass

            # Check for 'correctIndex' or 'correct_index' field
            if quiz.get('correct') == 0:
                for alt_key in ['correctIndex', 'correct_index', 'correctAnswer', 'correct_answer']:
                    if alt_key in quiz:
                        try:
                            quiz['correct'] = int(quiz[alt_key])
                            logger.info(f"  Used '{alt_key}' field instead: {quiz['correct']}")
                            break
                        except (ValueError, TypeError):
                            pass

            # Ensure we have exactly 4 options
            options = quiz.get('options', [])
            if len(options) < 4:
                # Pad with realistic fallback options
                fallback_options = [
                    "None of the above",
                    "Skip this step",
                    "This step is not needed",
                    "Cannot be determined",
                    "All of the above",
                    "Restart the algorithm",
                    "Return an error",
                    "Continue without changes"
                ]
                fallback_idx = 0
                while len(options) < 4:
                    # Add fallback options that aren't already in the list
                    while fallback_idx < len(fallback_options) and fallback_options[fallback_idx] in options:
                        fallback_idx += 1
                    if fallback_idx < len(fallback_options):
                        options.append(fallback_options[fallback_idx])
                        fallback_idx += 1
                    else:
                        options.append(f"Alternative approach {len(options)}")
                quiz['options'] = options
            elif len(options) > 4:
                # Truncate to 4 options
                quiz['options'] = options[:4]
                # Ensure correct index is still valid
                if quiz['correct'] >= 4:
                    quiz['correct'] = 0

            # Validate correct index is within bounds
            if quiz['correct'] < 0 or quiz['correct'] >= len(quiz['options']):
                logger.warning(f"  Correct index {quiz['correct']} out of bounds, resetting to 0")
                quiz['correct'] = 0

            # VALIDATE quiz answer against frame data
            frame_data = frame.get('state', {}).get('data', {})
            commentary = frame.get('commentary', '')
            _validate_quiz_answer(quiz, frame_data, commentary)

            # Shuffle options to randomize correct answer position
            _shuffle_quiz_options(quiz)

            # Final quiz state logging
            logger.info(f"  FINAL quiz correct: {quiz['correct']} (options: {len(quiz['options'])})")
            logger.info(f"  Correct answer: {quiz['options'][quiz['correct']][:50]}...")

    # Extract input data from multiple sources
    input_data = None
    input_data_dict = {}  # Store multiple input variables

    # Source 1: Try to get from normalized_data (original problem inputs)
    logger.info("=" * 40)
    logger.info("EXTRACTING INPUT DATA FROM normalized_data")
    if normalized_data is None:
        logger.warning("normalized_data is None!")
        normalized_data = {}
    else:
        logger.info(f"normalized_data keys: {list(normalized_data.keys())}")

    if normalized_data:
        example_inputs = normalized_data.get('example_inputs', [])
        logger.info(f"example_inputs count: {len(example_inputs) if example_inputs else 0}")
        if example_inputs and len(example_inputs) > 0:
            logger.info(f"First example_inputs entry: {example_inputs[0]}")
            input_vars = example_inputs[0].get('input_vars', {})
            logger.info(f"input_vars: {input_vars}")
            for key, value in input_vars.items():
                if value is not None:
                    input_data_dict[key.upper()] = value
                    logger.info(f"  Added to input_data_dict: {key.upper()} = {str(value)[:100]}")
                    if input_data is None and isinstance(value, (list, str)) and len(value) > 0:
                        input_data = list(value) if isinstance(value, str) else value
                        logger.info(f"  Set input_data from '{key}': type={type(value).__name__}, len={len(value)}")

    # Source 2: Try to get from raw trace first entry
    if raw_trace and len(raw_trace) > 0:
        first_vars = raw_trace[0].get('vars', {})
        for key, value in first_vars.items():
            if isinstance(value, (list, str)) and len(value) > 0:
                key_upper = key.upper()
                if key_upper not in input_data_dict:
                    input_data_dict[key_upper] = value
                if input_data is None:
                    input_data = list(value) if isinstance(value, str) else value
                    logger.info(f"Extracted input '{key}' from raw trace: {type(value)}")

    logger.info("=" * 40)
    logger.info("INPUT DATA EXTRACTION SUMMARY")
    if input_data:
        logger.info(f"  Primary input_data: type={type(input_data).__name__}, len={len(input_data) if input_data else 0}")
        if isinstance(input_data, (list, str)) and len(input_data) <= 50:
            logger.info(f"  Primary input_data value: {input_data}")
    else:
        logger.warning("  No primary input_data extracted!")

    logger.info(f"  Input data dict ({len(input_data_dict)} keys): {list(input_data_dict.keys())}")
    for k, v in input_data_dict.items():
        v_str = str(v)[:50] + "..." if len(str(v)) > 50 else str(v)
        logger.info(f"    {k}: {v_str}")
    logger.info("=" * 40)

    for frame_idx, frame in enumerate(frames):
        # Ensure state exists
        if 'state' not in frame or frame['state'] is None:
            frame['state'] = {'visual_type': 'array', 'data': {}, 'highlights': []}

        state = frame['state']

        # Handle data_entries format (convert to data dict)
        if 'data_entries' in state and state['data_entries']:
            try:
                data_entries = state['data_entries']
                converted_data = {}
                for entry in data_entries:
                    if isinstance(entry, dict) and 'name' in entry and 'values' in entry:
                        converted_data[entry['name']] = entry['values']
                if converted_data:
                    state['data'] = converted_data
                    del state['data_entries']
                    logger.debug(f"Frame {frame_idx}: Converted data_entries to data dict")
            except Exception as e:
                logger.warning(f"Frame {frame_idx}: Failed to convert data_entries: {e}")

        # Get data (or empty dict if missing)
        data = state.get('data', {})

        # Ensure data is a dict
        if not isinstance(data, dict):
            logger.warning(f"Frame {frame_idx}: data is not a dict ({type(data)}), resetting to empty")
            data = {}

        # Ensure input data is present in every frame
        # Add all extracted input variables to the frame
        added_inputs = []
        for input_key, input_value in input_data_dict.items():
            # Only add if not already present (case-insensitive check)
            if not any(input_key.lower() == k.lower() for k in data.keys()):
                data[input_key] = input_value
                added_inputs.append(input_key)
        if added_inputs and frame_idx == 0:  # Log only for first frame to avoid spam
            logger.info(f"Frame 0: Added input keys from normalized_data: {added_inputs}")

        # Fallback: if still no input-related data, add generic input
        if input_data and not any('INPUT' in key.upper() or 'S' == key.upper() or 'STR' in key.upper() for key in data.keys()):
            if isinstance(input_data, list) and all(isinstance(x, str) and len(x) == 1 for x in input_data):
                data['INPUT_STRING'] = input_data
            elif isinstance(input_data, str):
                data['INPUT_STRING'] = list(input_data)
            else:
                data['INPUT_DATA'] = input_data

        # Ensure data has at least some content
        if not data or len(data) == 0:
            logger.warning(f"Frame {frame_idx}: Empty data detected, attempting fallback")

            # Fallback to raw trace data for this frame
            if len(raw_trace) > 0:
                # Try to find a trace entry with data
                trace_idx = min(frame_idx, len(raw_trace) - 1)
                raw_vars = raw_trace[trace_idx].get('vars', {})

                if raw_vars and len(raw_vars) > 0:
                    data = dict(raw_vars)  # Make a copy
                    logger.info(f"Frame {frame_idx}: Used raw trace vars from step {trace_idx}")
                else:
                    # Try to find ANY trace entry with data
                    for i, t in enumerate(raw_trace[:10]):  # Check first 10 entries
                        t_vars = t.get('vars', {})
                        if t_vars and len(t_vars) > 0:
                            data = dict(t_vars)
                            logger.info(f"Frame {frame_idx}: Used raw trace vars from step {i}")
                            break

            # If still no data, create minimal fallback
            if not data or len(data) == 0:
                step_desc = frame.get('commentary', f'Processing step {frame_idx + 1}')
                if len(step_desc) > 50:
                    step_desc = step_desc[:50] + '...'
                data = {'STEP': [frame_idx + 1], 'STATUS': [step_desc]}
                # Add input data if we have it
                if input_data:
                    data['INPUT_DATA'] = input_data
                logger.warning(f"Frame {frame_idx}: Created minimal fallback data")

        # Validate highlights reference existing keys
        highlights = state.get('highlights', [])
        if not isinstance(highlights, list):
            highlights = []

        valid_highlights = []
        for h in highlights:
            if not isinstance(h, str):
                continue
            # Check if highlight refers to a valid key or index
            base_key = h.split('[')[0] if '[' in h else h
            if base_key in data:
                valid_highlights.append(h)

        # If no valid highlights but we have data, highlight the first key
        if not valid_highlights and data:
            first_key = list(data.keys())[0]
            valid_highlights = [first_key]

        state['highlights'] = valid_highlights
        state['data'] = data
        frame['state'] = state

        # Log the final state of this frame
        logger.debug(f"Frame {frame_idx}: Final data keys: {list(data.keys())}, highlights: {valid_highlights}")

    narrative['frames'] = frames

    # GUARANTEED FINAL FIX - Force data into any frame that still has empty data
    for idx, frame in enumerate(frames):
        frame_data = frame.get('state', {}).get('data', {})
        if not frame_data or len(frame_data) == 0:
            logger.error(f"GUARANTEED FIX: Frame {idx} still has empty data, forcing fallback")
            # Force create state if missing
            if 'state' not in frame:
                frame['state'] = {'visual_type': 'array', 'highlights': []}
            # Force create data
            frame['state']['data'] = {
                'STEP': [idx + 1],
                'INFO': [f'Frame {idx + 1}'],
                'STATUS': ['Visualization data unavailable']
            }
            # Add input_data if we extracted it
            if input_data:
                frame['state']['data']['INPUT_DATA'] = input_data
            logger.info(f"GUARANTEED FIX: Frame {idx} now has data: {list(frame['state']['data'].keys())}")

    # GUARANTEED QUIZ FIX - Ensure every frame has a quiz
    for idx, frame in enumerate(frames):
        if not frame.get('quiz'):
            # Generate a default quiz based on the frame's commentary
            commentary = frame.get('commentary', f'Step {idx + 1}')
            # Extract a short description from commentary
            short_desc = commentary.replace('##', '').replace('#', '').strip()
            if len(short_desc) > 60:
                short_desc = short_desc[:60] + '...'

            # Create contextual quiz options based on frame position
            if idx == 0:
                frame['quiz'] = {
                    'question': 'What is the first step in this algorithm?',
                    'options': [
                        f'Initialize variables and set up data structures',
                        'Start processing from the end',
                        'Skip initialization and process directly',
                        'Return immediately without processing'
                    ],
                    'correct': 0
                }
            elif idx == len(frames) - 1:
                frame['quiz'] = {
                    'question': 'What happens in this final step?',
                    'options': [
                        'Return the computed result',
                        'Continue iterating indefinitely',
                        'Discard all computed values',
                        'Restart the algorithm from beginning'
                    ],
                    'correct': 0
                }
            else:
                frame['quiz'] = {
                    'question': f'What is the purpose of this step?',
                    'options': [
                        short_desc if short_desc else 'Process the current element',
                        'Skip this element and move to next',
                        'Undo the previous operation',
                        'Terminate early with partial result'
                    ],
                    'correct': 0
                }
            # Shuffle the fallback quiz options
            _shuffle_quiz_options(frame['quiz'])
            logger.info(f"Generated fallback quiz for frame {idx}")

    # Final validation
    empty_frames = [i for i, f in enumerate(frames) if not f.get('state', {}).get('data')]
    if empty_frames:
        logger.error(f"CRITICAL: Still have empty frames after guaranteed fix: {empty_frames}")
    else:
        logger.info(f"Post-processing complete: All {len(frames)} frames have valid data")

    frames_with_quiz = sum(1 for f in frames if f.get('quiz'))
    logger.info(f"Quiz coverage: {frames_with_quiz}/{len(frames)} frames have quizzes")

    logger.info("=" * 50)
    logger.info("POST-PROCESS v2026-02-04 COMPLETE")
    logger.info("=" * 50)

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
       - EVERY frame MUST have a quiz - no exceptions
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
    - Add a quiz to EVERY frame - each step must have a quiz
    - IMPORTANT: Each quiz should appear BEFORE the step that reveals the answer
      (e.g., Step 3 asks "What happens next?", Step 4 shows the answer)

    QUIZ REQUIREMENT: EVERY SINGLE FRAME MUST HAVE A QUIZ. No frame should have "quiz": null.
    Learners should actively predict what happens next at each major algorithm step.

    Output valid JSON only.
    """

    try:
        logger.debug("Calling LLM (Pro tier) for narrative generation...")
        response_text = await llm.call(prompt, system_instruction=system_instruction, json_mode=True, model_tier="pro")

        narrative = json.loads(response_text)
        logger.debug(f"LLM returned narrative with {len(narrative.get('frames', []))} frames")

        # Log first frame structure for debugging
        if narrative.get('frames'):
            first_frame = narrative['frames'][0]
            first_data = first_frame.get('state', {}).get('data', {})
            logger.debug(f"First frame data keys before post-process: {list(first_data.keys()) if isinstance(first_data, dict) else 'not a dict'}")

        try:
            # Post-process frames to ensure quality
            narrative = _post_process_narrative(narrative, trace_data, normalized_data)
        except Exception as post_err:
            logger.error(f"Post-processing failed: {post_err}")
            # Continue with unprocessed narrative but try to fix empty data manually
            for frame in narrative.get('frames', []):
                if 'state' not in frame:
                    frame['state'] = {'visual_type': 'array', 'data': {}, 'highlights': []}
                if not frame['state'].get('data'):
                    frame['state']['data'] = {'STEP': [frame.get('step_id', 0) + 1], 'STATUS': ['Processing']}

        frames_count = len(narrative.get('frames', []))
        logger.info(f"✓ Generated {frames_count} narrative frames")

        # Verify frames have data
        empty_count = sum(1 for f in narrative.get('frames', []) if not f.get('state', {}).get('data'))
        if empty_count > 0:
            logger.warning(f"Warning: {empty_count} frames still have empty data after post-processing")

        quizzes = [f for f in narrative.get('frames', []) if f.get('quiz')]
        logger.info(f"📝 Created {len(quizzes)} quizzes")

        return narrative

    except Exception as e:
        logger.error("❌ Narrative generation failed, creating simplified fallback")
        log_error_with_context(logger, e, {"algo_name": algo_name, "trace_steps": len(trace_data) if trace_data else 0})

        # Return a skeleton based on the trace data with proper data extraction
        frames = []

        # Try to extract input data from first trace entry
        input_data = None
        if trace_data and len(trace_data) > 0:
            first_vars = trace_data[0].get('vars', {})
            for key, value in first_vars.items():
                if isinstance(value, (list, str)) and len(value) > 0:
                    input_data = list(value) if isinstance(value, str) else value
                    break

        for i, t in enumerate(trace_data[:10]):
            vars_data = t.get("vars", {})
            highlights = t.get("highlights", [])
            step_desc = t.get('step', f'Processing step {i + 1}')

            # Ensure we have meaningful data
            if not vars_data or len(vars_data) == 0:
                # Create fallback data with step info
                vars_data = {'STEP': [i + 1], 'STATUS': [step_desc]}
                # Add input data if available
                if input_data:
                    vars_data['INPUT_DATA'] = input_data

            # Validate highlights reference existing keys
            valid_highlights = []
            for h in highlights:
                base_key = h.split('[')[0] if '[' in h else h
                if base_key in vars_data:
                    valid_highlights.append(h)

            frames.append({
                "step_id": i,
                "commentary": f"Step {i + 1}: {step_desc}",
                "state": {
                    "visual_type": "array",
                    "data": vars_data,
                    "highlights": valid_highlights
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
