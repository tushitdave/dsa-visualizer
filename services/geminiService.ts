
import { TraceData } from "../types";

export const DEMO_TRACE: TraceData = {
  "title": "Median of Stream (Standalone Mode)",
  "strategy": "Two-Heap Optimization",
  "strategy_details": "The Two-Heap strategy maintains a Max-Heap for the lower half of data and a Min-Heap for the upper half. This ensures the median is always at the root of one (or both) heaps, providing O(1) access. Insertions stay O(log N).",
  "complexity": {"time": "O(log n)", "space": "O(n)"},
  "frames": [
    {
      "step_id": 0,
      "commentary": "Welcome to AlgoInsight Standalone. We initialize two heaps. First, we push **15** into the Max Heap (representing the smaller half).",
      "state": {
        "visual_type": "heap",
        "data": { "max_heap": [15], "min_heap": [] },
        "highlights": ["max_heap"]
      },
      "quiz": null
    },
    {
      "step_id": 1,
      "commentary": "To maintain the balance where the Min-Heap contains the larger elements, we move the top of the Max-Heap to the Min-Heap.",
      "state": {
        "visual_type": "heap",
        "data": { "max_heap": [], "min_heap": [15] },
        "highlights": ["min_heap"]
      },
      "quiz": {
         "question": "If we add a new value 20, where should it go first?",
         "options": ["Always Max-Heap", "Always Min-Heap", "Depends on the current median"],
         "correct": 0
      }
    }
  ]
};

export const MOCK_TRACE: TraceData = {
  "title": "AlgoInsight Initialized",
  "strategy": "System Ready",
  "strategy_details": "Enter a problem in the sidebar to generate a custom step-by-step trace. The engine will synthesize a high-fidelity visual animation of the best algorithm for your constraints.",
  "complexity": {"time": "---", "space": "---"},
  "frames": [
    {
      "step_id": 0,
      "commentary": "### Standing By...\n\nEnter a problem (e.g. 'Sort an array' or 'BFS traversal') to begin. Make sure the backend server is running at localhost:8000.",
      "state": {
        "visual_type": "array",
        "data": { "status": ["R", "E", "A", "D", "Y"] },
        "highlights": ["status"]
      },
      "quiz": null
    }
  ]
};
