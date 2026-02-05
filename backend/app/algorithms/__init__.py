"""
Algorithm library module for AlgoInsight.
Provides pattern matching and pre-computed algorithm templates.
"""

from .pattern_matcher import PatternMatcher, get_pattern_matcher
from .library_loader import AlgorithmLibrary, get_algorithm_library
from .template_engine import TemplateEngine

__all__ = [
    'PatternMatcher',
    'get_pattern_matcher',
    'AlgorithmLibrary',
    'get_algorithm_library',
    'TemplateEngine'
]
