"""
Pipeline Orchestrator - Manages the 5-agent pipeline with request-scoped providers

This module ensures each request gets its own LLM provider instance,
enabling multi-user, multi-provider concurrent execution.

Now with Smart Routing for sub-second responses on cached/known algorithms!
"""

import time
import json
from typing import Optional, Dict, Any, Tuple

from app.utils.request_context import RequestContext
from app.utils.providers.factory import LLMProviderFactory
from app.utils.logger import get_logger, log_error_with_context
from app.router.smart_router import SmartRouter, get_smart_router, RoutePath

logger = get_logger("pipeline")


class Pipeline:
    """
    Orchestrates the 5-agent pipeline with request-scoped LLM provider.

    Each Pipeline instance is created for a single request, ensuring:
    - Request isolation (no shared state)
    - Correct provider routing (user's selected provider)
    - Consistent logging with request_id
    """

    def __init__(self, context: RequestContext, smart_router: SmartRouter = None):
        """
        Initialize pipeline with request context.

        Args:
            context: RequestContext containing provider config
            smart_router: Optional SmartRouter instance (uses singleton if not provided)
        """
        self.context = context
        self.request_id = context.request_id

        # Create provider instance for this request
        self.llm_provider = LLMProviderFactory.create_from_context(context)

        # Smart router for instant/fast path detection
        self._router = smart_router or get_smart_router()

        logger.info(f"[{self.request_id}] Pipeline initialized: "
                   f"provider={context.provider}, model={context.model}")

    async def run_analysis(
        self,
        problem_text: str,
        context_toggles: list,
        recommended_algorithm: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the analysis with smart routing for sub-second responses.

        Routing priority:
        1. INSTANT: Cache hit or algorithm library match (<100ms)
        2. FAST: Pattern match with template customization (<500ms)
        3. FULL: Full 5-agent LLM pipeline (20-60s)

        Args:
            problem_text: User's problem description
            context_toggles: Context constraints (e.g., ['Low Memory'])
            recommended_algorithm: Optional algorithm hint from learning mode

        Returns:
            Complete trace data with frames
        """
        pipeline_start = time.time()

        # ============ SMART ROUTING PHASE ============
        logger.info(f"[{self.request_id}] Checking fast paths...")

        route_result = await self._router.route(problem_text, context_toggles)

        # INSTANT PATH: Return cached/pre-computed result immediately
        # Only used for HIGH confidence matches (>= 0.8) with exact algorithm identification
        if route_result.path == RoutePath.INSTANT and route_result.data:
            frames = route_result.data.get('frames', [])

            # Verify frames exist AND have valid data (not empty)
            has_valid_frames = False
            if frames and len(frames) > 0:
                # Check that at least the first frame has non-empty data
                first_frame_data = frames[0].get('state', {}).get('data', {})
                has_valid_frames = bool(first_frame_data) and len(first_frame_data) > 0

                if not has_valid_frames:
                    logger.warning(f"[{self.request_id}] INSTANT PATH: Cached frames have empty data, rejecting cache")

            if has_valid_frames:
                result = route_result.data

                # Import validation function
                from app.agents.narrator import _validate_quiz_answer, _shuffle_quiz_options

                # Fix and validate quizzes in cached results
                print(f"[CACHE] Validating quizzes in cached result...")
                for frame in result.get('frames', []):
                    quiz = frame.get('quiz')
                    if quiz:
                        # Ensure correct field exists
                        if 'correct' not in quiz or quiz['correct'] is None:
                            logger.warning(f"[{self.request_id}] Cached quiz missing 'correct', fixing")
                            quiz['correct'] = 0

                        # Validate quiz answer against frame data
                        frame_data = frame.get('state', {}).get('data', {})
                        commentary = frame.get('commentary', '')
                        _validate_quiz_answer(quiz, frame_data, commentary)

                result['_meta'] = {
                    'request_id': self.request_id,
                    'provider_used': 'cache',
                    'model_used': 'precomputed',
                    'route_path': 'instant',
                    'route_source': route_result.source,
                    'route_time_ms': route_result.timing_ms,
                    'total_time_ms': (time.time() - pipeline_start) * 1000,
                    'algorithm_matched': route_result.algorithm_id,
                    'confidence': route_result.confidence
                }
                logger.info(f"[{self.request_id}] INSTANT PATH: {route_result.source} "
                           f"(algo: {route_result.algorithm_id}, conf: {route_result.confidence:.0%}) "
                           f"in {route_result.timing_ms:.1f}ms")
                return result
            else:
                logger.warning(f"[{self.request_id}] INSTANT PATH had invalid data, falling back to FULL pipeline")

        # NOTE: FAST PATH removed - we no longer force algorithm recommendations from pattern matching
        # to avoid incorrect algorithm identification. Let the LLM decide the best algorithm.

        # ============ FULL LLM PIPELINE ============
        logger.info(f"[{self.request_id}] Starting 5-agent LLM pipeline")

        from app.agents.normalizer import run_normalizer_with_provider
        from app.agents.strategist import run_strategist_with_provider
        from app.agents.instrumenter import run_instrumenter_with_provider
        from app.agents.tracer import run_tracer
        from app.agents.narrator import run_narrator_with_provider

        try:
            # Agent 1: Normalizer
            logger.info(f"[{self.request_id}] [1/5] Starting NORMALIZER")
            start = time.time()
            normalized_data = await run_normalizer_with_provider(
                self.llm_provider,
                problem_text,
                context_toggles
            )
            logger.info(f"[{self.request_id}] [1/5] NORMALIZER completed in {time.time() - start:.2f}s")

            # Agent 2: Strategist
            logger.info(f"[{self.request_id}] [2/5] Starting STRATEGIST")
            start = time.time()

            if recommended_algorithm:
                logger.info(f"[{self.request_id}] Learning mode recommended: {recommended_algorithm}")
                normalized_data['recommended_algorithm_hint'] = recommended_algorithm

            blueprint = await run_strategist_with_provider(
                self.llm_provider,
                normalized_data
            )
            selected_strategy = blueprint.get('selected_strategy_for_instrumentation', 'Unknown')
            logger.info(f"[{self.request_id}] [2/5] STRATEGIST completed in {time.time() - start:.2f}s")
            logger.info(f"[{self.request_id}] Selected Strategy: {selected_strategy}")

            # Agent 3: Instrumenter
            logger.info(f"[{self.request_id}] [3/5] Starting INSTRUMENTER")
            start = time.time()
            spy_code_data = await run_instrumenter_with_provider(
                self.llm_provider,
                blueprint,
                normalized_data
            )
            logger.info(f"[{self.request_id}] [3/5] INSTRUMENTER completed in {time.time() - start:.2f}s")

            # Agent 4: Tracer (no LLM needed)
            logger.info(f"[{self.request_id}] [4/5] Starting TRACER")
            start = time.time()
            trace_results = run_tracer(spy_code_data['code'], spy_code_data['entry_point'])

            if trace_results.get('status') == 'error':
                logger.error(f"[{self.request_id}] [4/5] TRACER failed!")
                return None

            if not trace_results.get('trace_data'):
                logger.warning(f"[{self.request_id}] [4/5] TRACER returned empty trace")
                return None

            logger.info(f"[{self.request_id}] [4/5] TRACER completed in {time.time() - start:.2f}s")
            logger.info(f"[{self.request_id}] Captured {trace_results.get('step_count', 0)} steps")

            # Agent 5: Narrator
            logger.info(f"[{self.request_id}] [5/5] Starting NARRATOR")
            start = time.time()
            final_trace = await run_narrator_with_provider(
                self.llm_provider,
                trace_results['trace_data'],
                blueprint['selected_strategy_for_instrumentation'],
                normalized_data,
                blueprint
            )
            logger.info(f"[{self.request_id}] [5/5] NARRATOR completed in {time.time() - start:.2f}s")

            if not final_trace or not final_trace.get('frames'):
                logger.error(f"[{self.request_id}] NARRATOR produced no frames")
                return None

            total_time_ms = (time.time() - pipeline_start) * 1000

            # Add metadata to response
            final_trace['_meta'] = {
                'request_id': self.request_id,
                'provider_used': self.context.provider,
                'model_used': self.context.model,
                'route_path': 'full',
                'total_time_ms': total_time_ms
            }

            logger.info(f"[{self.request_id}] Pipeline SUCCESS - {len(final_trace.get('frames', []))} frames "
                       f"in {total_time_ms:.0f}ms")

            # ============ CACHE RESULT FOR FUTURE INSTANT ACCESS ============
            try:
                await self._router.store_result(
                    problem_text,
                    context_toggles,
                    final_trace,
                    algorithm_id=selected_strategy.lower().replace(' ', '_') if selected_strategy else None
                )
                logger.info(f"[{self.request_id}] Result cached for future instant access")
            except Exception as cache_err:
                logger.warning(f"[{self.request_id}] Failed to cache result: {cache_err}")

            return final_trace

        except Exception as e:
            logger.error(f"[{self.request_id}] Pipeline FAILED: {str(e)}")
            log_error_with_context(logger, e, {
                'request_id': self.request_id,
                'problem_preview': problem_text[:100]
            })
            raise

    async def run_learning(
        self,
        problem_text: str,
        context_toggles: list
    ) -> Dict[str, Any]:
        """
        Execute the educational flow generation.

        Args:
            problem_text: User's problem description
            context_toggles: Context constraints

        Returns:
            Educational flow with phases
        """
        from app.agents.educational_flow_generator import generate_educational_flow_with_provider

        logger.info(f"[{self.request_id}] Starting educational flow generation")

        try:
            start = time.time()
            educational_flow = await generate_educational_flow_with_provider(
                self.llm_provider,
                problem_text,
                context_toggles
            )
            duration = time.time() - start

            logger.info(f"[{self.request_id}] Educational flow completed in {duration:.2f}s")
            logger.info(f"[{self.request_id}] Generated {educational_flow.get('total_phases', 0)} phases")

            # Add metadata
            educational_flow['_meta'] = {
                'request_id': self.request_id,
                'provider_used': self.context.provider,
                'model_used': self.context.model
            }

            return educational_flow

        except Exception as e:
            logger.error(f"[{self.request_id}] Educational flow FAILED: {str(e)}")
            log_error_with_context(logger, e, {
                'request_id': self.request_id,
                'problem_preview': problem_text[:100]
            })
            raise

    async def get_algorithm_explanation(
        self,
        algorithm_name: str,
        problem_context: str = ""
    ) -> Dict[str, Any]:
        """
        Generate algorithm deep-dive explanation.

        Args:
            algorithm_name: Name of algorithm to explain
            problem_context: Optional problem context

        Returns:
            Algorithm explanation data
        """
        from app.agents.algorithm_explainer import get_algorithm_explanation_with_provider

        logger.info(f"[{self.request_id}] Generating explanation for: {algorithm_name}")

        try:
            start = time.time()
            explanation = await get_algorithm_explanation_with_provider(
                self.llm_provider,
                algorithm_name,
                problem_context
            )
            duration = time.time() - start

            logger.info(f"[{self.request_id}] Algorithm explanation completed in {duration:.2f}s")

            # Add metadata
            explanation['_meta'] = {
                'request_id': self.request_id,
                'provider_used': self.context.provider,
                'model_used': self.context.model
            }

            return explanation

        except Exception as e:
            logger.error(f"[{self.request_id}] Algorithm explanation FAILED: {str(e)}")
            raise
