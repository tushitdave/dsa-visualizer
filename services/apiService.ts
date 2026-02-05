
import { TraceData, ContextOption, LLMConfig, ProvidersResponse } from "../types";

// Environment-based API URL configuration for Vercel deployment
const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Get or create a unique session ID for this browser session.
 * Used for request correlation and credential management.
 */
const getSessionId = (): string => {
  let sessionId = sessionStorage.getItem('algoinsight_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    sessionStorage.setItem('algoinsight_session_id', sessionId);
  }
  return sessionId;
};

/**
 * Fetch available LLM providers and their models
 */
export const fetchProviders = async (): Promise<ProvidersResponse> => {
  try {
    const response = await fetch(`${API_BASE}/providers`, {
      headers: {
        'X-Session-ID': getSessionId(),
      },
    });
    if (!response.ok) {
      throw new Error("Failed to fetch providers");
    }
    return await response.json();
  } catch (err) {
    console.error("Failed to fetch providers:", err);
    // Return default providers if backend is offline
    return {
      providers: {
        azure: {
          name: 'Azure OpenAI',
          models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano'],
          requires_endpoint: true,
          description: 'Microsoft Azure hosted OpenAI models'
        },
        openai: {
          name: 'OpenAI',
          models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano'],
          requires_endpoint: false,
          description: 'OpenAI direct API'
        },
        gemini: {
          name: 'Google Gemini',
          models: ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-2.5-pro', 'gemini-3-flash', 'gemini-3-pro'],
          requires_endpoint: false,
          description: 'Google Gemini models'
        }
      }
    };
  }
};

/**
 * Validate LLM credentials
 */
export const validateCredentials = async (config: LLMConfig): Promise<{ valid: boolean; message: string }> => {
  try {
    const response = await fetch(`${API_BASE}/validate-credentials`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': getSessionId(),
      },
      body: JSON.stringify({
        provider: config.provider,
        model: config.model,
        api_key: config.apiKey,
        azure_endpoint: config.azureEndpoint
      })
    });

    return await response.json();
  } catch (err) {
    return { valid: false, message: "Failed to connect to backend" };
  }
};

/**
 * Analyze problem with backend pipeline
 */
export const analyzeProblemWithBackend = async (
  problem: string,
  context: ContextOption[],
  llmConfig?: LLMConfig,
  recommendedAlgorithm?: string
): Promise<TraceData> => {
  console.log(`[API] Analyzing with ${llmConfig?.provider || 'default'}/${llmConfig?.model || 'default'}`);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120000);

  try {
    const requestBody: any = {
      problem_text: problem,
      context_toggles: context,
      recommended_algorithm: recommendedAlgorithm || null
    };

    // Add LLM config if provided
    if (llmConfig) {
      requestBody.llm_config = {
        provider: llmConfig.provider,
        model: llmConfig.model,
        api_key: llmConfig.apiKey,
        azure_endpoint: llmConfig.azureEndpoint || null
      };
    }

    const response = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Session-ID': getSessionId(),
      },
      body: JSON.stringify(requestBody),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("[API] Backend Error:", errorText);
      throw new Error("Backend encountered an error during synthesis.");
    }

    const data = await response.json();

    // Log provider info from response
    if (data._meta) {
      console.log(`[API] Response from ${data._meta.provider_used}/${data._meta.model_used}`);
      console.log(`[API] Route path: ${data._meta.route_path || 'unknown'}`);
    }

    // Debug: Log raw frame data structure
    console.log(`[API] Received ${data.frames?.length || 0} frames`);
    if (data.frames && data.frames.length > 0) {
      console.log(`[API] First frame structure:`, JSON.stringify(data.frames[0], null, 2).slice(0, 500));
    }

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

    // Validate and transform frames
    const frames = (data.frames || []).map((frame: any, idx: number) => {
      try {
        // Transform data_entries format if present
        if (frame.state && frame.state.data_entries) {
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

        if (!frame.state) {
          frame.state = { visual_type: 'array', data: {}, highlights: [] };
        }

        if (!frame.state.data || typeof frame.state.data !== 'object') {
          frame.state.data = {};
        }

        if (!Array.isArray(frame.state.highlights)) {
          frame.state.highlights = [];
        }

        const validTypes = ['heap', 'array', 'list', 'tree', 'graph', 'map', 'matrix'];
        if (!frame.state.visual_type || !validTypes.includes(frame.state.visual_type)) {
          frame.state.visual_type = 'array';
        }

        frame.state.data = sanitizeValue(frame.state.data);

        // Ensure data is not empty - add fallback if needed
        if (Object.keys(frame.state.data).length === 0) {
          // Try to extract something from commentary for display
          const stepNum = frame.step_id ?? idx;
          frame.state.data = {
            'STEP': [stepNum + 1],
            'STATUS': ['Processing...']
          };
          console.warn(`[API] Frame ${idx} had empty data, added fallback`);
        }

        if (typeof frame.step_id !== 'number') {
          frame.step_id = idx;
        }

        if (typeof frame.commentary !== 'string') {
          frame.commentary = `Step ${idx + 1}`;
        }

        // QUIZ FIX: Ensure quiz has valid 'correct' field
        if (frame.quiz) {
          console.log(`[API] Frame ${idx} quiz before fix:`, {
            hasCorrect: 'correct' in frame.quiz,
            correctValue: frame.quiz.correct,
            correctType: typeof frame.quiz.correct,
            allKeys: Object.keys(frame.quiz)
          });

          if (frame.quiz.correct === undefined || frame.quiz.correct === null) {
            console.warn(`[API] Frame ${idx} quiz missing 'correct', setting to 0`);
            frame.quiz.correct = 0;
          } else {
            // Ensure it's a number
            frame.quiz.correct = Number(frame.quiz.correct);
            if (Number.isNaN(frame.quiz.correct)) {
              frame.quiz.correct = 0;
            }
          }

          console.log(`[API] Frame ${idx} quiz after fix: correct = ${frame.quiz.correct}`);
        }

        return frame;
      } catch (err) {
        console.error(`[API] Error processing frame ${idx}:`, err);
        return {
          step_id: idx,
          commentary: `Step ${idx + 1} (recovered)`,
          state: { visual_type: 'array', data: { 'STEP': [idx + 1], 'STATUS': ['Recovered'] }, highlights: [] },
          quiz: null
        };
      }
    });

    // Filter frames that have valid state with non-empty data
    const validFrames = frames.filter((f: any) =>
      f && f.state && f.state.data && Object.keys(f.state.data).length > 0
    );

    if (validFrames.length === 0) {
      throw new Error("Backend returned no valid frames.");
    }

    return { ...data, frames: validFrames };
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error("Backend timed out.");
    }
    throw err;
  }
};

/**
 * Learn problem with backend (educational flow)
 */
export const learnProblemWithBackend = async (
  problem: string,
  context: ContextOption[],
  llmConfig?: LLMConfig
): Promise<any> => {
  console.log(`[API] Learning with ${llmConfig?.provider || 'default'}/${llmConfig?.model || 'default'}`);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 180000);

  try {
    const requestBody: any = {
      problem_text: problem,
      context_toggles: context
    };

    // Add LLM config if provided
    if (llmConfig) {
      requestBody.llm_config = {
        provider: llmConfig.provider,
        model: llmConfig.model,
        api_key: llmConfig.apiKey,
        azure_endpoint: llmConfig.azureEndpoint || null
      };
    }

    const response = await fetch(`${API_BASE}/learn`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Session-ID': getSessionId(),
      },
      body: JSON.stringify(requestBody),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("[API] Learning Error:", errorText);
      throw new Error("Backend learning mode failed.");
    }

    const data = await response.json();

    if (data._meta) {
      console.log(`[API] Learning response from ${data._meta.provider_used}/${data._meta.model_used}`);
    }

    return data;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error("Learning mode timed out.");
    }
    throw err;
  }
};

/**
 * Store credentials securely on the backend (Phase 3: Secure Credential Management)
 */
export const storeSessionCredentials = async (config: LLMConfig): Promise<boolean> => {
  const sessionId = getSessionId();
  try {
    const response = await fetch(`${API_BASE}/session/store-credentials`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId,
      },
      body: JSON.stringify({
        session_id: sessionId,
        provider: config.provider,
        model: config.model,
        api_key: config.apiKey,
        azure_endpoint: config.azureEndpoint
      })
    });
    return response.ok;
  } catch {
    return false;
  }
};

/**
 * Check if session has stored credentials on the backend
 */
export const checkSessionCredentials = async (): Promise<{exists: boolean, provider?: string, model?: string}> => {
  const sessionId = getSessionId();
  try {
    const response = await fetch(`${API_BASE}/session/${sessionId}/credentials`, {
      headers: {
        'X-Session-ID': sessionId,
      },
    });
    return await response.json();
  } catch {
    return { exists: false };
  }
};

/**
 * Delete session credentials from backend
 */
export const deleteSessionCredentials = async (): Promise<boolean> => {
  const sessionId = getSessionId();
  try {
    const response = await fetch(`${API_BASE}/session/${sessionId}`, {
      method: 'DELETE',
      headers: {
        'X-Session-ID': sessionId,
      },
    });
    return response.ok;
  } catch {
    return false;
  }
};

/**
 * Export session ID getter for use in other components
 */
export { getSessionId };
