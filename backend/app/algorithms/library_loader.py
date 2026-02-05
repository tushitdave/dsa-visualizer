"""
Algorithm Library Loader - Loads and manages pre-computed algorithm templates.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Singleton instance
_library_instance: Optional['AlgorithmLibrary'] = None


@dataclass
class AlgorithmTemplate:
    """Pre-computed algorithm template."""
    algorithm_id: str
    algorithm_name: str
    category: str
    complexity: Dict[str, Any]
    strategy: str
    strategy_details: str
    templates: Dict[str, Any]  # size -> template data
    quiz_bank: List[Dict]


class AlgorithmLibrary:
    """
    Manages pre-computed algorithm templates.

    Loads JSON files from precomputed/ directory and provides
    instant access to algorithm visualizations.
    """

    def __init__(self, precomputed_dir: str = None):
        """
        Initialize library.

        Args:
            precomputed_dir: Directory containing pre-computed JSON files
        """
        if precomputed_dir is None:
            precomputed_dir = Path(__file__).parent / "precomputed"

        self._precomputed_dir = Path(precomputed_dir)
        self._algorithms: Dict[str, AlgorithmTemplate] = {}
        self._loaded = False

    def load(self) -> int:
        """
        Load all pre-computed algorithms from disk.

        Returns:
            Number of algorithms loaded
        """
        if not self._precomputed_dir.exists():
            logger.warning(f"Precomputed directory not found: {self._precomputed_dir}")
            return 0

        count = 0

        for json_file in self._precomputed_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                algo_id = data.get('algorithm_id', json_file.stem)

                self._algorithms[algo_id] = AlgorithmTemplate(
                    algorithm_id=algo_id,
                    algorithm_name=data.get('algorithm_name', algo_id),
                    category=data.get('category', 'unknown'),
                    complexity=data.get('complexity', {}),
                    strategy=data.get('strategy', ''),
                    strategy_details=data.get('strategy_details', ''),
                    templates=data.get('templates', {}),
                    quiz_bank=data.get('quiz_bank', [])
                )

                count += 1
                logger.debug(f"Loaded algorithm: {algo_id}")

            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")

        self._loaded = True
        logger.info(f"Algorithm library loaded: {count} algorithms")
        return count

    def get(self, algorithm_id: str) -> Optional[AlgorithmTemplate]:
        """
        Get algorithm template by ID.

        Args:
            algorithm_id: Algorithm identifier

        Returns:
            AlgorithmTemplate or None
        """
        if not self._loaded:
            self.load()

        return self._algorithms.get(algorithm_id.lower().replace(' ', '_').replace('-', '_'))

    def get_template(self, algorithm_id: str, size: str = "medium") -> Optional[Dict]:
        """
        Get specific size template for algorithm.

        Args:
            algorithm_id: Algorithm identifier
            size: Size category (small/medium/large)

        Returns:
            Template data or None
        """
        algo = self.get(algorithm_id)
        if not algo:
            return None

        # Try exact size match
        for key, template in algo.templates.items():
            if size in key:
                return template

        # Return first available
        if algo.templates:
            return list(algo.templates.values())[0]

        return None

    def get_full_trace(self, algorithm_id: str, size: str = "medium") -> Optional[Dict]:
        """
        Get complete trace data ready for frontend.

        Args:
            algorithm_id: Algorithm identifier
            size: Size category

        Returns:
            Complete trace data or None
        """
        algo = self.get(algorithm_id)
        if not algo:
            return None

        template = self.get_template(algorithm_id, size)
        if not template:
            return None

        # Build complete trace response
        return {
            'title': f"{algo.algorithm_name} Visualization",
            'strategy': algo.strategy,
            'strategy_details': algo.strategy_details,
            'complexity': algo.complexity,
            'frames': template.get('frames', []),
            '_meta': {
                'source': 'precomputed_library',
                'algorithm_id': algorithm_id,
                'size': size,
                'cached': True
            }
        }

    def has_algorithm(self, algorithm_id: str) -> bool:
        """Check if algorithm exists in library."""
        if not self._loaded:
            self.load()
        return algorithm_id.lower().replace(' ', '_').replace('-', '_') in self._algorithms

    def list_algorithms(self) -> List[str]:
        """Get list of all algorithm IDs."""
        if not self._loaded:
            self.load()
        return list(self._algorithms.keys())

    def list_by_category(self, category: str) -> List[str]:
        """Get algorithms in a specific category."""
        if not self._loaded:
            self.load()
        return [
            algo_id for algo_id, algo in self._algorithms.items()
            if algo.category == category
        ]

    def get_categories(self) -> List[str]:
        """Get all available categories."""
        if not self._loaded:
            self.load()
        return list(set(algo.category for algo in self._algorithms.values()))

    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        if not self._loaded:
            self.load()

        categories = {}
        for algo in self._algorithms.values():
            categories[algo.category] = categories.get(algo.category, 0) + 1

        return {
            'total_algorithms': len(self._algorithms),
            'categories': categories,
            'loaded': self._loaded,
            'directory': str(self._precomputed_dir)
        }


def get_algorithm_library() -> AlgorithmLibrary:
    """Get singleton AlgorithmLibrary instance."""
    global _library_instance
    if _library_instance is None:
        _library_instance = AlgorithmLibrary()
        _library_instance.load()
    return _library_instance
