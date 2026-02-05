
export interface Complexity {
  time: string;
  space: string;
}

export interface Quiz {
  question: string;
  options: string[];
  correct: number;
}

export interface State {
  visual_type: 'heap' | 'array' | 'list' | 'tree' | 'graph' | 'map' | 'matrix';
  data: Record<string, any>;
  highlights: string[];
}

export interface Frame {
  step_id: number;
  commentary: string;
  state: State;
  quiz: Quiz | null;
}

export interface TraceData {
  title: string;
  strategy: string;
  strategy_details?: string;
  complexity: Complexity;
  frames: Frame[];
  _meta?: {
    request_id?: string;
    provider_used?: string;
    model_used?: string;
    fallback?: boolean;
  };
}

export type ContextOption = 'Embedded System' | 'High Throughput' | 'Low Memory';

// LLM Provider types
export type LLMProvider = 'azure' | 'openai' | 'gemini';

export interface LLMConfig {
  provider: LLMProvider;
  model: string;
  apiKey: string;
  azureEndpoint?: string;
}

export interface ProviderInfo {
  name: string;
  models: string[];
  requires_endpoint: boolean;
  description: string;
}

export interface ProvidersResponse {
  providers: Record<LLMProvider, ProviderInfo>;
}
