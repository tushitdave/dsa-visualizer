"""
Base LLM Provider - Abstract base class for all LLM providers

All provider implementations must inherit from this class and
implement the abstract methods.
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Optional, List
from app.utils.logger import get_logger

logger = get_logger("llm_provider.base")


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM providers (Azure, OpenAI, Gemini) must implement this interface.
    This ensures consistent behavior across providers and enables the
    factory pattern for provider selection.
    """

    # Each provider defines its available models
    MODELS: List[str] = []

    def __init__(self, request_id: str, api_key: str, model: str, endpoint: Optional[str] = None):
        """
        Initialize the provider.

        Args:
            request_id: Unique request identifier for logging
            api_key: API key for authentication
            model: Model name to use
            endpoint: API endpoint (required for Azure, optional for others)
        """
        self.request_id = request_id
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint
        self._validate_model()

    def _validate_model(self):
        """Validate that the model is supported by this provider"""
        if self.MODELS and self.model not in self.MODELS:
            raise ValueError(
                f"Model '{self.model}' is not supported by {self.__class__.__name__}. "
                f"Available models: {self.MODELS}"
            )

    def _is_mock_mode(self) -> bool:
        """Check if we should use mock responses (no valid API key)"""
        if not self.api_key:
            return True
        if 'MOCK_MODE' in self.api_key:
            return True
        if 'YOUR_' in self.api_key or 'REPLACE' in self.api_key:
            return True
        if len(self.api_key) < 15:
            return True
        return False

    async def call(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = True
    ) -> str:
        """
        Make an LLM API call.

        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            json_mode: Whether to request JSON response format

        Returns:
            Response text from the LLM
        """
        # Check for mock mode
        if self._is_mock_mode():
            logger.warning(f"[{self.request_id}] Mock mode - no valid API key")
            return self._generate_mock_response(system_instruction)

        start_time = time.time()
        provider_name = self.__class__.__name__

        logger.info(f"[{self.request_id}] {provider_name} call: model={self.model}, "
                   f"prompt_length={len(prompt)}")

        try:
            response = await self._make_api_call(prompt, system_instruction, json_mode)

            elapsed = time.time() - start_time
            logger.info(f"[{self.request_id}] {provider_name} response: "
                       f"length={len(response)}, time={elapsed:.2f}s")

            return response

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[{self.request_id}] {provider_name} error after {elapsed:.2f}s: {str(e)}")
            raise

    @abstractmethod
    async def _make_api_call(
        self,
        prompt: str,
        system_instruction: Optional[str],
        json_mode: bool
    ) -> str:
        """
        Provider-specific API call implementation.

        Each provider implements this method with their SDK.

        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            json_mode: Whether to request JSON response format

        Returns:
            Response text from the LLM
        """
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate that the credentials are correct.

        Makes a minimal API call to verify the key works.

        Returns:
            True if credentials are valid, False otherwise
        """
        pass

    @classmethod
    def get_available_models(cls) -> List[str]:
        """
        Get list of available models for this provider.

        Returns:
            List of model names
        """
        return cls.MODELS.copy()

    def _generate_mock_response(self, system_instruction: Optional[str]) -> str:
        """
        Generate a context-aware mock response for testing without API keys.

        Args:
            system_instruction: System instruction to determine response type

        Returns:
            Mock JSON response
        """
        logger.info(f"[{self.request_id}] Generating mock response")

        instr = str(system_instruction).lower() if system_instruction else ""

        if "gatekeeper" in instr:
            logger.debug(f"[{self.request_id}] Mock: Normalizer response")
            return json.dumps({
                "objective": "Two-Heap Median Finder",
                "input_structure": "Stream of Integers",
                "output_structure": "Float",
                "math_constraints": ["N < 10^5"],
                "system_constraints": ["low_latency"],
                "intent": "LEARN",
                "main_dsa_topic": "Heaps",
                "was_sanitized": False,
                "example_inputs": [{"input_vars": {"nums": [5, 2, 8, 1]}, "expected_output": 3.5}]
            })

        if "architect" in instr:
            logger.debug(f"[{self.request_id}] Mock: Strategist response")
            return json.dumps({
                "analysis_summary": "Using Min-Max heaps for streaming median.",
                "options": [
                    {"name": "Two Heaps", "complexity": {"time": "O(log n)", "space": "O(n)"}, "selected": True},
                    {"name": "Sorting", "complexity": {"time": "O(n log n)", "space": "O(n)"}, "selected": False}
                ],
                "selected_strategy_for_instrumentation": "Two Heaps"
            })

        if "lead python developer" in instr or "instrumentation" in instr:
            logger.debug(f"[{self.request_id}] Mock: Instrumenter response")
            return json.dumps({
                "code": """import heapq

class Solution:
    def __init__(self):
        self.trace = []
        self.max_heap = []  # stores smaller half (negated for max behavior)
        self.min_heap = []  # stores larger half

    def log(self, step_name, variables, highlights):
        self.trace.append({
            'step': step_name,
            'vars': variables,
            'highlights': highlights
        })

    def run_demo(self):
        nums = [5, 2, 8, 1, 9]
        self.log('Initialize', {'nums': nums, 'max_heap': [], 'min_heap': []}, ['nums'])

        for num in nums:
            heapq.heappush(self.max_heap, -num)
            self.log('Push to max_heap', {'max_heap': [-x for x in self.max_heap], 'min_heap': self.min_heap}, ['max_heap'])

            if self.max_heap and self.min_heap and -self.max_heap[0] > self.min_heap[0]:
                val = -heapq.heappop(self.max_heap)
                heapq.heappush(self.min_heap, val)
                self.log('Rebalance', {'max_heap': [-x for x in self.max_heap], 'min_heap': self.min_heap}, ['min_heap'])

            if len(self.max_heap) > len(self.min_heap) + 1:
                val = -heapq.heappop(self.max_heap)
                heapq.heappush(self.min_heap, val)
                self.log('Balance sizes', {'max_heap': [-x for x in self.max_heap], 'min_heap': self.min_heap}, ['min_heap'])
            elif len(self.min_heap) > len(self.max_heap):
                val = heapq.heappop(self.min_heap)
                heapq.heappush(self.max_heap, -val)
                self.log('Balance sizes', {'max_heap': [-x for x in self.max_heap], 'min_heap': self.min_heap}, ['max_heap'])

        if len(self.max_heap) > len(self.min_heap):
            median = -self.max_heap[0]
        else:
            median = (-self.max_heap[0] + self.min_heap[0]) / 2

        self.log('Final median', {'median': median}, ['median'])
        return median
""",
                "entry_point": "run_demo",
                "complexity_analysis": "Time: O(log N) per insertion, Space: O(N)"
            })

        # Default: Narrator response
        logger.debug(f"[{self.request_id}] Mock: Narrator response")
        return json.dumps({
            "title": "Median of Stream (Mock Mode)",
            "strategy": "Two-Heap Optimization",
            "strategy_details": "Mock response - connect a valid API key to enable dynamic synthesis.",
            "complexity": {
                "algorithm_name": "Two Heaps",
                "time": {"best": "O(log n)", "average": "O(log n)", "worst": "O(log n)", "explanation": "Heap operations"},
                "space": {"complexity": "O(n)", "explanation": "Storing elements in heaps"}
            },
            "frames": [
                {
                    "step_id": 0,
                    "commentary": "**Mock Mode Active**\n\nThis is a simulated response. Connect a valid API key to enable full functionality.",
                    "state": {"visual_type": "heap", "data": {"max_heap": [5], "min_heap": []}, "highlights": ["max_heap"]},
                    "quiz": None
                }
            ]
        })
