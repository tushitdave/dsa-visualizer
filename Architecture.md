# AlgoInsight - Complete System Architecture

> A comprehensive guide to understanding AlgoInsight's architecture, design decisions, and implementation details. This document is designed to help you understand the system deeply and prepare for technical interviews.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Backend Architecture](#4-backend-architecture)
5. [Multi-User Session Management](#5-multi-user-session-management)
6. [Request Flow Diagrams](#6-request-flow-diagrams)
7. [Data Flow & State Management](#7-data-flow--state-management)
8. [Security Architecture](#8-security-architecture)
9. [Caching Strategy](#9-caching-strategy)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Interview Q&A](#11-interview-qa)

---

## 1. Executive Summary

### What is AlgoInsight?

AlgoInsight is an AI-powered educational platform that helps users understand Data Structures and Algorithms (DSA) through:
- **Visual Step-by-Step Execution**: Animated algorithm traces
- **Interactive Learning Mode**: Guided educational flow with quizzes
- **Multi-Provider LLM Support**: Azure OpenAI, OpenAI, Google Gemini
- **Context-Aware Optimization**: Adapts solutions for embedded systems, high throughput, or low memory constraints

### Why was it built this way?

| Design Goal | Solution | Reason |
|-------------|----------|--------|
| **Scalability** | Stateless backend with session tracking | Supports multiple concurrent users without shared mutable state |
| **Flexibility** | Multi-provider LLM support | Users can choose their preferred AI provider |
| **Security** | Encrypted credential storage | Protects API keys at rest |
| **Performance** | Multi-layer caching | Reduces LLM API calls and response latency |
| **User Experience** | Learning + Quick modes | Accommodates different learning styles |

### Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  React 18 + TypeScript + Vite + TailwindCSS                     │
│  State: React useState/useEffect (no Redux needed)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS (REST API)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND                                   │
│  Python 3.11 + FastAPI + Uvicorn                                │
│  LLM: OpenAI SDK + Google GenAI SDK                             │
│  Storage: SQLite (credentials) + JSON (cache)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS (Provider APIs)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LLM PROVIDERS                                │
│  Azure OpenAI  │  OpenAI Direct  │  Google Gemini               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. High-Level Architecture

### System Components

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              USER BROWSER                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         React Frontend                                │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Sidebar   │  │  MainPanel  │  │ Visualizer  │  │  Learning   │  │  │
│  │  │  - Problem  │  │  - Tabs     │  │  - Frames   │  │    Mode     │  │  │
│  │  │  - Config   │  │  - Controls │  │  - Animation│  │  - Phases   │  │  │
│  │  │  - Provider │  │  - Progress │  │  - Quiz     │  │  - Quiz     │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │                      apiService.ts                               │ │  │
│  │  │  - Session ID Management (sessionStorage)                        │ │  │
│  │  │  - API Calls with X-Session-ID header                           │ │  │
│  │  │  - Credential Management                                         │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTPS + X-Session-ID Header
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI Backend                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         API Layer (main.py)                           │  │
│  │  POST /analyze    POST /learn    POST /validate-credentials           │  │
│  │  POST /session/*  GET /providers GET /router/*                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────┐  │
│  │  RequestContext   │  │  CredentialStore  │  │    Smart Router       │  │
│  │  - request_id     │  │  - SQLite + Fernet│  │  - Pattern Matching   │  │
│  │  - session_id     │  │  - Encrypt/Decrypt│  │  - Algorithm Library  │  │
│  │  - provider/model │  │  - TTL Expiration │  │  - Cache Integration  │  │
│  └───────────────────┘  └───────────────────┘  └───────────────────────┘  │
│                                      │                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      5-Agent Pipeline                                 │  │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌────────┐ ┌────────────┐  │  │
│  │  │Normalizer│→│Strategist│→│Instrumenter│→│ Tracer │→│  Narrator  │  │  │
│  │  │Parse     │ │Select    │ │Add Logging │ │Execute │ │Generate    │  │  │
│  │  │Problem   │ │Algorithm │ │to Code     │ │& Trace │ │Commentary  │  │  │
│  │  └──────────┘ └──────────┘ └────────────┘ └────────┘ └────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      LLM Provider Factory                             │  │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐ │  │
│  │  │  AzureProvider  │ │  OpenAIProvider │ │    GeminiProvider       │ │  │
│  │  │  - gpt-4o       │ │  - gpt-4o       │ │  - gemini-2.5-flash     │ │  │
│  │  │  - gpt-4o-mini  │ │  - gpt-4o-mini  │ │  - gemini-2.5-pro       │ │  │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Cache Manager                                  │  │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐ │  │
│  │  │  Memory Cache   │ │   File Cache    │ │   Algorithm Library     │ │  │
│  │  │  (RLock-safe)   │ │  (JSON files)   │ │   (Pre-computed)        │ │  │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | What | Why | Where |
|-----------|------|-----|-------|
| **Sidebar** | Problem input, LLM config, mode selection | Central control panel for user | `components/Sidebar.tsx` |
| **MainPanel** | Visualization display, playback controls | Shows algorithm execution | `components/MainPanel.tsx` |
| **apiService** | API communication, session management | Abstracts backend communication | `services/apiService.ts` |
| **RequestContext** | Request isolation, credential routing | Ensures multi-user safety | `backend/app/utils/request_context.py` |
| **Pipeline** | Orchestrates 5-agent workflow | Coordinates LLM agents | `backend/app/pipeline.py` |
| **CredentialStore** | Encrypted credential storage | Secure API key management | `backend/app/utils/credential_store.py` |
| **CacheManager** | Multi-layer caching | Performance optimization | `backend/app/cache.py` |

---

## 3. Frontend Architecture

### Component Hierarchy

```
App.tsx
├── Sidebar.tsx
│   ├── LLM Configuration Panel
│   │   ├── Provider Selection (Azure/OpenAI/Gemini)
│   │   ├── Model Selection
│   │   ├── API Key Input
│   │   └── Validate Button
│   ├── Experience Mode Toggle (Learning/Quick)
│   ├── Problem Input Textarea
│   ├── Contextual Toggles
│   │   ├── Embedded System
│   │   ├── High Throughput
│   │   └── Low Memory
│   └── Analyze Button
│
├── MainPanel.tsx
│   ├── Tab Navigation
│   │   ├── Visualizer Tab
│   │   ├── Algorithm Deep Dive Tab
│   │   └── Code Tab
│   ├── PlaybackControls.tsx
│   │   ├── Play/Pause
│   │   ├── Step Forward/Back
│   │   ├── Speed Control
│   │   └── Progress Bar
│   └── Content Area
│       ├── Visualizer.tsx (frames rendering)
│       ├── AlgorithmDeepDive.tsx
│       └── CodeDisplay.tsx
│
└── LearningMode.tsx (when learning mode active)
    ├── Phase Navigation
    ├── Phase Content
    │   ├── Problem Understanding
    │   ├── Pattern Recognition
    │   ├── Strategy Selection
    │   ├── Implementation
    │   └── Optimization
    └── Interactive Quizzes
```

### State Management Strategy

```typescript
// App.tsx - Main State
const [traceData, setTraceData] = useState<TraceData | null>(null);
const [isLoading, setIsLoading] = useState(false);
const [learningMode, setLearningMode] = useState(true);
const [isBackendOnline, setIsBackendOnline] = useState(false);

// Sidebar.tsx - Configuration State
const [selectedProvider, setSelectedProvider] = useState<LLMProvider>('azure');
const [selectedModel, setSelectedModel] = useState<string>('gpt-4o');
const [apiKey, setApiKey] = useState<string>('');
const [validationStatus, setValidationStatus] = useState<'idle'|'valid'|'invalid'>('idle');

// MainPanel.tsx - Playback State
const [currentFrame, setCurrentFrame] = useState(0);
const [isPlaying, setIsPlaying] = useState(false);
const [playbackSpeed, setPlaybackSpeed] = useState(1);
```

**Why no Redux/Zustand?**
- App complexity is moderate
- State is localized to specific components
- Prop drilling is minimal (max 2-3 levels)
- React's useState + Context is sufficient

### Session ID Management

```typescript
// services/apiService.ts

const getSessionId = (): string => {
  // Check sessionStorage first (persists across page refreshes, cleared on tab close)
  let sessionId = sessionStorage.getItem('algoinsight_session_id');

  if (!sessionId) {
    // Generate new UUID v4
    sessionId = crypto.randomUUID();
    sessionStorage.setItem('algoinsight_session_id', sessionId);
  }

  return sessionId;
};

// All API calls include this header
headers: {
  'Content-Type': 'application/json',
  'X-Session-ID': getSessionId(),  // <-- Session correlation
}
```

**Why sessionStorage over localStorage?**
| Storage | Lifetime | Sharing | Use Case |
|---------|----------|---------|----------|
| sessionStorage | Tab lifetime | Not shared between tabs | Session ID (each tab = new session) |
| localStorage | Permanent | Shared between tabs | User preferences, cached config |

---

## 4. Backend Architecture

### Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application, endpoints
│   ├── pipeline.py             # 5-agent orchestration
│   ├── cache.py                # Cache manager
│   │
│   ├── agents/                 # LLM-powered agents
│   │   ├── normalizer.py       # Problem parsing
│   │   ├── strategist.py       # Algorithm selection
│   │   ├── instrumenter.py     # Code instrumentation
│   │   ├── tracer.py           # Execution tracing
│   │   ├── narrator.py         # Commentary generation
│   │   └── educational_flow_generator.py
│   │
│   ├── utils/
│   │   ├── request_context.py  # Request isolation
│   │   ├── credential_store.py # Encrypted storage
│   │   ├── logger.py           # Logging utilities
│   │   └── providers/          # LLM provider implementations
│   │       ├── factory.py
│   │       ├── base.py
│   │       ├── azure.py
│   │       ├── openai_provider.py
│   │       └── gemini.py
│   │
│   └── router/
│       └── smart_router.py     # Algorithm routing & caching
│
├── data/
│   ├── sessions.db             # SQLite credential store
│   └── cache/                  # File-based cache
│
├── requirements.txt
└── .env
```

### Request Context Pattern

```python
@dataclass
class RequestContext:
    """
    Immutable context carrying request-specific configuration.
    Created fresh for each API request - ensures isolation.
    """
    request_id: str      # Unique per request (for logging)
    session_id: str      # From X-Session-ID header (for correlation)
    provider: str        # 'azure' | 'openai' | 'gemini'
    model: str           # 'gpt-4o', 'gemini-2.5-flash', etc.
    api_key: str         # User's API key
    azure_endpoint: str  # Azure-specific endpoint URL
```

**Why RequestContext?**
```
Problem: Multiple users making concurrent requests
         User A wants Azure GPT-4o
         User B wants Gemini Flash

Without RequestContext:
  ┌─────────────────────────────────────┐
  │  Global provider = AzureProvider()  │  <-- User B's request uses
  │  Global model = "gpt-4o"            │      wrong provider!
  └─────────────────────────────────────┘

With RequestContext:
  Request A                    Request B
  ┌─────────────────┐         ┌─────────────────┐
  │ context_a:      │         │ context_b:      │
  │  provider=azure │         │  provider=gemini│
  │  model=gpt-4o   │         │  model=flash    │
  │  api_key=xxx    │         │  api_key=yyy    │
  └─────────────────┘         └─────────────────┘
         │                           │
         ▼                           ▼
  AzureProvider(context_a)    GeminiProvider(context_b)
```

### 5-Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE FLOW                                      │
│                                                                              │
│  Input: "Find the longest palindromic substring in a string"                │
│                                                                              │
│  ┌──────────────┐                                                           │
│  │  NORMALIZER  │  What: Parse and normalize problem statement              │
│  │              │  Why: Standardize input for downstream agents             │
│  │              │  Output: {                                                │
│  │              │    problem_type: "string_manipulation",                   │
│  │              │    input_format: "string s",                              │
│  │              │    output_format: "string (longest palindrome)",          │
│  │              │    constraints: ["1 <= s.length <= 1000"]                 │
│  │              │  }                                                        │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐                                                           │
│  │  STRATEGIST  │  What: Select optimal algorithm                           │
│  │              │  Why: Match problem to best-fit solution                  │
│  │              │  Considers: Context toggles (embedded, memory, throughput)│
│  │              │  Output: {                                                │
│  │              │    algorithm: "Expand Around Center",                     │
│  │              │    complexity: { time: "O(n²)", space: "O(1)" },         │
│  │              │    rationale: "Optimal for space-constrained env"        │
│  │              │  }                                                        │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐                                                           │
│  │ INSTRUMENTER │  What: Generate code with tracing hooks                   │
│  │              │  Why: Enable step-by-step visualization                   │
│  │              │  Output: Python code with trace_step() calls              │
│  │              │                                                           │
│  │              │  def longest_palindrome(s):                               │
│  │              │      trace_step("Initialize", {"s": s})                   │
│  │              │      for i in range(len(s)):                              │
│  │              │          trace_step("Check center", {"i": i})             │
│  │              │          ...                                              │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐                                                           │
│  │    TRACER    │  What: Execute code, capture state at each step           │
│  │              │  Why: Generate visualization frames                       │
│  │              │  Output: [                                                │
│  │              │    { step: 0, state: {...}, variables: {...} },          │
│  │              │    { step: 1, state: {...}, variables: {...} },          │
│  │              │    ...                                                    │
│  │              │  ]                                                        │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐                                                           │
│  │   NARRATOR   │  What: Generate human-readable commentary                 │
│  │              │  Why: Educational explanations for each step              │
│  │              │  Output: Frames with commentary + optional quizzes        │
│  │              │                                                           │
│  │              │  { step: 0,                                               │
│  │              │    commentary: "We start by examining each character...", │
│  │              │    quiz: { question: "Why O(1) space?", ... }            │
│  │              │  }                                                        │
│  └──────────────┘                                                           │
│                                                                              │
│  Final Output: TraceData with frames, strategy, complexity, metadata        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### LLM Provider Factory Pattern

```python
# Factory Pattern for LLM Provider Creation

class LLMProviderFactory:
    @staticmethod
    def create_from_context(context: RequestContext) -> BaseLLMProvider:
        """
        Factory method - creates appropriate provider based on context.

        Why Factory Pattern?
        - Decouples provider creation from usage
        - Easy to add new providers
        - Centralizes provider configuration
        """
        providers = {
            'azure': AzureOpenAIProvider,
            'openai': OpenAIProvider,
            'gemini': GeminiProvider,
        }

        provider_class = providers.get(context.provider)
        if not provider_class:
            raise ValueError(f"Unknown provider: {context.provider}")

        return provider_class(
            api_key=context.api_key,
            model=context.model,
            endpoint=context.azure_endpoint  # Only used by Azure
        )
```

---

## 5. Multi-User Session Management

### Session Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SESSION LIFECYCLE                                     │
│                                                                              │
│  1. USER OPENS APP                                                          │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  Browser Tab Opens                                               │     │
│     │  sessionStorage.getItem('algoinsight_session_id') → null        │     │
│     │  crypto.randomUUID() → "a1b2c3d4-e5f6-..."                      │     │
│     │  sessionStorage.setItem('algoinsight_session_id', uuid)         │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                      │                                       │
│  2. USER VALIDATES CREDENTIALS                                              │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  POST /validate-credentials                                      │     │
│     │  Headers: { X-Session-ID: "a1b2c3d4-e5f6-..." }                 │     │
│     │  Body: { provider, model, api_key }                             │     │
│     │                                                                  │     │
│     │  → Backend validates with LLM provider                          │     │
│     │  → Returns { valid: true }                                      │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                      │                                       │
│  3. CREDENTIALS STORED ON BACKEND                                           │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  POST /session/store-credentials                                 │     │
│     │  Body: { session_id, provider, model, api_key }                 │     │
│     │                                                                  │     │
│     │  → Encrypt API key with Fernet                                  │     │
│     │  → Store in SQLite: sessions.db                                 │     │
│     │  → Set TTL: 24 hours                                            │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                      │                                       │
│  4. USER MAKES ANALYSIS REQUEST                                             │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  POST /analyze                                                   │     │
│     │  Headers: { X-Session-ID: "a1b2c3d4-e5f6-..." }                 │     │
│     │  Body: { problem_text, context_toggles, llm_config? }           │     │
│     │                                                                  │     │
│     │  Backend Resolution Order:                                       │     │
│     │  1. llm_config in request body? → Use it                        │     │
│     │  2. Stored credentials for session? → Decrypt and use           │     │
│     │  3. Environment variables? → Use as fallback                    │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                      │                                       │
│  5. SESSION ENDS                                                            │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  User closes browser tab                                         │     │
│     │  → sessionStorage cleared automatically                          │     │
│     │  → Backend credentials expire after 24h (TTL)                   │     │
│     │  → Cleanup job removes expired sessions                         │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Concurrent Users Isolation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CONCURRENT REQUEST HANDLING                              │
│                                                                              │
│  Time ──────────────────────────────────────────────────────────────────►   │
│                                                                              │
│  User A (Session: abc123)           User B (Session: xyz789)                │
│  Azure GPT-4o                       Gemini Flash                            │
│       │                                  │                                   │
│       │ POST /analyze                    │ POST /analyze                    │
│       │ X-Session-ID: abc123             │ X-Session-ID: xyz789             │
│       ▼                                  ▼                                   │
│  ┌─────────────────┐              ┌─────────────────┐                       │
│  │ RequestContext  │              │ RequestContext  │                       │
│  │ request_id: r1  │              │ request_id: r2  │                       │
│  │ session: abc123 │              │ session: xyz789 │                       │
│  │ provider: azure │              │ provider: gemini│                       │
│  └────────┬────────┘              └────────┬────────┘                       │
│           │                                │                                 │
│           ▼                                ▼                                 │
│  ┌─────────────────┐              ┌─────────────────┐                       │
│  │ Pipeline(ctx_A) │              │ Pipeline(ctx_B) │                       │
│  │ Uses Azure API  │              │ Uses Gemini API │                       │
│  └────────┬────────┘              └────────┬────────┘                       │
│           │                                │                                 │
│           ▼                                ▼                                 │
│  Response to User A               Response to User B                        │
│  (Azure-generated)                (Gemini-generated)                        │
│                                                                              │
│  KEY INSIGHT: No shared mutable state between requests!                     │
│  - Each request creates new RequestContext                                  │
│  - Each Pipeline instance is isolated                                       │
│  - Cache is intentionally shared (same problem = same answer)              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Credential Storage Security

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CREDENTIAL ENCRYPTION FLOW                               │
│                                                                              │
│  1. STORAGE                                                                 │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  Input: api_key = "sk-abc123xyz..."                             │     │
│     │                                                                  │     │
│     │  Fernet Key (from env): CREDENTIAL_ENCRYPTION_KEY               │     │
│     │  fernet = Fernet(key)                                           │     │
│     │                                                                  │     │
│     │  encrypted = fernet.encrypt(api_key.encode())                   │     │
│     │  → b'gAAAAABl...' (base64-encoded ciphertext)                   │     │
│     │                                                                  │     │
│     │  SQLite INSERT:                                                  │     │
│     │  | session_id | provider | model | encrypted_api_key | expires |│     │
│     │  | abc123...  | azure    | gpt-4o| gAAAAABl...       | 172800  |│     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  2. RETRIEVAL                                                               │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  SQLite SELECT WHERE session_id = 'abc123...'                   │     │
│     │                                                                  │     │
│     │  Check expiration: now < expires_at? ✓                          │     │
│     │                                                                  │     │
│     │  api_key = fernet.decrypt(encrypted_api_key).decode()           │     │
│     │  → "sk-abc123xyz..."                                            │     │
│     │                                                                  │     │
│     │  Return to RequestContext (never sent to frontend)              │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  Security Properties:                                                       │
│  ✓ API keys encrypted at rest (AES-128 via Fernet)                         │
│  ✓ Encryption key stored in environment (not in code/DB)                   │
│  ✓ Automatic expiration (24-hour TTL)                                      │
│  ✓ Keys never returned to frontend after storage                           │
│  ✓ Graceful degradation if cryptography not installed                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Request Flow Diagrams

### Analysis Request Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COMPLETE ANALYSIS REQUEST FLOW                          │
│                                                                              │
│  ┌──────────┐                                                               │
│  │  User    │                                                               │
│  │  Browser │                                                               │
│  └────┬─────┘                                                               │
│       │                                                                      │
│       │ 1. Click "ANALYZE & VISUALIZE"                                      │
│       ▼                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │  Sidebar.tsx::handleAnalyze()                                     │       │
│  │                                                                    │       │
│  │  const llmConfig = {                                              │       │
│  │    provider: selectedProvider,                                    │       │
│  │    model: selectedModel,                                          │       │
│  │    apiKey: apiKey,                                                │       │
│  │    azureEndpoint: azureEndpoint                                   │       │
│  │  };                                                               │       │
│  │                                                                    │       │
│  │  onAnalyze(problem, contexts, learningMode, llmConfig);           │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│       │                                                                      │
│       │ 2. Props callback to App.tsx                                        │
│       ▼                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │  App.tsx::handleAnalyze()                                         │       │
│  │                                                                    │       │
│  │  setIsLoading(true);                                              │       │
│  │                                                                    │       │
│  │  if (learningMode) {                                              │       │
│  │    result = await learnProblemWithBackend(problem, ctx, config);  │       │
│  │  } else {                                                         │       │
│  │    result = await analyzeProblemWithBackend(problem, ctx, config);│       │
│  │  }                                                                │       │
│  │                                                                    │       │
│  │  setTraceData(result);                                            │       │
│  │  setIsLoading(false);                                             │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│       │                                                                      │
│       │ 3. API Service Call                                                 │
│       ▼                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │  apiService.ts::analyzeProblemWithBackend()                       │       │
│  │                                                                    │       │
│  │  const sessionId = getSessionId();  // From sessionStorage        │       │
│  │                                                                    │       │
│  │  fetch(`${API_BASE}/analyze`, {                                   │       │
│  │    method: 'POST',                                                │       │
│  │    headers: {                                                     │       │
│  │      'Content-Type': 'application/json',                          │       │
│  │      'X-Session-ID': sessionId,  // <-- Session correlation       │       │
│  │    },                                                             │       │
│  │    body: JSON.stringify({                                         │       │
│  │      problem_text: problem,                                       │       │
│  │      context_toggles: context,                                    │       │
│  │      llm_config: { provider, model, api_key, azure_endpoint }    │       │
│  │    })                                                             │       │
│  │  });                                                              │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│       │                                                                      │
│       │ 4. HTTP Request                                                     │
│       ▼                                                                      │
│  ═══════════════════════════════════════════════════════════════════════    │
│                            NETWORK BOUNDARY                                  │
│  ═══════════════════════════════════════════════════════════════════════    │
│       │                                                                      │
│       ▼                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │  main.py::analyze_algorithm()                                     │       │
│  │                                                                    │       │
│  │  # Extract session from header                                    │       │
│  │  session_id = req.headers.get("X-Session-ID", "anonymous")        │       │
│  │                                                                    │       │
│  │  # Credential Resolution (Priority Order)                         │       │
│  │  if request.llm_config and request.llm_config.api_key:           │       │
│  │      context = RequestContext.from_request(llm_config, session_id)│       │
│  │  elif session_id != "anonymous":                                  │       │
│  │      stored = credential_store.get_credentials(session_id)        │       │
│  │      if stored:                                                   │       │
│  │          context = RequestContext.from_request(stored, session_id)│       │
│  │      else:                                                        │       │
│  │          context = RequestContext.from_env(session_id)            │       │
│  │  else:                                                            │       │
│  │      context = RequestContext.from_env(session_id)                │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│       │                                                                      │
│       │ 5. Pipeline Execution                                               │
│       ▼                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │  Pipeline(context).run_analysis()                                 │       │
│  │                                                                    │       │
│  │  # Check cache first                                              │       │
│  │  cache_key = hash(problem_text + context_toggles)                 │       │
│  │  if cache.has(cache_key):                                         │       │
│  │      return cache.get(cache_key)  # <100ms response               │       │
│  │                                                                    │       │
│  │  # Run 5-agent pipeline                                           │       │
│  │  normalized = await normalizer.run(problem_text)                  │       │
│  │  strategy = await strategist.run(normalized, context_toggles)     │       │
│  │  code = await instrumenter.run(strategy)                          │       │
│  │  traces = await tracer.run(code)                                  │       │
│  │  frames = await narrator.run(traces)                              │       │
│  │                                                                    │       │
│  │  # Cache result                                                   │       │
│  │  cache.set(cache_key, frames)                                     │       │
│  │                                                                    │       │
│  │  return { frames, strategy, complexity, _meta }                   │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│       │                                                                      │
│       │ 6. Response                                                         │
│       ▼                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │  JSON Response:                                                   │       │
│  │  {                                                                │       │
│  │    "title": "Longest Palindromic Substring",                     │       │
│  │    "strategy": "Expand Around Center",                           │       │
│  │    "complexity": { "time": "O(n²)", "space": "O(1)" },          │       │
│  │    "frames": [                                                    │       │
│  │      { "step_id": 0, "commentary": "...", "state": {...} },      │       │
│  │      { "step_id": 1, "commentary": "...", "state": {...} },      │       │
│  │      ...                                                          │       │
│  │    ],                                                             │       │
│  │    "_meta": {                                                     │       │
│  │      "request_id": "a1b2c3d4",                                   │       │
│  │      "session_id": "abc123...",                                  │       │
│  │      "provider_used": "azure",                                   │       │
│  │      "model_used": "gpt-4o"                                      │       │
│  │    }                                                              │       │
│  │  }                                                                │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│       │                                                                      │
│       │ 7. Render Visualization                                             │
│       ▼                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │  MainPanel.tsx                                                    │       │
│  │                                                                    │       │
│  │  - Render frames as visualizations                                │       │
│  │  - Enable playback controls                                       │       │
│  │  - Display commentary                                             │       │
│  │  - Show quizzes (if learning mode)                               │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Credential Validation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CREDENTIAL VALIDATION FLOW                                │
│                                                                              │
│  User clicks "Validate"                                                     │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  1. Frontend: Sidebar.tsx::handleValidate()                      │        │
│  │     POST /validate-credentials                                   │        │
│  │     { provider: "azure", model: "gpt-4o", api_key: "xxx" }      │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  2. Backend: main.py::validate_credentials()                     │        │
│  │     - Create temporary RequestContext                            │        │
│  │     - Instantiate provider via Factory                           │        │
│  │     - Call provider.validate_credentials()                       │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  3. Provider: AzureProvider.validate_credentials()               │        │
│  │     - Make minimal API call (list models or simple completion)   │        │
│  │     - Return True if successful, False if auth error             │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  4. Response: { valid: true, message: "Credentials validated" }  │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  5. Frontend: If valid, store on backend                         │        │
│  │     POST /session/store-credentials                              │        │
│  │     { session_id, provider, model, api_key }                    │        │
│  │                                                                   │        │
│  │     Backend encrypts and stores in SQLite                        │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  6. UI Update: Show green "Validated" status                     │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Data Flow & State Management

### TraceData Structure

```typescript
interface TraceData {
  title: string;           // "Two Sum Problem"
  strategy: string;        // "Hash Map Approach"
  strategy_details: string;// Detailed explanation
  complexity: {
    time: string;          // "O(n)"
    space: string;         // "O(n)"
  };
  frames: Frame[];         // Visualization frames
  _meta: {
    request_id: string;
    session_id: string;
    provider_used: string;
    model_used: string;
    route_path: string;    // "cache" | "library" | "llm"
  };
}

interface Frame {
  step_id: number;
  commentary: string;      // Human-readable explanation
  state: {
    visual_type: 'array' | 'heap' | 'tree' | 'graph' | 'matrix' | 'list' | 'map';
    data: Record<string, any[]>;  // { "nums": [2,7,11,15], "target": [9] }
    highlights: string[];         // ["nums[0]", "nums[1]"]
  };
  quiz?: {
    question: string;
    options: string[];
    correct: number;       // Index of correct answer
  };
}
```

### State Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STATE FLOW DIAGRAM                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           App.tsx                                    │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │  traceData: TraceData | null                                 │    │    │
│  │  │  isLoading: boolean                                          │    │    │
│  │  │  learningData: LearningData | null                          │    │    │
│  │  │  isBackendOnline: boolean                                    │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                              │                                       │    │
│  │         ┌────────────────────┼────────────────────┐                 │    │
│  │         │                    │                    │                 │    │
│  │         ▼                    ▼                    ▼                 │    │
│  │  ┌───────────┐       ┌─────────────┐      ┌─────────────┐          │    │
│  │  │  Sidebar  │       │  MainPanel  │      │ LearningMode│          │    │
│  │  │           │       │             │      │             │          │    │
│  │  │ Props:    │       │ Props:      │      │ Props:      │          │    │
│  │  │ -onAnalyze│       │ -traceData  │      │ -learningDat│          │    │
│  │  │ -isLoading│       │ -isLoading  │      │ -onComplete │          │    │
│  │  │           │       │             │      │             │          │    │
│  │  │ State:    │       │ State:      │      │ State:      │          │    │
│  │  │ -provider │       │ -currentFram│      │ -currentPhas│          │    │
│  │  │ -model    │       │ -isPlaying  │      │ -quizAnswers│          │    │
│  │  │ -apiKey   │       │ -speed      │      │             │          │    │
│  │  │ -problem  │       │             │      │             │          │    │
│  │  └───────────┘       └─────────────┘      └─────────────┘          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Data Flow:                                                                 │
│  1. Sidebar collects user input (problem, config)                          │
│  2. Sidebar calls onAnalyze callback (lifts data to App)                   │
│  3. App makes API call, updates traceData state                            │
│  4. traceData flows down to MainPanel/LearningMode as props                │
│  5. Child components render based on received props                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Security Architecture

### Threat Model & Mitigations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SECURITY ARCHITECTURE                                 │
│                                                                              │
│  THREAT: API Key Exposure                                                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│  │ Attack Vector         │ Mitigation                                     │ │
│  ├───────────────────────┼───────────────────────────────────────────────┤ │
│  │ Key in localStorage   │ Store encrypted on backend instead            │ │
│  │ Key in URL/logs       │ Send in request body, never in URL params     │ │
│  │ Key in JS bundle      │ User provides key, not hardcoded              │ │
│  │ Key leaked in response│ Never return API key from backend             │ │
│  │ Key stolen from DB    │ Fernet encryption at rest                     │ │
│  └───────────────────────┴───────────────────────────────────────────────┘ │
│                                                                              │
│  THREAT: Cross-Session Data Leakage                                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│  │ Attack Vector         │ Mitigation                                     │ │
│  ├───────────────────────┼───────────────────────────────────────────────┤ │
│  │ Shared global state   │ RequestContext per request                    │ │
│  │ Session ID guessing   │ UUID v4 (122 bits entropy)                    │ │
│  │ Session hijacking     │ Session in sessionStorage (tab-isolated)      │ │
│  └───────────────────────┴───────────────────────────────────────────────┘ │
│                                                                              │
│  THREAT: Cross-Origin Attacks                                               │
│  ─────────────────────────────────────────────────────────────────────────  │
│  │ Attack Vector         │ Mitigation                                     │ │
│  ├───────────────────────┼───────────────────────────────────────────────┤ │
│  │ CSRF                  │ Custom header (X-Session-ID) + CORS           │ │
│  │ Unauthorized origins  │ ALLOWED_ORIGINS env var whitelist             │ │
│  └───────────────────────┴───────────────────────────────────────────────┘ │
│                                                                              │
│  ENCRYPTION DETAILS:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Algorithm: Fernet (symmetric encryption)                            │   │
│  │  Underlying: AES-128-CBC + HMAC-SHA256                              │   │
│  │  Key Source: CREDENTIAL_ENCRYPTION_KEY environment variable          │   │
│  │  Key Generation: Fernet.generate_key() → 32 bytes base64            │   │
│  │  TTL: 24 hours (credentials auto-expire)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CREDENTIAL FLOW COMPARISON                               │
│                                                                              │
│  OPTION A: Credentials in Every Request (Current Default)                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  Frontend                           Backend                                 │
│  ┌──────────┐                      ┌──────────┐                             │
│  │ Store in │  POST /analyze       │ Extract  │     ┌──────────┐           │
│  │ local-   │  { llm_config: {    │ from body│────▶│ LLM API  │           │
│  │ Storage  │    api_key: "xxx"   │          │     └──────────┘           │
│  │          │  }}                  │          │                             │
│  └──────────┘                      └──────────┘                             │
│                                                                              │
│  Pros: Simple, stateless backend                                            │
│  Cons: Key sent with every request, stored in browser                       │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                              │
│  OPTION B: Session-Stored Credentials (More Secure)                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  Frontend                           Backend                                 │
│  ┌──────────┐                      ┌──────────┐     ┌──────────┐           │
│  │ Store    │  POST /store-creds   │ Encrypt  │────▶│ SQLite   │           │
│  │ session  │  { api_key: "xxx" } │ & Store  │     │ (Fernet) │           │
│  │ ID only  │                      └──────────┘     └──────────┘           │
│  └──────────┘                                              │                │
│       │                                                    │                │
│       │      POST /analyze                                 │                │
│       │      X-Session-ID: abc123                          │                │
│       │      { problem_text: "..." }                       ▼                │
│       │                            ┌──────────┐     ┌──────────┐           │
│       └───────────────────────────▶│ Lookup & │────▶│ LLM API  │           │
│                                    │ Decrypt  │     └──────────┘           │
│                                    └──────────┘                             │
│                                                                              │
│  Pros: Key not sent repeatedly, encrypted at rest                          │
│  Cons: Slightly more complex, requires encryption key management           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Caching Strategy

### Multi-Layer Cache Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CACHING ARCHITECTURE                                    │
│                                                                              │
│  Request: "Find two numbers that sum to target"                             │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LAYER 1: Smart Router - Pattern Matching                            │    │
│  │  ─────────────────────────────────────────────────────────────────   │    │
│  │  Check: Does problem match known algorithm pattern?                  │    │
│  │                                                                       │    │
│  │  Patterns: "two sum" → Two Sum                                       │    │
│  │            "binary search" → Binary Search                           │    │
│  │            "quicksort" → Quick Sort                                  │    │
│  │                                                                       │    │
│  │  If match found: Use pre-computed algorithm library                  │    │
│  │  Response time: <10ms                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       │ No pattern match                                                     │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LAYER 2: Memory Cache (RLock-protected)                             │    │
│  │  ─────────────────────────────────────────────────────────────────   │    │
│  │  Key: SHA256(problem_text + context_toggles)                         │    │
│  │  Value: Complete TraceData response                                  │    │
│  │                                                                       │    │
│  │  Why RLock? Multiple readers OR single writer                        │    │
│  │  TTL: Session lifetime (cleared on server restart)                   │    │
│  │  Response time: <5ms                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       │ Cache miss                                                           │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LAYER 3: File Cache (JSON files)                                    │    │
│  │  ─────────────────────────────────────────────────────────────────   │    │
│  │  Location: backend/data/cache/{hash}.json                           │    │
│  │  Persists across server restarts                                     │    │
│  │  TTL: 7 days                                                         │    │
│  │  Response time: <50ms                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       │ Cache miss                                                           │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LAYER 4: LLM Pipeline (Full Processing)                             │    │
│  │  ─────────────────────────────────────────────────────────────────   │    │
│  │  Run 5-agent pipeline                                                │    │
│  │  Make LLM API calls                                                  │    │
│  │  Response time: 10-60 seconds                                        │    │
│  │                                                                       │    │
│  │  After completion: Cache result in Layer 2 + Layer 3                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  CACHE SHARING STRATEGY:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Same problem text + same context = same cache key                   │    │
│  │                                                                       │    │
│  │  User A: "Find two sum" + [Low Memory] → hash: abc123               │    │
│  │  User B: "Find two sum" + [Low Memory] → hash: abc123 (cache hit!)  │    │
│  │  User C: "Find two sum" + [High Throughput] → hash: xyz789 (miss)   │    │
│  │                                                                       │    │
│  │  This is INTENTIONAL:                                                │    │
│  │  - Same problem should get same answer                               │    │
│  │  - Reduces LLM API costs significantly                               │    │
│  │  - API key is NOT part of cache key (results are provider-agnostic) │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cache Key Generation

```python
def generate_cache_key(problem_text: str, context_toggles: list[str]) -> str:
    """
    Generate deterministic cache key from problem and context.

    Why SHA256?
    - Fixed length (64 chars) regardless of input size
    - Deterministic (same input = same output)
    - Collision-resistant

    Why NOT include API key?
    - Same problem should produce same visualization
    - Allows cache sharing between users
    - API key is for authentication, not for results
    """
    normalized = problem_text.strip().lower()
    sorted_toggles = sorted(context_toggles)
    key_input = f"{normalized}:{':'.join(sorted_toggles)}"
    return hashlib.sha256(key_input.encode()).hexdigest()
```

---

## 10. Deployment Architecture

### Production Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION DEPLOYMENT ARCHITECTURE                        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         VERCEL (Frontend)                            │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  Static React Build (Vite)                                     │  │    │
│  │  │  - index.html                                                  │  │    │
│  │  │  - assets/*.js, *.css                                          │  │    │
│  │  │                                                                 │  │    │
│  │  │  Environment Variables:                                        │  │    │
│  │  │  VITE_API_BASE_URL=https://algoinsight-api.railway.app        │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  │                                                                      │    │
│  │  Features:                                                          │    │
│  │  ✓ Global CDN (edge caching)                                       │    │
│  │  ✓ Automatic HTTPS                                                 │    │
│  │  ✓ Preview deployments for PRs                                     │    │
│  │  ✓ Zero-config deployment from Git                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              │ HTTPS API Calls                              │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    RAILWAY / RENDER (Backend)                        │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  FastAPI + Uvicorn                                             │  │    │
│  │  │  Docker Container                                              │  │    │
│  │  │                                                                 │  │    │
│  │  │  Environment Variables:                                        │  │    │
│  │  │  ALLOWED_ORIGINS=https://algoinsight.vercel.app               │  │    │
│  │  │  CREDENTIAL_ENCRYPTION_KEY=<fernet-key>                       │  │    │
│  │  │  # Optional: Default LLM keys for fallback                    │  │    │
│  │  │  AZURE_OPENAI_API_KEY=xxx (optional)                          │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  │                                                                      │    │
│  │  Persistent Storage:                                                │    │
│  │  ✓ data/sessions.db (credential store)                             │    │
│  │  ✓ data/cache/ (file cache)                                        │    │
│  │                                                                      │    │
│  │  Features:                                                          │    │
│  │  ✓ Auto-scaling                                                    │    │
│  │  ✓ Persistent volumes                                              │    │
│  │  ✓ Zero-downtime deploys                                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              │ HTTPS (Provider APIs)                        │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      LLM PROVIDER APIS                               │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │    │
│  │  │ Azure       │  │ OpenAI      │  │ Google AI                   │  │    │
│  │  │ OpenAI      │  │ API         │  │ (Gemini)                    │  │    │
│  │  │ (Regional)  │  │ (Global)    │  │                             │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Environment Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ENVIRONMENT CONFIGURATION                                │
│                                                                              │
│  FRONTEND (.env.local - Development)                                        │
│  ────────────────────────────────────                                       │
│  VITE_API_BASE_URL=http://localhost:8000                                    │
│                                                                              │
│  FRONTEND (.env.production - Production)                                    │
│  ───────────────────────────────────────                                    │
│  VITE_API_BASE_URL=https://your-backend.railway.app                         │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                              │
│  BACKEND (.env - All Environments)                                          │
│  ─────────────────────────────────                                          │
│                                                                              │
│  # CORS Configuration (comma-separated for multiple origins)                │
│  ALLOWED_ORIGINS=https://algoinsight.vercel.app,http://localhost:5173       │
│                                                                              │
│  # Credential Encryption (REQUIRED for production)                          │
│  CREDENTIAL_ENCRYPTION_KEY=<generate with Fernet.generate_key()>            │
│                                                                              │
│  # Optional: Default LLM API Keys (fallback when user doesn't provide)      │
│  AZURE_OPENAI_API_KEY=xxx                                                   │
│  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/              │
│  AZURE_DEPLOYMENT_NAME=gpt-4o                                               │
│                                                                              │
│  OPENAI_API_KEY=xxx                                                         │
│  GEMINI_API_KEY=xxx                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Interview Q&A

### Architecture & Design Questions

**Q: Why did you choose FastAPI over Flask or Django?**
```
A: FastAPI was chosen for several reasons:
   1. Native async support - critical for I/O-bound LLM API calls
   2. Automatic OpenAPI documentation (/docs endpoint)
   3. Pydantic models for request/response validation
   4. Type hints throughout for better IDE support
   5. Performance - one of the fastest Python frameworks

   Django would be overkill (don't need ORM, admin panel)
   Flask lacks native async and auto-documentation
```

**Q: How do you ensure thread safety for concurrent users?**
```
A: Multiple mechanisms:
   1. RequestContext pattern - each request gets isolated context
   2. No shared mutable global state
   3. RLock on cache operations (multiple readers OR single writer)
   4. SQLite with proper connection handling (new connection per query)
   5. Stateless API design - server can be horizontally scaled
```

**Q: Why store credentials on the backend instead of just localStorage?**
```
A: Defense in depth:
   1. localStorage is accessible to any JS on the page (XSS risk)
   2. Backend encryption adds protection at rest
   3. TTL enforcement is more reliable server-side
   4. Never need to send API key after initial storage
   5. Easier to audit and rotate encryption keys

   Trade-off: More complex implementation, requires encryption key management
```

**Q: Explain your caching strategy.**
```
A: Four-layer caching with different purposes:

   Layer 1 (Pattern Matching): <10ms
   - Pre-computed traces for common algorithms
   - No LLM calls needed

   Layer 2 (Memory Cache): <5ms
   - In-process dictionary with RLock
   - Lost on server restart

   Layer 3 (File Cache): <50ms
   - JSON files on disk
   - Survives restarts
   - 7-day TTL

   Layer 4 (LLM Pipeline): 10-60s
   - Full processing
   - Results cached in L2+L3

   Cache key: SHA256(problem + toggles)
   Shared between users: YES (same problem = same answer)
```

### Code-Level Questions

**Q: How does the Provider Factory pattern work?**
```python
# Factory Method Pattern
# Problem: Need to create different LLM providers based on runtime config

class LLMProviderFactory:
    @staticmethod
    def create_from_context(ctx: RequestContext) -> BaseLLMProvider:
        providers = {
            'azure': AzureOpenAIProvider,
            'openai': OpenAIProvider,
            'gemini': GeminiProvider,
        }
        return providers[ctx.provider](ctx.api_key, ctx.model)

# Usage:
provider = LLMProviderFactory.create_from_context(context)
response = provider.complete(prompt)

# Benefits:
# - Decouples creation from usage
# - Easy to add new providers
# - Single point of change for provider config
```

**Q: How do you handle session ID generation and why UUID v4?**
```typescript
// UUID v4: Random-based, 122 bits of entropy
const sessionId = crypto.randomUUID();
// Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

// Why UUID v4?
// - Cryptographically random (no predictable patterns)
// - Standard format (easy to validate/parse)
// - Native browser support (crypto.randomUUID())
// - Virtually impossible to guess (2^122 possibilities)

// Why sessionStorage over localStorage?
// - Isolated per tab (each tab = new session)
// - Cleared on tab close (session ends)
// - Not shared across tabs (privacy)
```

**Q: How do you prevent CSRF attacks?**
```
A: Multiple layers of protection:

1. Custom Header Requirement:
   - All requests include X-Session-ID header
   - Browsers don't send custom headers in CSRF attacks
   - Simple forms can't add custom headers

2. CORS Whitelist:
   - ALLOWED_ORIGINS environment variable
   - Only specified origins can make requests
   - Preflight requests (OPTIONS) required for POST

3. JSON Content-Type:
   - All requests use application/json
   - Simple CSRF forms can't set this header

4. No cookie-based auth:
   - We don't use cookies for authentication
   - Session ID is explicitly sent per request
```

### Scaling Questions

**Q: How would you scale this system for 10x users?**
```
A: Horizontal and vertical scaling strategies:

1. Frontend (Already scalable):
   - Vercel CDN handles any load
   - Static assets cached at edge

2. Backend scaling:
   - Horizontal: Multiple container instances behind load balancer
   - Stateless design allows any instance to handle any request
   - Session credentials in SQLite → migrate to Redis/PostgreSQL

3. Cache scaling:
   - Memory cache → Redis cluster (shared across instances)
   - File cache → S3/GCS with CloudFront/CDN

4. LLM API calls:
   - Already async (non-blocking)
   - Rate limiting per user session
   - Queue long-running requests

5. Database:
   - SQLite → PostgreSQL for concurrent writes
   - Read replicas for credential lookups
```

**Q: What's the biggest bottleneck and how would you address it?**
```
A: LLM API latency (10-60 seconds per request)

Current mitigations:
1. Aggressive caching (4 layers)
2. Pattern matching for instant responses
3. Async processing (non-blocking I/O)

Additional improvements:
1. Streaming responses (partial results while processing)
2. Pre-computation of popular algorithms
3. Request queuing with progress updates
4. Parallel agent execution where possible
5. Smaller/faster models for initial steps
```

### Security Questions

**Q: What happens if the CREDENTIAL_ENCRYPTION_KEY is compromised?**
```
A: Impact and remediation:

Impact:
- All stored API keys can be decrypted
- Attacker could use them for LLM API calls

Remediation:
1. Generate new encryption key immediately
2. All existing encrypted credentials become invalid
3. Users must re-enter their API keys
4. Old database is useless without old key

Prevention:
- Store key in secure secrets manager (AWS Secrets Manager, etc.)
- Rotate key periodically
- Audit access to key
- Never log or expose the key
```

**Q: How do you prevent one user from accessing another's credentials?**
```
A: Multiple isolation mechanisms:

1. Session ID as primary key:
   - Credentials stored by session_id
   - UUIDv4 is unguessable (122 bits entropy)

2. Backend-only storage:
   - API keys never returned to frontend after storage
   - Only metadata (provider, model) returned

3. Request isolation:
   - Each request creates new RequestContext
   - No shared state between requests

4. No credential enumeration:
   - API returns same response for "not found" and "invalid"
   - Can't determine if a session exists
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          QUICK REFERENCE                                     │
│                                                                              │
│  FRONTEND ENTRY POINTS                                                      │
│  ─────────────────────                                                      │
│  App.tsx          → Main component, state management                        │
│  Sidebar.tsx      → User input, LLM config                                  │
│  MainPanel.tsx    → Visualization display                                   │
│  apiService.ts    → All backend communication                               │
│                                                                              │
│  BACKEND ENTRY POINTS                                                       │
│  ────────────────────                                                       │
│  main.py          → FastAPI app, all endpoints                              │
│  pipeline.py      → 5-agent orchestration                                   │
│  request_context.py → Request isolation                                     │
│  credential_store.py → Encrypted storage                                    │
│                                                                              │
│  KEY ENDPOINTS                                                              │
│  ─────────────                                                              │
│  POST /analyze              → Run analysis pipeline                         │
│  POST /learn                → Run educational flow                          │
│  POST /validate-credentials → Validate LLM keys                             │
│  POST /session/store-credentials → Store encrypted keys                     │
│  GET  /session/{id}/credentials  → Get credential metadata                  │
│                                                                              │
│  ENVIRONMENT VARIABLES                                                      │
│  ────────────────────                                                       │
│  Frontend:                                                                  │
│    VITE_API_BASE_URL      → Backend URL                                     │
│                                                                              │
│  Backend:                                                                   │
│    ALLOWED_ORIGINS        → CORS whitelist                                  │
│    CREDENTIAL_ENCRYPTION_KEY → Fernet key for encryption                    │
│    AZURE_OPENAI_API_KEY   → Optional fallback key                          │
│                                                                              │
│  DATA FLOW                                                                  │
│  ─────────                                                                  │
│  User Input → Sidebar → App → apiService → Backend → Pipeline → LLM        │
│                                                                              │
│  SESSION FLOW                                                               │
│  ────────────                                                               │
│  New Tab → Generate UUID → Store in sessionStorage → Send with requests     │
│                                                                              │
│  CREDENTIAL FLOW                                                            │
│  ───────────────                                                            │
│  Enter Key → Validate → Encrypt → Store in SQLite → Use via session lookup  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Conclusion

AlgoInsight demonstrates several modern software engineering practices:

1. **Clean Architecture**: Separation of concerns between frontend, API, and business logic
2. **Design Patterns**: Factory, Context, and Observer patterns applied appropriately
3. **Security First**: Encryption at rest, session isolation, CORS protection
4. **Performance**: Multi-layer caching, async operations, pattern matching
5. **Scalability**: Stateless backend, horizontal scaling ready
6. **Developer Experience**: Type safety, auto-documentation, clear structure

The multi-user session support enables production deployment while maintaining security and isolation between users.

---

*Document Version: 1.0*
*Last Updated: 2024*
*Author: AlgoInsight Team*
