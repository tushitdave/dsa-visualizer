
import json
from app.utils.llm_provider import llm
from app.utils.heuristics import consult_heuristics_db
from app.utils.logger import get_logger, log_error_with_context

logger = get_logger("strategist")


async def run_strategist_with_provider(llm_provider, normalized_data: dict) -> dict:
    """
    Select the best algorithm using provided LLM provider.

    Args:
        llm_provider: LLM provider instance (from Pipeline)
        normalized_data: Output from normalizer agent

    Returns:
        Strategy blueprint with selected algorithm
    """
    logger.info("Analyzing problem and selecting strategy...")

    system_constraints = normalized_data.get("system_constraints", [])
    logger.debug(f"System constraints: {system_constraints}")

    # Check if learning mode provided a recommendation
    recommended_hint = normalized_data.get("recommended_algorithm_hint")
    if recommended_hint:
        logger.info(f"Learning mode FORCED algorithm: {recommended_hint}")
        logger.info("Skipping LLM selection - using learning mode recommendation directly")

        return {
            "analysis_summary": f"Using algorithm recommended by learning journey: {recommended_hint}",
            "options": [
                {
                    "name": recommended_hint,
                    "time_complexity": "As per algorithm",
                    "space_complexity": "As per algorithm",
                    "production_suitability": "Selected via educational learning path",
                    "trade_offs": ["Chosen through guided learning for understanding"]
                }
            ],
            "selected_strategy_for_instrumentation": recommended_hint
        }

    # Get engineering rules from our RAG-lite DB
    heuristics_advice = consult_heuristics_db(system_constraints)

    if heuristics_advice:
        logger.info("Retrieved engineering heuristics from database")
        logger.debug(f"Heuristics: {heuristics_advice}")
    else:
        logger.info("No specific engineering constraints found")

    system_instruction = "You are a Principal Software Architect specializing in Data Structures and Algorithms."
    prompt = f"""
    PROBLEM ANALYSIS:
    {json.dumps(normalized_data, indent=2)}

    ENGINEERING HEURISTICS:
    {heuristics_advice}

    Evaluate potential algorithms. Select the single best approach considering both Big-O and the Engineering Rules.

    Return a JSON matching this structure:
    {{
        "analysis_summary": "Brief summary of context",
        "options": [
            {{
                "name": "Algo Name",
                "time_complexity": "O(...)",
                "space_complexity": "O(...)",
                "production_suitability": "Why good/bad for system constraints",
                "trade_offs": ["Tradeoff 1", "Tradeoff 2"]
            }}
        ],
        "selected_strategy_for_instrumentation": "The specific algorithm name to implement"
    }}
    """

    try:
        logger.debug("Calling LLM for strategy selection...")
        response_text = await llm_provider.call(prompt, system_instruction=system_instruction, json_mode=True)

        blueprint = json.loads(response_text)

        selected = blueprint.get('selected_strategy_for_instrumentation', 'Unknown')
        logger.info(f"Selected: {selected}")

        options_count = len(blueprint.get('options', []))
        logger.debug(f"Evaluated {options_count} algorithm options")

        return blueprint

    except Exception as e:
        log_error_with_context(logger, e, {"normalized_data": normalized_data})
        raise


async def run_strategist(normalized_data: dict) -> dict:
    """
    Select the best algorithm based on problem analysis and engineering heuristics

    Args:
        normalized_data: Output from normalizer agent

    Returns:
        Strategy blueprint with selected algorithm
    """
    logger.info("Analyzing problem and selecting strategy...")

    system_constraints = normalized_data.get("system_constraints", [])
    logger.debug(f"System constraints: {system_constraints}")

    # Check if learning mode provided a recommendation
    recommended_hint = normalized_data.get("recommended_algorithm_hint")
    if recommended_hint:
        logger.info(f"🎓 Learning mode FORCED algorithm: {recommended_hint}")
        logger.info("Skipping LLM selection - using learning mode recommendation directly")

        # Return directly with the recommended algorithm - no LLM call needed
        return {
            "analysis_summary": f"Using algorithm recommended by learning journey: {recommended_hint}",
            "options": [
                {
                    "name": recommended_hint,
                    "time_complexity": "As per algorithm",
                    "space_complexity": "As per algorithm",
                    "production_suitability": "Selected via educational learning path",
                    "trade_offs": ["Chosen through guided learning for understanding"]
                }
            ],
            "selected_strategy_for_instrumentation": recommended_hint
        }

    # Get engineering rules from our RAG-lite DB
    heuristics_advice = consult_heuristics_db(system_constraints)

    if heuristics_advice:
        logger.info("📚 Retrieved engineering heuristics from database")
        logger.debug(f"Heuristics: {heuristics_advice}")
    else:
        logger.info("No specific engineering constraints found")

    # Build hint section for prompt
    hint_section = ""
    if recommended_hint:
        hint_section = f"""
    IMPORTANT - LEARNING MODE RECOMMENDATION:
    The educational analysis recommended using: "{recommended_hint}"
    You MUST use this algorithm unless it's technically impossible for this problem.
    This is a strong directive from the learning journey.
    """

    system_instruction = "You are a Principal Software Architect specializing in Data Structures and Algorithms."
    prompt = f"""
    PROBLEM ANALYSIS:
    {json.dumps(normalized_data, indent=2)}

    ENGINEERING HEURISTICS:
    {heuristics_advice}

    {hint_section}

    Evaluate potential algorithms. Select the single best approach considering both Big-O and the Engineering Rules.

    Return a JSON matching this structure:
    {{
        "analysis_summary": "Brief summary of context",
        "options": [
            {{
                "name": "Algo Name",
                "time_complexity": "O(...)",
                "space_complexity": "O(...)",
                "production_suitability": "Why good/bad for system constraints",
                "trade_offs": ["Tradeoff 1", "Tradeoff 2"]
            }}
        ],
        "selected_strategy_for_instrumentation": "The specific algorithm name to implement"
    }}
    """

    try:
        logger.debug("Calling LLM (Pro tier) for strategy selection...")
        response_text = await llm.call(prompt, system_instruction=system_instruction, json_mode=True, model_tier="pro")

        blueprint = json.loads(response_text)

        selected = blueprint.get('selected_strategy_for_instrumentation', 'Unknown')
        logger.info(f"🎯 Selected: {selected}")

        options_count = len(blueprint.get('options', []))
        logger.debug(f"Evaluated {options_count} algorithm options")

        return blueprint

    except Exception as e:
        log_error_with_context(logger, e, {"normalized_data": normalized_data})
        raise
