import os
import json
from google import genai
from google.genai import types
from openai import AzureOpenAI
from dotenv import load_dotenv
from app.utils.logger import get_logger, log_error_with_context

load_dotenv()

logger = get_logger("llm_provider")

class LLMProvider:
    def __init__(self):
        self.azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_version = os.getenv("AZURE_API_VERSION", "2024-08-01-preview")
        self.azure_deployment = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4o")
        self.gemini_key = os.getenv("API_KEY")

        logger.info("LLMProvider initialized")
        self._log_config_status()

    def _log_config_status(self):
        
        if self._is_valid_key(self.azure_key):
            logger.info(f"[OK] Azure OpenAI configured (endpoint: {self.azure_endpoint[:30]}...)")
        else:
            logger.debug("Azure OpenAI not configured")

        if self._is_valid_key(self.gemini_key):
            logger.info("[OK] Gemini API configured")
        else:
            logger.debug("Gemini API not configured")

        if not self._is_valid_key(self.azure_key) and not self._is_valid_key(self.gemini_key):
            logger.warning("[WARNING] No valid API keys - will use mock responses")

    def _is_valid_key(self, key):
        if not key: return False
        if "YOUR_" in str(key) or "REPLACE" in str(key) or len(str(key)) < 15:
            return False
        return True

    def _call_azure(self, prompt: str, system_instruction: str = None, json_mode: bool = True):
        
        logger.debug(f"Calling Azure OpenAI (model: {self.azure_deployment})")

        try:
            client = AzureOpenAI(
                api_key=self.azure_key,
                api_version=self.azure_version,
                azure_endpoint=self.azure_endpoint
            )

            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            logger.debug(f"Prompt length: {len(prompt)} chars")

            response = client.chat.completions.create(
                model=self.azure_deployment,
                messages=messages,
                response_format={"type": "json_object"} if json_mode else {"type": "text"},
                temperature=0.3
            )

            result = response.choices[0].message.content
            logger.info(f"[OK] Azure response received ({len(result)} chars)")

            return result

        except Exception as e:
            logger.error(f"[ERROR] Azure call failed: {str(e)}")
            raise

    def _call_gemini(self, prompt: str, system_instruction: str = None, json_mode: bool = True, model_name: str = "gemini-2.5-flash"):
        
        logger.debug(f"Calling Gemini (model: {model_name})")

        try:
            client = genai.Client(api_key=self.gemini_key)

            config = {}
            if system_instruction:
                config["system_instruction"] = system_instruction
            if json_mode:
                config["response_mime_type"] = "application/json"

            logger.debug(f"Prompt length: {len(prompt)} chars")

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            result = response.text

            logger.info(f"[OK] Gemini response received ({len(result)} chars)")

            return result

        except Exception as e:
            logger.error(f"[ERROR] Gemini call failed: {str(e)}")
            raise

    async def call(self, prompt: str, system_instruction: str = None, json_mode: bool = True, model_tier: str = "flash"):
        
        logger.debug(f"LLM call requested (tier: {model_tier}, json_mode: {json_mode})")

        if self._is_valid_key(self.azure_key):
            try:
                logger.info("→ Attempting Azure OpenAI...")
                return self._call_azure(prompt, system_instruction, json_mode)
            except Exception as e:
                logger.warning(f"Azure failed, falling back to Gemini")
                log_error_with_context(logger, e, {"prompt_preview": prompt[:100]})

        if self._is_valid_key(self.gemini_key):
            try:
                logger.info(f"→ Attempting Gemini ({model_tier} tier)...")
                m_name = "gemini-2.5-flash" if model_tier == "flash" else "gemini-2.5-pro"
                return self._call_gemini(prompt, system_instruction, json_mode, m_name)
            except Exception as e:
                logger.error("Gemini failed, falling back to mock response")
                log_error_with_context(logger, e, {"prompt_preview": prompt[:100]})

        logger.warning("[WARNING]  All LLM providers failed - returning mock response")
        return self._generate_mock_response(system_instruction)

    def _generate_mock_response(self, system_instruction: str):
        
        logger.info("Generating context-aware mock response")

        instr = str(system_instruction).lower()

        if "gatekeeper" in instr:
            logger.debug("Mock: Normalizer response")
            return json.dumps({
                "objective": "Two-Heap Median Finder",
                "input_structure": "Stream of Integers",
                "output_structure": "Float",
                "math_constraints": ["N < 10^5"],
                "system_constraints": ["low_latency"],
                "intent": "LEARN",
                "main_dsa_topic": "Heaps",
                "was_sanitized": False
            })

        if "architect" in instr:
            logger.debug("Mock: Strategist response")
            return json.dumps({
                "analysis_summary": "Using Min-Max heaps for streaming median.",
                "options": [],
                "selected_strategy_for_instrumentation": "Median of Stream Algorithm"
            })

        if "lead python developer" in instr or "instrumentation" in instr:
            logger.debug("Mock: Instrumenter response")
            return json.dumps({
                "code": "import heapq\nclass Solution:\n    def __init__(self): self.trace = []; self.mx = []; self.mn = []\n    def log(self, s, v, h): self.trace.append({'step': s, 'vars': v, 'highlights': h})\n    def find(self, l): \n        for x in l:\n            heapq.heappush(self.mx, -x)\n            self.log('Push Max', {'max':[-v for v in self.mx]}, ['max'])\n            if self.mx: \n                v = -heapq.heappop(self.mx); heapq.heappush(self.mn, v)\n                self.log('Balanced', {'min':list(self.mn)}, ['min'])",
                "entry_point": "find",
                "complexity_analysis": "O(log N)"
            })

        logger.debug("Mock: Default (Narrator) response")
        return json.dumps({
            "title": "Median of Stream (Mock Execution)",
            "strategy": "Two-Heap Optimization",
            "strategy_details": "Simulated output due to missing API keys. Connect a valid key in backend/.env to enable dynamic synthesis.",
            "complexity": {"time": "O(log N)", "space": "O(N)"},
            "frames": [
                {
                    "step_id": 0,
                    "commentary": "Initial state. Welcome to AlgoInsight! (Simulated Mode)",
                    "state": {"visual_type": "heap", "data": {"max_heap": [15]}, "highlights": ["max_heap"]},
                    "quiz": None
                }
            ]
        })

llm = LLMProvider()

logger.info("LLM Provider module loaded")
