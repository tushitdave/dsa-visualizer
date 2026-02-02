
import { GoogleGenAI, Type } from "@google/genai";
import { TraceData, ContextOption, ModelName } from "../types";

const ENGINEERING_HEURISTICS: Record<string, string> = {
  "low_latency": "Prefer O(1) or O(log n) lookups. Avoid GC heavy operations (like massive HashMaps).",
  "embedded": "Strict Memory limit. Avoid Recursion. Prefer In-place algorithms (O(1) Space).",
  "embedded system": "Strict Memory limit. Avoid Recursion. Prefer In-place algorithms (O(1) Space).",
  "high_throughput": "Minimize locking. Use localized data structures to prevent cache misses.",
  "high throughput": "Minimize locking. Use localized data structures to prevent cache misses.",
  "low_memory": "Strict Memory limit. Prefer In-place algorithms (O(1) Space). Avoid creating new data structures.",
  "low memory": "Strict Memory limit. Prefer In-place algorithms (O(1) Space). Avoid creating new data structures.",
  "real_time": "Deterministic execution required. Avoid amortized analysis.",
  "large_dataset": "Streaming algorithms required. Cannot load all into RAM.",
  "threading": "Avoid shared mutable state. Prefer Immutable data structures."
};

const ALGORITHM_SELECTION_RULES: Record<string, string[]> = {
  "low_memory": ["Two Pointer", "Sliding Window", "Morris Traversal", "In-place Sort", "Bit Manipulation"],
  "low memory": ["Two Pointer", "Sliding Window", "Morris Traversal", "In-place Sort", "Bit Manipulation"],
  "embedded": ["Two Pointer", "Sliding Window", "Morris Traversal", "In-place algorithms"],
  "embedded system": ["Two Pointer", "Sliding Window", "Morris Traversal", "In-place algorithms"],
  "low_latency": ["Binary Search", "Hash Map", "Two Pointer", "Heap"],
  "high_throughput": ["Hash Map", "Sorting", "Binary Search"],
  "high throughput": ["Hash Map", "Sorting", "Binary Search"]
};

const consultHeuristics = (contexts: ContextOption[]): string => {
  if (!contexts || contexts.length === 0) {
    return "No specific constraints. Optimize for standard Time/Space balance.";
  }

  const advice: string[] = [];
  const preferredAlgorithms: Set<string> = new Set();

  const normalizedContexts = contexts.map(c => c.toLowerCase());

  for (const constraint of normalizedContexts) {
    for (const [key, rule] of Object.entries(ENGINEERING_HEURISTICS)) {
      if (constraint.includes(key) || key.includes(constraint.split(' ')[0])) {
        advice.push(`RULE [${key.toUpperCase().replace(' ', '_')}]: ${rule}`);
      }
    }

    for (const [key, algorithms] of Object.entries(ALGORITHM_SELECTION_RULES)) {
      if (constraint.includes(key) || key.includes(constraint.split(' ')[0])) {
        algorithms.forEach(algo => preferredAlgorithms.add(algo));
      }
    }
  }

  let result = advice.length > 0
    ? advice.join("\n")
    : "Optimize for standard Time/Space balance.";

  if (preferredAlgorithms.size > 0) {
    result += `\n\nPREFERRED ALGORITHMS for these constraints: ${Array.from(preferredAlgorithms).join(", ")}`;
  }

  return result;
};

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

const traceSchema = {
  type: Type.OBJECT,
  properties: {
    title: { type: Type.STRING },
    strategy: { type: Type.STRING },
    strategy_details: { type: Type.STRING },
    complexity: {
      type: Type.OBJECT,
      properties: {
        time: { type: Type.STRING },
        space: { type: Type.STRING }
      },
      required: ["time", "space"]
    },
    frames: {
      type: Type.ARRAY,
      items: {
        type: Type.OBJECT,
        properties: {
          step_id: { type: Type.INTEGER },
          commentary: { type: Type.STRING },
          state: {
            type: Type.OBJECT,
            properties: {
              visual_type: { type: Type.STRING, description: "One of: heap, array, map" },
              data_entries: {
                type: Type.ARRAY,
                description: "Array of named data structures",
                items: {
                  type: Type.OBJECT,
                  properties: {
                    name: { type: Type.STRING, description: "The variable name (e.g., 'max_heap', 'arr')" },
                    values: { type: Type.ARRAY, items: { type: Type.STRING }, description: "The contents of the structure as strings" }
                  },
                  required: ["name", "values"]
                }
              },
              highlights: { type: Type.ARRAY, items: { type: Type.STRING } }
            },
            required: ["visual_type", "data_entries", "highlights"]
          },
          quiz: {
            type: Type.OBJECT,
            properties: {
              question: { type: Type.STRING },
              options: { type: Type.ARRAY, items: { type: Type.STRING } },
              correct: { type: Type.INTEGER }
            },
            required: ["question", "options", "correct"]
          }
        },
        required: ["step_id", "commentary", "state"]
      }
    }
  },
  required: ["title", "strategy", "strategy_details", "complexity", "frames"]
};

export const generateAlgorithmTrace = async (
  problem: string,
  context: ContextOption[],
  modelName: ModelName = "gemini-2.5-flash",
  recommendedAlgorithm?: string
): Promise<TraceData> => {
  const apiKey = import.meta.env.VITE_API_KEY;

  console.log('🔑 [Cloud Trace] API Key check:', apiKey ? `Present (${apiKey.substring(0, 10)}...)` : 'MISSING');

  if (!apiKey || apiKey === "YOUR_API_KEY" || apiKey.length < 10) {
    console.warn("⚠️ Gemini API Key missing or invalid. Using Demo Trace.");
    return DEMO_TRACE;
  }

  const ai = new GoogleGenAI({ apiKey });

  const heuristicsAdvice = consultHeuristics(context);

  const algorithmRequirement = recommendedAlgorithm
    ? `MANDATORY: You MUST use the "${recommendedAlgorithm}" algorithm. This was recommended during the learning phase. Do NOT use a different algorithm.`
    : `Choose the most efficient algorithm based on the ENGINEERING HEURISTICS below.`;

  const systemInstruction = `
    You are the "AlgoInsight Engine". Generate an educational step-by-step algorithm execution trace.

    === ENGINEERING HEURISTICS (CRITICAL - FOLLOW THESE RULES) ===
    ${heuristicsAdvice}
    === END HEURISTICS ===

    ${algorithmRequirement}

    ALGORITHM SELECTION PRIORITY:
    1. If a specific algorithm is MANDATORY above, use it
    2. Otherwise, select based on ENGINEERING HEURISTICS rules above
    3. For "Low Memory" or "Embedded" constraints: MUST use O(1) space algorithms (Two Pointer, Sliding Window, Morris Traversal)
    4. For "Low Latency" constraints: MUST use O(log n) or O(1) lookup algorithms (Binary Search, Hash Map)
    5. NEVER use Backtracking for simple array/string problems unless explicitly needed for combinations/permutations

    REQUIREMENTS:
    1. ALGORITHM: ${recommendedAlgorithm ? `Use ${recommendedAlgorithm} as specified` : 'Choose based on heuristics above'}
    2. VISUALIZE: Create 10-15 frames showing actual state changes
    3. DATA: Represent variables in data_entries. Each entry has a 'name' and 'values' array
    4. HIGHLIGHTS: Reference entry names or specific indices (e.g., "arr", "arr[0]")
    5. QUIZZES: Include 5-7 interactive quizzes at key decision points

    QUIZ REQUIREMENTS:
    - Add quiz objects to frames at important steps (every 2-3 steps)
    - Quiz format: { "question": "...", "options": ["A", "B", "C"], "correct": 0 }
    - Quiz types: predictive ("What happens next?"), decision ("Should we swap?"), understanding ("Why does this work?")

    Provide high-quality strategy_details explaining WHY this algorithm works and rich commentary referencing actual input values.
  `;

  console.log(`🎬 [Cloud] Generating trace${recommendedAlgorithm ? ` with algorithm: ${recommendedAlgorithm}` : ''}...`);
  console.log(`📋 [Cloud] Heuristics applied:\n${heuristicsAdvice}`);

  try {
    const response = await ai.models.generateContent({
      model: modelName,
      contents: `Generate a high-fidelity visualization trace for: "${problem}".

Focus context: ${context.join(", ")}.
${recommendedAlgorithm ? `\nIMPORTANT: Use the ${recommendedAlgorithm} algorithm as recommended.` : ''}

Extract ACTUAL input values from the problem and use them in the visualization.`,
      config: {
        systemInstruction,
        responseMimeType: "application/json",
        responseSchema: traceSchema
      }
    });

    const text = response.text;
    if (!text) throw new Error("Empty response from AI engine");

    const raw = JSON.parse(text);

    // Helper to sanitize values
    const sanitizeValue = (val: any, depth = 0): any => {
      if (depth > 10) return '[Max Depth]';
      if (val === null || val === undefined) return null;
      if (typeof val === 'number') {
        if (!isFinite(val)) return String(val);
        return val;
      }
      if (typeof val === 'string' || typeof val === 'boolean') return val;
      if (Array.isArray(val)) {
        return val.map(v => sanitizeValue(v, depth + 1));
      }
      if (typeof val === 'object') {
        const sanitized: Record<string, any> = {};
        for (const key of Object.keys(val)) {
          sanitized[key] = sanitizeValue(val[key], depth + 1);
        }
        return sanitized;
      }
      return String(val);
    };

    const frames = (raw.frames || []).map((frame: any, idx: number) => {
      try {
        // Transform data_entries to data
        const { data_entries, ...stateRest } = frame.state || {};
        const transformedData = (data_entries || []).reduce((acc: any, curr: any) => {
          if (curr && curr.name) {
            acc[curr.name] = curr.values || [];
          }
          return acc;
        }, {});

        // Ensure required fields exist
        return {
          step_id: typeof frame.step_id === 'number' ? frame.step_id : idx,
          commentary: typeof frame.commentary === 'string' ? frame.commentary : `Step ${idx + 1}`,
          state: {
            visual_type: stateRest.visual_type || 'array',
            data: sanitizeValue(transformedData),
            highlights: Array.isArray(stateRest.highlights) ? stateRest.highlights : []
          },
          quiz: frame.quiz || null
        };
      } catch (err) {
        console.error(`[Cloud] Error processing frame ${idx}:`, err);
        return {
          step_id: idx,
          commentary: `Step ${idx + 1} (recovered)`,
          state: { visual_type: 'array', data: {}, highlights: [] },
          quiz: null
        };
      }
    });

    // Filter out completely broken frames
    const validFrames = frames.filter((f: any) => f && f.state && typeof f.state.data === 'object');

    if (validFrames.length === 0) {
      throw new Error("Cloud returned no valid frames");
    }

    return { ...raw, frames: validFrames } as TraceData;
  } catch (apiError: any) {
    console.error("Standalone Gemini Error:", apiError);
    return DEMO_TRACE;
  }
};

export const MOCK_TRACE: TraceData = {
  "title": "AlgoInsight Initialized",
  "strategy": "System Ready",
  "strategy_details": "Enter a problem in the sidebar to generate a custom step-by-step trace. The engine will synthesize a high-fidelity visual animation of the best algorithm for your constraints.",
  "complexity": {"time": "---", "space": "---"},
  "frames": [
    {
      "step_id": 0,
      "commentary": "### Standing By...\n\nEnter a problem (e.g. 'Sort an array' or 'BFS traversal') to begin. If the local engine is offline, the cloud synthesis engine will automatically take over.",
      "state": {
        "visual_type": "array",
        "data": { "status": ["R", "E", "A", "D", "Y"] },
        "highlights": ["status"]
      },
      "quiz": null
    }
  ]
};

const learningPhaseSchema = {
  type: Type.OBJECT,
  properties: {
    phases: {
      type: Type.ARRAY,
      items: {
        type: Type.OBJECT,
        properties: {
          phase: { type: Type.STRING, description: "Phase identifier: understand_problem, analyze_input, or explore_approaches" },
          phase_number: { type: Type.INTEGER },
          phase_title: { type: Type.STRING },
          content: {
            type: Type.OBJECT,
            properties: {
              problem_statement: { type: Type.STRING },
              breakdown: {
                type: Type.OBJECT,
                properties: {
                  objective: { type: Type.STRING, description: "Clear statement of what we're solving" },
                  input: { type: Type.STRING, description: "Description of input data" },
                  output: { type: Type.STRING, description: "Description of expected output" },
                  constraints: { type: Type.ARRAY, items: { type: Type.STRING } }
                },
                required: ["objective", "input", "output", "constraints"]
              },
              key_insights: { type: Type.ARRAY, items: { type: Type.STRING } },

              data_structure_type: { type: Type.STRING, description: "array|tree|graph|string|linked_list|etc" },
              sample_input: {
                type: Type.OBJECT,
                properties: {
                  visual_type: { type: Type.STRING, description: "array|tree|etc for visualization" },
                  values: { type: Type.ARRAY, items: { type: Type.STRING }, description: "Actual values from problem" },
                  display_format: { type: Type.STRING, description: "horizontal|vertical|tree" }
                },
                required: ["visual_type", "values", "display_format"]
              },
              properties: { type: Type.ARRAY, items: { type: Type.STRING }, description: "Properties discovered about input" },
              why_properties_matter: { type: Type.ARRAY, items: { type: Type.STRING }, description: "Why each property is important" },

              approaches: {
                type: Type.ARRAY,
                items: {
                  type: Type.OBJECT,
                  properties: {
                    name: { type: Type.STRING, description: "Algorithm name like Binary Search, Two Pointer, etc" },
                    description: { type: Type.STRING },
                    complexity: {
                      type: Type.OBJECT,
                      properties: {
                        time: { type: Type.STRING, description: "O(n), O(log n), etc" },
                        space: { type: Type.STRING, description: "O(1), O(n), etc" }
                      },
                      required: ["time", "space"]
                    },
                    meets_constraints: { type: Type.BOOLEAN, description: "Does this approach meet the problem constraints?" },
                    pros: { type: Type.ARRAY, items: { type: Type.STRING } },
                    cons: { type: Type.ARRAY, items: { type: Type.STRING } },
                    suitable_for: { type: Type.STRING, description: "When to use this approach" }
                  },
                  required: ["name", "description", "complexity", "meets_constraints", "pros", "cons"]
                }
              },
              recommended: {
                type: Type.OBJECT,
                properties: {
                  approach_name: { type: Type.STRING, description: "Must match one of the approach names" },
                  reason: { type: Type.STRING, description: "Why this is the best approach" },
                  key_insight: { type: Type.STRING, description: "The key insight that makes this work" }
                },
                required: ["approach_name", "reason", "key_insight"]
              }
            }
          }
        },
        required: ["phase", "phase_number", "phase_title", "content"]
      }
    }
  },
  required: ["phases"]
};

export const generateLearningPhases = async (
  problem: string,
  context: ContextOption[],
  modelName: ModelName = "gemini-2.5-flash"
): Promise<{ phases: any[], learning_mode: boolean }> => {
  const apiKey = import.meta.env.VITE_API_KEY;

  console.log('🔑 [Cloud] API Key check:', apiKey ? `Present (${apiKey.substring(0, 10)}...)` : 'MISSING');

  if (!apiKey || apiKey === "YOUR_API_KEY" || apiKey.length < 10) {
    console.warn("⚠️ Gemini API Key missing or invalid. Using mock learning phases.");
    return getMockLearningPhases(problem);
  }

  const ai = new GoogleGenAI({ apiKey });

  const constraintsText = context.length > 0 ? context.join(", ") : "None specified";
  const heuristicsAdvice = consultHeuristics(context);

  const systemInstruction = `
You are an expert DSA (Data Structures and Algorithms) teacher. Generate a 3-phase educational learning journey.

=== ENGINEERING HEURISTICS (MUST FOLLOW FOR ALGORITHM RECOMMENDATION) ===
${heuristicsAdvice}
=== END HEURISTICS ===

ALGORITHM SELECTION RULES (Phase 3 recommendation MUST follow these):
- For "Low Memory" or "Embedded System" constraints: MUST recommend O(1) space algorithms like Two Pointer, Sliding Window, Morris Traversal, In-place Sort
- For "Low Latency" constraints: MUST recommend O(log n) or O(1) lookup algorithms like Binary Search, Hash Map
- For "High Throughput" constraints: Prefer Hash Map, efficient sorting, Binary Search
- NEVER recommend Backtracking for simple array/string problems (only for combinations/permutations)
- NEVER recommend Brute Force as the final recommendation if better options exist

CRITICAL: Your output MUST follow this EXACT structure for each phase:

=== PHASE 1: "understand_problem" ===
{
  "phase": "understand_problem",
  "phase_number": 1,
  "phase_title": "Understanding the Problem",
  "content": {
    "problem_statement": "The original problem text",
    "breakdown": {
      "objective": "Clear statement of what we're solving",
      "input": "Description of input data",
      "output": "Description of expected output",
      "constraints": ["constraint 1", "constraint 2"]
    },
    "key_insights": ["insight 1", "insight 2", "insight 3"]
  }
}

=== PHASE 2: "analyze_input" ===
{
  "phase": "analyze_input",
  "phase_number": 2,
  "phase_title": "Analyzing Input Structure",
  "content": {
    "data_structure_type": "array|tree|graph|string|linked_list",
    "sample_input": {
      "visual_type": "array",
      "values": ["actual", "values", "from", "problem"],
      "display_format": "horizontal"
    },
    "properties": ["Property 1: description", "Property 2: description"],
    "why_properties_matter": ["Why property 1 matters", "Why property 2 matters"]
  }
}

=== PHASE 3: "explore_approaches" ===
{
  "phase": "explore_approaches",
  "phase_number": 3,
  "phase_title": "Exploring Possible Approaches",
  "content": {
    "approaches": [
      {
        "name": "Brute Force",
        "description": "Description of approach",
        "complexity": { "time": "O(n²)", "space": "O(1)" },
        "meets_constraints": false,
        "pros": ["pro 1", "pro 2"],
        "cons": ["con 1", "con 2"],
        "suitable_for": "Small datasets or learning"
      },
      {
        "name": "Hash Map",
        "description": "Optimized approach",
        "complexity": { "time": "O(n)", "space": "O(n)" },
        "meets_constraints": true,
        "pros": ["Fast lookup", "Simple implementation"],
        "cons": ["Extra memory"],
        "suitable_for": "Production use"
      }
    ],
    "recommended": {
      "approach_name": "Hash Map",
      "reason": "Meets all constraints with optimal time complexity",
      "key_insight": "The key insight that makes this algorithm work"
    }
  }
}

IMPORTANT RULES:
1. Use EXACT field names: "input" not "input_description", "name" not "approach_name" in approaches array
2. sample_input.values MUST be an array of strings, NOT an object
3. complexity MUST be a nested object with "time" and "space" keys
4. meets_constraints MUST be a boolean (true/false)
5. Extract ACTUAL values from the problem statement for sample_input.values
6. recommended.approach_name MUST match one of: Binary Search, Two Pointer, Sliding Window, Hash Map, Stack-Based, Morris Traversal, BFS, DFS, Dynamic Programming, Sorting, Heap, Greedy

System constraints to consider: ${constraintsText}
`;

  try {
    console.log('🎓 [Cloud] Generating learning phases with Gemini...');
    console.log(`📋 [Cloud] Constraints: ${constraintsText}`);
    console.log(`📋 [Cloud] Heuristics applied:\n${heuristicsAdvice}`);

    const response = await ai.models.generateContent({
      model: modelName,
      contents: `Generate a complete 3-phase learning journey for this DSA problem:

${problem}

SYSTEM CONSTRAINTS: ${constraintsText}

ENGINEERING RULES TO FOLLOW:
${heuristicsAdvice}

CRITICAL INSTRUCTIONS:
1. Extract ACTUAL input values from the problem (e.g., if problem says nums = [2,7,11,15], use those exact values)
2. In Phase 3, your "recommended" algorithm MUST follow the ENGINEERING RULES above
3. If constraints include "Low Memory" or "Embedded System" → recommend Two Pointer, Sliding Window, or Morris Traversal (O(1) space)
4. If constraints include "Low Latency" → recommend Binary Search or Hash Map (fast lookup)
5. NEVER recommend Backtracking for simple array/string traversal problems
6. Be educational and explain WHY each insight matters`,
      config: {
        systemInstruction,
        responseMimeType: "application/json",
        responseSchema: learningPhaseSchema
      }
    });

    const text = response.text;
    if (!text) throw new Error("Empty response from Gemini for learning phases");

    console.log('📥 [Cloud] Raw response length:', text.length);

    const data = JSON.parse(text);
    console.log(`✅ [Cloud] Generated ${data.phases?.length || 0} learning phases`);

    if (data.phases && data.phases.length > 0) {
      data.phases.forEach((phase: any, idx: number) => {
        console.log(`   Phase ${idx + 1}: ${phase.phase} - ${phase.phase_title}`);
        console.log(`   Content keys:`, Object.keys(phase.content || {}));

        // Log phase 1 details
        if (phase.phase === 'understand_problem') {
          console.log('   📋 Phase 1 breakdown:', phase.content?.breakdown ? 'EXISTS' : 'MISSING');
          console.log('   📋 Phase 1 key_insights:', phase.content?.key_insights?.length || 0, 'items');
        }

        // Log phase 2 details
        if (phase.phase === 'analyze_input') {
          console.log('   🔍 Phase 2 sample_input:', phase.content?.sample_input ? 'EXISTS' : 'MISSING');
          console.log('   🔍 Phase 2 properties:', phase.content?.properties?.length || 0, 'items');
        }

        // Log phase 3 details
        if (phase.phase === 'explore_approaches') {
          console.log('   💡 Phase 3 approaches:', phase.content?.approaches?.length || 0, 'approaches');
          console.log('   💡 Phase 3 recommended:', phase.content?.recommended?.approach_name || 'MISSING');
        }
      });
    } else {
      console.warn('⚠️ [Cloud] No phases in response:', JSON.stringify(data).substring(0, 200));
    }

    return {
      phases: data.phases || [],
      learning_mode: true
    };
  } catch (error: any) {
    console.error("❌ [Cloud] Learning phase generation failed:", error);
    return getMockLearningPhases(problem);
  }
};

const getMockLearningPhases = (problem: string): { phases: any[], learning_mode: boolean } => {
  return {
    learning_mode: true,
    phases: [
      {
        phase: "understand_problem",
        phase_number: 1,
        phase_title: "Understanding the Problem",
        content: {
          problem_statement: problem,
          breakdown: {
            objective: "Solve the given problem efficiently",
            input: "Input as specified in the problem",
            output: "Output as specified in the problem",
            constraints: ["Consider time complexity", "Consider space complexity"]
          },
          key_insights: [
            "Analyze the problem requirements carefully",
            "Consider edge cases",
            "Think about the most efficient approach"
          ]
        }
      },
      {
        phase: "analyze_input",
        phase_number: 2,
        phase_title: "Analyzing Input Structure",
        content: {
          data_structure_type: "array",
          sample_input: {
            visual_type: "array",
            values: ["sample", "data"],
            display_format: "horizontal"
          },
          properties: [
            "Property 1: Analyze the input structure",
            "Property 2: Identify patterns in the data"
          ],
          why_properties_matter: [
            "Understanding the structure helps choose the right algorithm",
            "Patterns reveal optimization opportunities"
          ]
        }
      },
      {
        phase: "explore_approaches",
        phase_number: 3,
        phase_title: "Exploring Possible Approaches",
        content: {
          approaches: [
            {
              name: "Brute Force",
              description: "Simple iteration through all possibilities",
              complexity: {
                time: "O(n²)",
                space: "O(1)"
              },
              meets_constraints: false,
              pros: ["Easy to implement", "Works for small inputs"],
              cons: ["Slow for large inputs"],
              suitable_for: "Small datasets or learning"
            },
            {
              name: "Hash Map",
              description: "Use hash map for O(1) lookups",
              complexity: {
                time: "O(n)",
                space: "O(n)"
              },
              meets_constraints: true,
              pros: ["Fast lookup", "Linear time complexity"],
              cons: ["Extra memory usage"],
              suitable_for: "Production use with moderate memory"
            }
          ],
          recommended: {
            approach_name: "Hash Map",
            reason: "Provides efficient O(1) lookup with good balance of time/space complexity",
            key_insight: "Trading space for time often leads to significant performance gains"
          }
        }
      }
    ]
  };
};
