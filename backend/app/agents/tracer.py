
import traceback
import sys
import io
from app.utils.logger import get_logger

logger = get_logger("tracer")

class ExecutionSandbox:
    """Isolated execution environment for generated code"""

    def __init__(self):
        self.captured_trace = []

    def run(self, code_str: str, entry_point: str, inputs: list = None):
        """
        Execute instrumented code in isolated scope

        Args:
            code_str: Python code as string
            entry_point: Method name to call
            inputs: Input arguments (optional)

        Returns:
            Dictionary with status, trace_data, and logs
        """
        # Dedicated scope for execution
        execution_scope = {}

        logger.debug(f"Preparing to execute {entry_point}")
        logger.debug(f"Code length: {len(code_str)} chars")

        try:
            # Execute the code string
            logger.debug("Executing code with exec()...")
            exec(code_str, execution_scope)

            # Check if Solution class exists
            if 'Solution' not in execution_scope:
                error_msg = "Class 'Solution' not found in generated code."
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)

            # Instantiate Solution
            SolutionClass = execution_scope['Solution']
            instance = SolutionClass()
            logger.debug("Solution instance created")

            # Check if entry point exists
            if not hasattr(instance, entry_point):
                error_msg = f"Method '{entry_point}' not found in Solution class."
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)

            # Get the method
            method = getattr(instance, entry_point)

            # Execute the method
            # Note: entry_point should be 'run_demo' which takes NO parameters
            # run_demo() handles test data creation internally
            logger.info(f"▶️  Executing {entry_point}()...")
            method()

            # Extract the trace
            trace = getattr(instance, 'trace', [])

            if not trace:
                logger.warning("⚠️  Execution successful but trace is empty")
            else:
                logger.info(f"✓ Captured {len(trace)} trace steps")

            return {
                "status": "success",
                "trace_data": trace,
                "step_count": len(trace)
            }

        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"❌ Execution failed: {str(e)}")
            logger.error(f"Traceback:\n{error_trace}")

            return {
                "status": "error",
                "logs": error_trace
            }

def run_tracer(code: str, entry_point: str, inputs: list = None):
    """
    Public interface for tracer agent

    Args:
        code: Python code string
        entry_point: Method to call
        inputs: Optional inputs

    Returns:
        Execution results
    """
    logger.info("Initializing execution sandbox...")
    sandbox = ExecutionSandbox()
    result = sandbox.run(code, entry_point, inputs)

    if result['status'] == 'success':
        logger.info(f"✅ Sandbox execution successful")
    else:
        logger.error(f"❌ Sandbox execution failed")

    return result
