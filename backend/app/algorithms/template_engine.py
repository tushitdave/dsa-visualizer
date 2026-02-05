"""
Template Engine - Customizes pre-computed traces with user inputs.
"""

import copy
import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    Customizes algorithm templates with user-provided inputs.

    Features:
    - Variable substitution in commentary
    - Input data replacement in frames
    - Quiz regeneration with new values
    - Maintains trace integrity
    """

    @staticmethod
    def customize_trace(
        template: Dict,
        user_inputs: Optional[Dict] = None,
        problem_text: str = ""
    ) -> Dict:
        """
        Customize a template trace with user inputs.

        Args:
            template: Pre-computed trace template
            user_inputs: User-provided input values
            problem_text: Original problem text for context

        Returns:
            Customized trace data
        """
        if not template:
            return template

        # Deep copy to avoid modifying original
        trace = copy.deepcopy(template)

        if not user_inputs:
            return trace

        # Extract input arrays/values from user_inputs
        input_arrays = TemplateEngine._extract_arrays(user_inputs)

        if input_arrays:
            # Customize frames with new data
            trace['frames'] = TemplateEngine._customize_frames(
                trace.get('frames', []),
                input_arrays
            )

            # Update title if needed
            if 'title' in trace:
                trace['title'] = TemplateEngine._customize_text(
                    trace['title'],
                    input_arrays
                )

        return trace

    @staticmethod
    def _extract_arrays(user_inputs: Dict) -> Dict[str, List]:
        """Extract array-like inputs for substitution."""
        arrays = {}

        for key, value in user_inputs.items():
            if isinstance(value, list):
                arrays[key] = value
            elif isinstance(value, str):
                # Try to parse as array
                try:
                    parsed = eval(value)  # Safe in controlled context
                    if isinstance(parsed, (list, tuple)):
                        arrays[key] = list(parsed)
                except:
                    pass

        return arrays

    @staticmethod
    def _customize_frames(frames: List[Dict], input_arrays: Dict) -> List[Dict]:
        """Customize frame data with new inputs."""
        if not frames or not input_arrays:
            return frames

        customized = []

        # Get the primary input array (usually 'arr', 'nums', or 'input')
        primary_key = None
        primary_array = None
        for key in ['arr', 'nums', 'input', 'array', 'data']:
            if key in input_arrays:
                primary_key = key
                primary_array = input_arrays[key]
                break

        if not primary_array:
            # Use first array found
            if input_arrays:
                primary_key, primary_array = next(iter(input_arrays.items()))

        for frame in frames:
            new_frame = copy.deepcopy(frame)

            # Update state data
            if 'state' in new_frame and 'data' in new_frame['state']:
                new_frame['state']['data'] = TemplateEngine._substitute_data(
                    new_frame['state']['data'],
                    input_arrays,
                    primary_array
                )

            # Update commentary
            if 'commentary' in new_frame and primary_array:
                new_frame['commentary'] = TemplateEngine._customize_text(
                    new_frame['commentary'],
                    input_arrays
                )

            customized.append(new_frame)

        return customized

    @staticmethod
    def _substitute_data(data: Dict, input_arrays: Dict, primary_array: List) -> Dict:
        """Substitute data values in frame state."""
        if not data or not primary_array:
            return data

        new_data = {}

        for key, value in data.items():
            if isinstance(value, list):
                # Check if this is the main array to substitute
                if key in input_arrays:
                    new_data[key] = input_arrays[key]
                elif key in ['arr', 'nums', 'input', 'array'] and primary_array:
                    # Substitute with primary array, maintaining length if needed
                    if len(value) <= len(primary_array):
                        new_data[key] = primary_array[:len(value)]
                    else:
                        new_data[key] = value  # Keep original if user input is shorter
                else:
                    new_data[key] = value
            else:
                new_data[key] = value

        return new_data

    @staticmethod
    def _customize_text(text: str, input_arrays: Dict) -> str:
        """Replace array references in text."""
        if not text or not input_arrays:
            return text

        # Replace array representations like [1, 2, 3] with new values
        for key, arr in input_arrays.items():
            # Replace patterns like "array: [...]" or "[original values]"
            text = re.sub(
                r'\[[\d,\s]+\]',
                str(arr),
                text,
                count=1  # Only first occurrence
            )

        return text

    @staticmethod
    def generate_custom_quizzes(
        algorithm_id: str,
        quiz_bank: List[Dict],
        frame_count: int = 10
    ) -> List[Dict]:
        """
        Generate quiz placements for frames.

        Args:
            algorithm_id: Algorithm identifier
            quiz_bank: Available quiz questions
            frame_count: Number of frames

        Returns:
            List of quizzes with frame assignments
        """
        if not quiz_bank:
            return []

        quizzes = []
        quiz_interval = max(2, frame_count // (len(quiz_bank) + 1))

        for i, quiz in enumerate(quiz_bank):
            insert_at = min((i + 1) * quiz_interval, frame_count - 1)
            quizzes.append({
                'frame_index': insert_at,
                'quiz': quiz
            })

        return quizzes

    @staticmethod
    def merge_quizzes_into_frames(
        frames: List[Dict],
        quizzes: List[Dict]
    ) -> List[Dict]:
        """Insert quizzes into appropriate frames."""
        if not quizzes:
            return frames

        frames = copy.deepcopy(frames)

        for quiz_data in quizzes:
            frame_idx = quiz_data.get('frame_index', 0)
            if 0 <= frame_idx < len(frames):
                frames[frame_idx]['quiz'] = quiz_data.get('quiz')

        return frames

    @staticmethod
    def validate_trace(trace: Dict) -> bool:
        """
        Validate that trace has required structure.

        Returns:
            True if valid
        """
        if not trace:
            return False

        required = ['frames']
        for field in required:
            if field not in trace:
                return False

        frames = trace.get('frames', [])
        if not frames:
            return False

        for frame in frames:
            if 'state' not in frame:
                return False
            if 'data' not in frame.get('state', {}):
                return False

        return True
