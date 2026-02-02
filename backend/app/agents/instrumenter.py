
import json
from app.utils.llm_provider import llm
from app.utils.logger import get_logger, log_error_with_context

logger = get_logger("instrumenter")

async def run_instrumenter(blueprint: dict, normalized_data: dict) -> dict:
    """
    Generate instrumented Python code for the selected algorithm

    Args:
        blueprint: Output from strategist agent
        normalized_data: Output from normalizer (includes example inputs)

    Returns:
        Dictionary with generated code and entry point
    """
    strategy = blueprint.get('selected_strategy_for_instrumentation', 'Unknown')
    example_inputs = normalized_data.get('example_inputs', [])

    logger.info(f"Generating instrumented code for: {strategy}")
    if example_inputs:
        logger.info(f"Using example inputs: {example_inputs[0].get('input_vars', {})}")

    # Build example inputs section
    example_section = ""
    if example_inputs and len(example_inputs) > 0:
        first_example = example_inputs[0]
        input_vars = first_example.get('input_vars', {})
        expected_output = first_example.get('expected_output', 'Unknown')

        example_section = f"""
    ╔══════════════════════════════════════════════════════════════════╗
    ║  CRITICAL: USE THESE EXACT INPUT VALUES IN run_demo()            ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Input Variables: {json.dumps(input_vars)}
    ║  Expected Output: {expected_output}
    ╚══════════════════════════════════════════════════════════════════╝

    Your run_demo() function MUST use these exact values, NOT made-up examples!
    For example, if input_vars shows {{"s": "babad"}}, your run_demo() should have:
        test_input = "babad"  # From problem example
    """
    else:
        example_section = """
    No specific example inputs provided. Create reasonable test data for the algorithm.
    """

    system_instruction = """You are a Lead Python Developer specializing in algorithm instrumentation for educational visualizations.
    Create code that logs MEANINGFUL ALGORITHMIC STEPS, not individual variable updates."""

    prompt = f"""
    Implement this algorithm: {strategy}

    {example_section}

    INSTRUMENTATION REQUIREMENTS:

    1. **CLASS STRUCTURE**:
       - Define class `Solution`
       - Initialize `self.trace = []` in `__init__`
       - Implement `self.log(step_name, variables, highlights)` method
       - CRITICAL: Implement `run_demo(self)` method with NO parameters

    2. **THE run_demo() METHOD** (MANDATORY):
       This method must:
       - Take NO parameters (def run_demo(self):)
       - Extract test parameters from the problem description
       - Create appropriate test data structures
       - Call the main algorithm method
       - Return the result

       **Examples by Data Structure:**

       **Linked List Problems:**
       ```python
       def run_demo(self):
           class ListNode:
               def __init__(self, val=0, next=None):
                   self.val = val
                   self.next = next

           # Build test list from problem example
           head = ListNode(1, ListNode(2, ListNode(3, ListNode(4, ListNode(5)))))
           k = 2  # Extract k value from problem description

           result = self.reverseKGroup(head, k)
           return result
       ```

       **Array/String Problems:**
       ```python
       def run_demo(self):
           test_input = "babad"  # From problem example
           result = self.longestPalindrome(test_input)
           return result
       ```

       **Tree Problems:**
       ```python
       def run_demo(self):
           class TreeNode:
               def __init__(self, val=0, left=None, right=None):
                   self.val = val
                   self.left = left
                   self.right = right

           # Build test tree
           root = TreeNode(3)
           root.left = TreeNode(9)
           root.right = TreeNode(20, TreeNode(15), TreeNode(7))

           result = self.maxDepth(root)
           return result
       ```

       **Graph Problems:**
       ```python
       def run_demo(self):
           graph = [[1,2], [0,2], [0,1]]  # From problem example
           result = self.isBipartite(graph)
           return result
       ```

       **Mathematical/Single-Value Problems (sqrt, pow, etc.):**
       ```python
       def run_demo(self):
           x = 4  # EXACT value from problem example - DO NOT create arrays!
           result = self.mySqrt(x)
           return result
       ```

       IMPORTANT FOR MATHEMATICAL PROBLEMS:
       - If input is a single number like x=4, visualize it as 'x': 4, NOT as an array!
       - Show the actual search boundaries (low, high) as they change
       - Do NOT fabricate arrays like [1,2,3,4,5] - that's NOT the user's input!

    3. **LOGGING STRATEGY** (CRITICAL):
       ❌ BAD: Log every single variable assignment (creates 20+ micro-steps)
       ```python
       self.log('Set start', {{'start': 0}}, [])
       self.log('Set end', {{'end': 0}}, [])
       self.log('Set i', {{'i': 0}}, [])
       ```

       ✅ GOOD: Group related operations into logical steps (aim for ~10-15 steps)
       ```python
       self.log('Initialize pointers and input', {{
           'input_data': list(s),
           'start': 0,
           'end': 0,
           'max_length': 1
       }}, ['start', 'end'])
       ```

    4. **WHEN TO LOG** - Only log at these moments:
       - ✅ Initialization (setup phase with ALL initial state)
       - ✅ Before/after significant operations (swaps, comparisons, expansions)
       - ✅ When multiple related variables update together
       - ✅ At decision points (if/else branches)
       - ❌ NOT for every single variable update
       - ❌ NOT for loop counter increments unless meaningful

    5. **DATA TO INCLUDE**:
       - ALWAYS include the ACTUAL input from the problem in first log
       - If input is a single number (x=4), show it as 'x': 4, NOT as an array!
       - If input is an array, show the actual array values
       - NEVER fabricate/invent arrays that weren't in the original input
       - For binary search on a range, show 'low' and 'high' boundaries, not a fake array
       - Group related variables (left, right, center together)
       - Use descriptive variable names matching the problem (x, target, nums, etc.)

    6. **LOG FORMAT**:
       ```python
       self.log(
           'Step description',  # Brief, actionable description
           {{
               'input_array': [...],     # Include when relevant
               'pointers': {{...}},        # Group related vars
               'result': {{...}}
           }},
           ['input_array[i]', 'pointers']  # What to highlight
       )
       ```

    7. **COMPLETE EXAMPLE CODE PATTERNS**:

       **Example A - String Problem (palindrome):**
       ```python
       class Solution:
           def __init__(self):
               self.trace = []

           def log(self, step, vars, highlights):
               self.trace.append({{
                   'step': step,
                   'vars': vars,
                   'highlights': highlights
               }})

           def run_demo(self):
               test_string = "babad"  # From problem example
               result = self.longestPalindrome(test_string)
               return result

           def longestPalindrome(self, s):
               self.log('Initialize', {{
                   'input_s': list(s),
                   'start': 0,
                   'end': 0
               }}, ['input_s'])
               # ... algorithm logic with meaningful logs
               return s[start:end+1]
       ```

       **Example B - Mathematical Problem (sqrt, binary search on range):**
       ```python
       class Solution:
           def __init__(self):
               self.trace = []

           def log(self, step, vars, highlights):
               self.trace.append({{
                   'step': step,
                   'vars': vars,
                   'highlights': highlights
               }})

           def run_demo(self):
               x = 4  # EXACT input from problem - just the number!
               result = self.mySqrt(x)
               return result

           def mySqrt(self, x):
               # Show ACTUAL input x, not a fabricated array!
               self.log('Initialize binary search', {{
                   'x': x,           # The actual input: 4
                   'low': 0,         # Search boundary
                   'high': x         # Search boundary
               }}, ['x'])

               low, high = 0, x
               while low <= high:
                   mid = (low + high) // 2
                   self.log('Check middle value', {{
                       'x': x,
                       'low': low,
                       'high': high,
                       'mid': mid,
                       'mid_squared': mid * mid
                   }}, ['mid'])

                   if mid * mid == x:
                       return mid
                   elif mid * mid < x:
                       low = mid + 1
                   else:
                       high = mid - 1
               return high
       ```

       ⚠️ WRONG for sqrt: Creating INPUT_ARRAY: [1,2,3,4,5] - that's NOT the input!
       ✅ CORRECT for sqrt: Showing x: 4, low: 0, high: 4 - the actual values!

    GENERATE CODE:
    - MUST include run_demo() method with NO parameters
    - run_demo() extracts test data from problem description
    - Aim for 10-15 log calls total (not 20+)
    - Each log should represent a significant algorithm step
    - Always include input data in first log
    - Group related variables together
    - Use meaningful step descriptions

    Return JSON:
    {{
        "code": "Full Python code as string (MUST include run_demo() method)",
        "entry_point": "run_demo",
        "complexity_analysis": "Time and space complexity explanation"
    }}

    CRITICAL REMINDER:
    - entry_point MUST be "run_demo"
    - run_demo() must take NO parameters
    - run_demo() creates test data internally based on problem description
    - This makes the code self-contained and executable without external inputs
    """

    try:
        logger.debug("Calling LLM (Pro tier) for code generation...")
        response_text = await llm.call(prompt, system_instruction=system_instruction, json_mode=True, model_tier="pro")

        code_data = json.loads(response_text)

        entry_point = code_data.get('entry_point', 'Unknown')
        code_length = len(code_data.get('code', ''))

        logger.info(f"✓ Code generated: {code_length} characters")
        logger.info(f"Entry point: {entry_point}")
        logger.debug(f"Code preview:\n{code_data.get('code', '')[:300]}...")

        return code_data

    except Exception as e:
        log_error_with_context(logger, e, {"strategy": strategy})
        raise
