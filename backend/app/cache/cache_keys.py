"""
Cache key generation utilities.
Provides consistent key generation for all cache levels.
"""

import hashlib
import json
from typing import List, Optional, Any


class CacheKeys:
    """Generates cache keys for different cache levels."""

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for consistent hashing."""
        return ' '.join(text.lower().split())

    @staticmethod
    def _hash_string(s: str) -> str:
        """Generate SHA256 hash of string."""
        return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]

    @classmethod
    def l1_exact_match(cls, problem_text: str, context_toggles: List[str]) -> str:
        """
        L1 Cache Key: Exact problem match.
        Hash of (problem_text + sorted context_toggles)
        """
        normalized = cls._normalize_text(problem_text)
        toggles_str = ','.join(sorted(context_toggles))
        combined = f"{normalized}|{toggles_str}"
        return f"l1:{cls._hash_string(combined)}"

    @classmethod
    def l2_normalized_match(cls, objective: str, input_structure: str, output_structure: str) -> str:
        """
        L2 Cache Key: Normalized problem structure match.
        Hash of (objective + input_structure + output_structure)
        """
        combined = f"{cls._normalize_text(objective)}|{input_structure}|{output_structure}"
        return f"l2:{cls._hash_string(combined)}"

    @classmethod
    def l3_algorithm_match(cls, algorithm_name: str, input_size_category: str = "medium") -> str:
        """
        L3 Cache Key: Algorithm pattern match.
        Key: algorithm_name + input_size_category
        """
        algo_normalized = algorithm_name.lower().replace(' ', '_').replace('-', '_')
        return f"l3:{algo_normalized}:{input_size_category}"

    @classmethod
    def strategy_cache(cls, normalized_hash: str) -> str:
        """Cache key for strategy results."""
        return f"strategy:{normalized_hash}"

    @classmethod
    def code_cache(cls, algorithm_name: str, input_signature: str) -> str:
        """Cache key for generated code."""
        algo_normalized = algorithm_name.lower().replace(' ', '_')
        sig_hash = cls._hash_string(input_signature)
        return f"code:{algo_normalized}:{sig_hash}"

    @classmethod
    def get_input_size_category(cls, data: Any) -> str:
        """Categorize input size for cache key generation."""
        size = 0
        if isinstance(data, (list, tuple)):
            size = len(data)
        elif isinstance(data, dict):
            size = sum(len(v) if isinstance(v, (list, tuple)) else 1 for v in data.values())
        elif isinstance(data, str):
            size = len(data)
        elif isinstance(data, int):
            size = data

        if size <= 8:
            return "small"
        elif size <= 20:
            return "medium"
        else:
            return "large"
