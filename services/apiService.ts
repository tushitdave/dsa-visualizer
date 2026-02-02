
import { TraceData, ContextOption } from "../types";

const API_BASE = "http://localhost:8000";

export const analyzeProblemWithBackend = async (
  problem: string,
  context: ContextOption[],
  recommendedAlgorithm?: string
): Promise<TraceData> => {
  console.log(`📡 [Core] Attempting Local Python Engine at ${API_BASE}...`);

  if (recommendedAlgorithm) {
    console.log(`🎯 [Core] Using recommended algorithm: ${recommendedAlgorithm}`);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120000);

  try {
    const response = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        problem_text: problem,
        context_toggles: context,
        recommended_algorithm: recommendedAlgorithm || null
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("❌ [Backend] Logic Error:", errorText);
      throw new Error("Backend encountered an error during synthesis.");
    }

    const data = await response.json();

    console.log('🔍 [Backend Response] Raw data received:', {
      title: data.title,
      frameCount: data.frames?.length,
      firstFrameStructure: data.frames?.[0]?.state
    });

    // Helper to sanitize values that could crash React
    const sanitizeValue = (val: any, depth = 0): any => {
      if (depth > 10) return '[Max Depth]'; // Prevent infinite recursion
      if (val === null || val === undefined) return null;
      if (typeof val === 'number') {
        if (!isFinite(val)) return String(val); // Handle Infinity, -Infinity, NaN
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
      return String(val); // Convert any other type to string
    };

    // Validate and transform frames
    const frames = (data.frames || []).map((frame: any, idx: number) => {
      try {
        // Transform data_entries format if present
        if (frame.state && frame.state.data_entries) {
          console.log('✅ [Transform] Converting data_entries to flat data format');
          const { data_entries, ...stateRest } = frame.state;
          frame = {
            ...frame,
            state: {
              ...stateRest,
              data: data_entries.reduce((acc: any, curr: any) => {
                acc[curr.name] = curr.values;
                return acc;
              }, {})
            }
          };
        }

        // Ensure frame has required structure
        if (!frame.state) {
          console.warn(`⚠️ [Frame ${idx}] Missing state, creating default`);
          frame.state = { visual_type: 'array', data: {}, highlights: [] };
        }

        // Ensure state has data object
        if (!frame.state.data || typeof frame.state.data !== 'object') {
          console.warn(`⚠️ [Frame ${idx}] Invalid state.data, creating default`);
          frame.state.data = {};
        }

        // Ensure highlights is an array
        if (!Array.isArray(frame.state.highlights)) {
          frame.state.highlights = [];
        }

        // Ensure visual_type is valid
        const validTypes = ['heap', 'array', 'list', 'tree', 'graph', 'map', 'matrix'];
        if (!frame.state.visual_type || !validTypes.includes(frame.state.visual_type)) {
          frame.state.visual_type = 'array';
        }

        // Sanitize all data values to prevent render crashes
        frame.state.data = sanitizeValue(frame.state.data);

        // Ensure step_id exists
        if (typeof frame.step_id !== 'number') {
          frame.step_id = idx;
        }

        // Ensure commentary exists
        if (typeof frame.commentary !== 'string') {
          frame.commentary = `Step ${idx + 1}`;
        }

        return frame;
      } catch (err) {
        console.error(`❌ [Frame ${idx}] Error processing frame:`, err);
        // Return a safe fallback frame
        return {
          step_id: idx,
          commentary: `Step ${idx + 1} (recovered)`,
          state: { visual_type: 'array', data: {}, highlights: [] },
          quiz: null
        };
      }
    });

    // Filter out completely broken frames
    const validFrames = frames.filter((f: any) => f && f.state && f.state.data);

    if (validFrames.length === 0) {
      throw new Error("Backend returned no valid frames.");
    }

    console.log('✅ [Backend Response] Transformed data:', {
      title: data.title,
      frameCount: validFrames.length,
      firstFrameData: validFrames[0]?.state?.data
    });

    return { ...data, frames: validFrames };
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error("Backend timed out. Switching to Standalone Mode.");
    }
    throw err;
  }
};

export const learnProblemWithBackend = async (
  problem: string,
  context: ContextOption[]
): Promise<any> => {
  console.log(`🎓 [Learning Mode] Requesting educational flow from ${API_BASE}...`);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 180000);

  try {
    const response = await fetch(`${API_BASE}/learn`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        problem_text: problem,
        context_toggles: context
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("❌ [Learning Backend] Error:", errorText);
      throw new Error("Backend learning mode failed.");
    }

    const data = await response.json();

    console.log('✅ [Learning Response] Phases received:', {
      total_phases: data.total_phases,
      phases: data.phases?.map((p: any) => p.phase_title)
    });

    return data;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error("Learning mode timed out.");
    }
    throw err;
  }
};
