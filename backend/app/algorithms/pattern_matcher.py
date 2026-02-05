"""
Pattern Matcher - Identifies algorithms from user problem text.
Uses keyword matching, phrase detection, and fuzzy matching.
"""

import re
import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Singleton instance
_pattern_matcher_instance: Optional['PatternMatcher'] = None


@dataclass
class MatchResult:
    """Result of pattern matching."""
    algorithm_id: str
    algorithm_name: str
    category: str
    confidence: float  # 0.0 to 1.0
    matched_keywords: List[str]
    matched_phrases: List[str]


# Algorithm patterns database
ALGORITHM_PATTERNS: Dict[str, Dict] = {
    # ==================== SORTING ====================
    "quicksort": {
        "name": "QuickSort",
        "category": "sorting",
        "keywords": ["quicksort", "quick sort", "quick-sort", "pivot", "partition"],
        "phrases": ["divide and conquer sort", "in-place sorting", "pivot element", "partition array"],
        "exclude": ["merge", "heap", "bubble", "insertion"],
        "weight": 1.0
    },
    "mergesort": {
        "name": "MergeSort",
        "category": "sorting",
        "keywords": ["mergesort", "merge sort", "merge-sort"],
        "phrases": ["divide and conquer", "merge two sorted", "split and merge"],
        "exclude": ["quick", "heap", "bubble"],
        "weight": 1.0
    },
    "heapsort": {
        "name": "HeapSort",
        "category": "sorting",
        "keywords": ["heapsort", "heap sort", "heap-sort", "heapify"],
        "phrases": ["build heap", "extract max", "heap property"],
        "exclude": ["quick", "merge", "bubble"],
        "weight": 1.0
    },
    "bubblesort": {
        "name": "BubbleSort",
        "category": "sorting",
        "keywords": ["bubblesort", "bubble sort", "bubble-sort"],
        "phrases": ["adjacent elements", "swap adjacent", "bubble up"],
        "exclude": ["quick", "merge", "heap"],
        "weight": 0.9
    },
    "insertionsort": {
        "name": "InsertionSort",
        "category": "sorting",
        "keywords": ["insertionsort", "insertion sort", "insertion-sort"],
        "phrases": ["insert element", "sorted portion", "shift elements"],
        "exclude": ["quick", "merge", "heap", "bubble"],
        "weight": 0.9
    },
    "selectionsort": {
        "name": "SelectionSort",
        "category": "sorting",
        "keywords": ["selectionsort", "selection sort", "selection-sort"],
        "phrases": ["find minimum", "select minimum", "swap minimum"],
        "exclude": ["quick", "merge", "heap"],
        "weight": 0.9
    },

    # ==================== SEARCHING ====================
    "binary_search": {
        "name": "Binary Search",
        "category": "searching",
        "keywords": ["binary search", "binarysearch", "binary-search", "bisect"],
        "phrases": ["search sorted array", "divide in half", "log n search", "find in sorted"],
        "exclude": ["tree", "bst"],
        "weight": 1.0
    },
    "linear_search": {
        "name": "Linear Search",
        "category": "searching",
        "keywords": ["linear search", "sequential search", "linearsearch"],
        "phrases": ["search one by one", "iterate through", "find element"],
        "exclude": ["binary", "tree"],
        "weight": 0.8
    },

    # ==================== GRAPH ====================
    "bfs": {
        "name": "Breadth-First Search",
        "category": "graph",
        "keywords": ["bfs", "breadth first", "breadth-first", "level order"],
        "phrases": ["level by level", "queue based", "shortest path unweighted", "explore neighbors"],
        "exclude": ["dfs", "depth"],
        "weight": 1.0
    },
    "dfs": {
        "name": "Depth-First Search",
        "category": "graph",
        "keywords": ["dfs", "depth first", "depth-first"],
        "phrases": ["go deep", "stack based", "backtracking", "explore path"],
        "exclude": ["bfs", "breadth"],
        "weight": 1.0
    },
    "dijkstra": {
        "name": "Dijkstra's Algorithm",
        "category": "graph",
        "keywords": ["dijkstra", "dijkstras", "dijkstra's"],
        "phrases": ["shortest path", "weighted graph", "minimum distance", "priority queue"],
        "exclude": ["bellman", "floyd", "negative"],
        "weight": 1.0
    },
    "bellman_ford": {
        "name": "Bellman-Ford Algorithm",
        "category": "graph",
        "keywords": ["bellman", "bellman-ford", "bellmanford"],
        "phrases": ["negative weight", "relax edges", "detect negative cycle"],
        "exclude": ["dijkstra", "floyd"],
        "weight": 1.0
    },
    "floyd_warshall": {
        "name": "Floyd-Warshall Algorithm",
        "category": "graph",
        "keywords": ["floyd", "warshall", "floyd-warshall", "floydwarshall"],
        "phrases": ["all pairs shortest", "dynamic programming graph"],
        "exclude": ["dijkstra", "bellman"],
        "weight": 1.0
    },
    "kruskal": {
        "name": "Kruskal's MST",
        "category": "graph",
        "keywords": ["kruskal", "kruskals", "kruskal's"],
        "phrases": ["minimum spanning tree", "mst", "union find", "sort edges"],
        "exclude": ["prim"],
        "weight": 1.0
    },
    "prim": {
        "name": "Prim's MST",
        "category": "graph",
        "keywords": ["prim", "prims", "prim's"],
        "phrases": ["minimum spanning tree", "mst", "grow tree", "nearest vertex"],
        "exclude": ["kruskal"],
        "weight": 1.0
    },
    "topological_sort": {
        "name": "Topological Sort",
        "category": "graph",
        "keywords": ["topological", "topo sort", "toposort"],
        "phrases": ["directed acyclic", "dag", "dependency order", "prerequisite"],
        "exclude": [],
        "weight": 1.0
    },

    # ==================== DYNAMIC PROGRAMMING ====================
    "fibonacci": {
        "name": "Fibonacci Sequence",
        "category": "dp",
        "keywords": ["fibonacci", "fib"],
        "phrases": ["nth fibonacci", "fibonacci number", "f(n) = f(n-1) + f(n-2)"],
        "exclude": [],
        "weight": 1.0
    },
    "knapsack": {
        "name": "0/1 Knapsack",
        "category": "dp",
        "keywords": ["knapsack", "0/1 knapsack", "01 knapsack"],
        "phrases": ["maximum value", "weight capacity", "include or exclude"],
        "exclude": [],
        "weight": 1.0
    },
    "lcs": {
        "name": "Longest Common Subsequence",
        "category": "dp",
        "keywords": ["lcs", "longest common subsequence"],
        "phrases": ["common subsequence", "two strings", "subsequence match"],
        "exclude": ["substring", "lis"],
        "weight": 1.0
    },
    "lis": {
        "name": "Longest Increasing Subsequence",
        "category": "dp",
        "keywords": ["lis", "longest increasing subsequence"],
        "phrases": ["increasing order", "subsequence increasing"],
        "exclude": ["lcs", "common"],
        "weight": 1.0
    },
    "edit_distance": {
        "name": "Edit Distance",
        "category": "dp",
        "keywords": ["edit distance", "levenshtein"],
        "phrases": ["minimum operations", "insert delete replace", "transform string"],
        "exclude": [],
        "weight": 1.0
    },
    "coin_change": {
        "name": "Coin Change",
        "category": "dp",
        "keywords": ["coin change", "coins"],
        "phrases": ["minimum coins", "make change", "coin denominations"],
        "exclude": [],
        "weight": 1.0
    },
    "longest_palindrome": {
        "name": "Longest Palindromic Substring",
        "category": "dp",
        "keywords": ["palindrome", "palindromic"],
        "phrases": ["longest palindrome", "palindromic substring", "expand around center"],
        "exclude": [],
        "weight": 1.0
    },

    # ==================== STRING ====================
    "kmp": {
        "name": "KMP Pattern Matching",
        "category": "string",
        "keywords": ["kmp", "knuth morris pratt"],
        "phrases": ["pattern matching", "failure function", "prefix function"],
        "exclude": ["rabin", "z-algorithm"],
        "weight": 1.0
    },
    "rabin_karp": {
        "name": "Rabin-Karp",
        "category": "string",
        "keywords": ["rabin", "rabin-karp", "rabinkarp"],
        "phrases": ["rolling hash", "hash pattern", "string hashing"],
        "exclude": ["kmp"],
        "weight": 1.0
    },
    "trie": {
        "name": "Trie Operations",
        "category": "string",
        "keywords": ["trie", "prefix tree"],
        "phrases": ["prefix search", "autocomplete", "word dictionary"],
        "exclude": [],
        "weight": 1.0
    },

    # ==================== DATA STRUCTURES ====================
    "bst": {
        "name": "Binary Search Tree",
        "category": "data_structure",
        "keywords": ["bst", "binary search tree"],
        "phrases": ["insert node", "delete node", "search tree", "inorder traversal"],
        "exclude": ["avl", "red-black"],
        "weight": 1.0
    },
    "heap_operations": {
        "name": "Heap Operations",
        "category": "data_structure",
        "keywords": ["heap", "priority queue", "min heap", "max heap"],
        "phrases": ["insert heap", "extract min", "extract max", "heapify"],
        "exclude": ["heapsort"],
        "weight": 1.0
    },
    "hash_table": {
        "name": "Hash Table",
        "category": "data_structure",
        "keywords": ["hash table", "hashmap", "hash map", "dictionary"],
        "phrases": ["hash function", "collision", "key value"],
        "exclude": [],
        "weight": 0.9
    },

    # ==================== CLASSIC PROBLEMS ====================
    "two_sum": {
        "name": "Two Sum",
        "category": "classic",
        "keywords": ["two sum", "twosum", "2sum"],
        "phrases": ["find two numbers", "target sum", "indices of two", "pair that adds"],
        "exclude": ["three sum", "3sum"],
        "weight": 1.0
    },
    "three_sum": {
        "name": "Three Sum",
        "category": "classic",
        "keywords": ["three sum", "threesum", "3sum"],
        "phrases": ["three numbers", "triplets", "sum to zero"],
        "exclude": ["two sum"],
        "weight": 1.0
    },
    "sliding_window": {
        "name": "Sliding Window",
        "category": "technique",
        "keywords": ["sliding window", "window"],
        "phrases": ["fixed window", "variable window", "maximum sum subarray"],
        "exclude": [],
        "weight": 0.9
    },
    "two_pointer": {
        "name": "Two Pointer Technique",
        "category": "technique",
        "keywords": ["two pointer", "two pointers"],
        "phrases": ["left right pointer", "start end", "converging pointers"],
        "exclude": [],
        "weight": 0.9
    },
}


class PatternMatcher:
    """
    Identifies algorithms from user problem text.

    Uses multi-stage matching:
    1. Exact keyword match
    2. Phrase detection
    3. Exclusion filtering
    4. Confidence scoring
    """

    def __init__(self, patterns: Dict[str, Dict] = None):
        """Initialize with algorithm patterns."""
        self._patterns = patterns or ALGORITHM_PATTERNS

    def match(self, text: str, min_confidence: float = 0.3) -> Optional[MatchResult]:
        """
        Match text against algorithm patterns.

        Args:
            text: User's problem description
            min_confidence: Minimum confidence threshold

        Returns:
            MatchResult if match found, None otherwise
        """
        text_lower = text.lower()
        text_normalized = ' '.join(text_lower.split())  # Normalize whitespace

        best_match: Optional[MatchResult] = None
        best_score = 0.0

        for algo_id, pattern in self._patterns.items():
            score, matched_keywords, matched_phrases = self._score_pattern(
                text_normalized, pattern
            )

            # Apply weight
            weighted_score = score * pattern.get('weight', 1.0)

            if weighted_score > best_score and weighted_score >= min_confidence:
                best_score = weighted_score
                best_match = MatchResult(
                    algorithm_id=algo_id,
                    algorithm_name=pattern['name'],
                    category=pattern['category'],
                    confidence=weighted_score,
                    matched_keywords=matched_keywords,
                    matched_phrases=matched_phrases
                )

        if best_match:
            logger.info(f"Pattern match: {best_match.algorithm_name} (confidence: {best_match.confidence:.2f})")
        else:
            logger.debug(f"No pattern match found for: {text[:50]}...")

        return best_match

    def _score_pattern(self, text: str, pattern: Dict) -> Tuple[float, List[str], List[str]]:
        """
        Score how well text matches a pattern.

        Returns:
            (score, matched_keywords, matched_phrases)
        """
        matched_keywords = []
        matched_phrases = []

        # Check exclusions first
        for exclude in pattern.get('exclude', []):
            if exclude.lower() in text:
                return 0.0, [], []

        # Check keywords (each worth 0.3)
        keyword_score = 0.0
        for keyword in pattern.get('keywords', []):
            if keyword.lower() in text:
                matched_keywords.append(keyword)
                keyword_score += 0.3

        # Check phrases (each worth 0.2)
        phrase_score = 0.0
        for phrase in pattern.get('phrases', []):
            if phrase.lower() in text:
                matched_phrases.append(phrase)
                phrase_score += 0.2

        # Calculate total score (capped at 1.0)
        total_score = min(1.0, keyword_score + phrase_score)

        # Boost if multiple keywords matched
        if len(matched_keywords) >= 2:
            total_score = min(1.0, total_score + 0.1)

        return total_score, matched_keywords, matched_phrases

    def match_multiple(self, text: str, top_n: int = 3, min_confidence: float = 0.2) -> List[MatchResult]:
        """
        Get top N matching algorithms.

        Args:
            text: User's problem description
            top_n: Number of top matches to return
            min_confidence: Minimum confidence threshold

        Returns:
            List of MatchResults sorted by confidence
        """
        text_lower = text.lower()
        text_normalized = ' '.join(text_lower.split())

        results = []

        for algo_id, pattern in self._patterns.items():
            score, matched_keywords, matched_phrases = self._score_pattern(
                text_normalized, pattern
            )

            weighted_score = score * pattern.get('weight', 1.0)

            if weighted_score >= min_confidence:
                results.append(MatchResult(
                    algorithm_id=algo_id,
                    algorithm_name=pattern['name'],
                    category=pattern['category'],
                    confidence=weighted_score,
                    matched_keywords=matched_keywords,
                    matched_phrases=matched_phrases
                ))

        # Sort by confidence descending
        results.sort(key=lambda x: x.confidence, reverse=True)

        return results[:top_n]

    def quick_identify(self, text: str) -> Optional[str]:
        """
        Quick algorithm identification (just returns algorithm_id or None).
        Use this for fast routing decisions.
        """
        result = self.match(text, min_confidence=0.5)
        return result.algorithm_id if result else None

    def get_category_algorithms(self, category: str) -> List[str]:
        """Get all algorithm IDs in a category."""
        return [
            algo_id for algo_id, pattern in self._patterns.items()
            if pattern['category'] == category
        ]

    def get_all_algorithm_ids(self) -> List[str]:
        """Get all available algorithm IDs."""
        return list(self._patterns.keys())


def get_pattern_matcher() -> PatternMatcher:
    """Get singleton PatternMatcher instance."""
    global _pattern_matcher_instance
    if _pattern_matcher_instance is None:
        _pattern_matcher_instance = PatternMatcher()
    return _pattern_matcher_instance
