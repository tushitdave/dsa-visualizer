
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
}

export type ContextOption = 'Embedded System' | 'High Throughput' | 'Low Memory';

export type ModelName = 'gemini-2.5-flash' | 'gemini-2.5-pro' | 'gemini-2.5-flash-lite-latest';
