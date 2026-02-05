# AlgoInsight: The Human Algorithm Debugger

![AlgoInsight Demo](demo.gif)

**AlgoInsight** is an AI-powered, local-first platform that transforms raw problem statements into interactive, step-by-step algorithmic visualizations. It bridges the gap between abstract theory and production-grade engineering.

---

## The "Why"

I built AlgoInsight after realizing a critical gap during technical interviews: **We often memorize syntax, but fail to visualize the "mechanics" of an algorithm.**

Standard AI tools give you code. AlgoInsight gives you **intuition**. It acts as a "flight simulator" for logic, helping developers:

1. **Visualize** how data structures mutate in real-time
2. **Debug** thought processes before writing a single line of code
3. **Optimize** for production constraints (Embedded, High-Throughput, Low-Memory)

---

## Key Features

- **Agentic Pipeline:** A 5-stage AI pipeline (Normalizer → Strategist → Instrumenter → Tracer → Narrator) that ensures deterministic accuracy
- **Interactive Traces:** Scrubbable timelines of algorithm execution (not static GIFs)
- **Context-Aware:** Toggles for "Embedded Systems" or "High Frequency Trading" change the algorithm recommendations
- **Active Learning:** The system pauses to quiz you ("Why did the heap rebalance here?") to ensure retention
- **Privacy-First:** Code execution happens in a secure local sandbox, not on the cloud
- **Multi-Provider LLM Support:** Choose between Azure OpenAI, OpenAI, or Google Gemini
- **Dual Mode:** Learning mode for education, Quick mode for direct visualization

---

## Technical Architecture

AlgoInsight is not a wrapper around ChatGPT. It uses a **Hybrid Execution Model**:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Normalizer  │ ──▶ │  Strategist  │ ──▶ │ Instrumenter │ ──▶ │    Tracer    │ ──▶ │   Narrator   │
│  Parse &     │     │  Select      │     │  Generate    │     │  Execute &   │     │  Generate    │
│  Normalize   │     │  Algorithm   │     │  Spy Code    │     │  Trace       │     │  Commentary  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

1. **Normalizer Agent:** Sanitizes input and detects User Intent (Learn vs. Production)
2. **Strategist Agent:** Consults a local Heuristics DB to select the best architectural pattern
3. **Instrumenter Agent:** Generates "Spy Code" – a hidden Python script designed to log internal states
4. **Tracer (Sandbox):** Executes the Spy Code locally to generate a precise JSON Trace
5. **Narrator Agent:** Consumes the JSON Trace to generate commentary and educational quizzes

### Additional Systems

- **Smart Router:** Pattern matching for instant responses on common algorithms
- **Multi-Layer Cache:** Memory + File cache for optimal performance
- **Credential Store:** Encrypted API key storage with session management

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS, Framer Motion |
| **Backend** | Python 3.11, FastAPI, Uvicorn, Pydantic |
| **AI Layer** | Azure OpenAI / OpenAI / Google Gemini (Swappable) |
| **Storage** | SQLite (credentials), JSON (cache) |

---

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1. Clone the Repo

```bash
git clone https://github.com/tushitdave/AlgoInsight.git
cd AlgoInsight
```

### 2. Frontend Setup

```bash
npm install
npm run dev
```

### 3. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. Environment Variables

Create `.env` file in the backend directory:

**For Azure OpenAI:**
```env
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_API_VERSION=2024-08-01-preview
AZURE_DEPLOYMENT_NAME=gpt-4o
```

**For OpenAI:**
```env
OPENAI_API_KEY=your_openai_key
```

**For Gemini:**
```env
GEMINI_API_KEY=your_gemini_api_key
```

**Security (Required for production):**
```env
CREDENTIAL_ENCRYPTION_KEY=your_fernet_key
ALLOWED_ORIGINS=http://localhost:5173
```

---

## Project Structure

```
AlgoInsight/
├── components/              # React UI components
├── services/                # API service layer
├── public/algorithms/       # Algorithm visualization data
├── backend/
│   └── app/
│       ├── agents/          # AI agents (normalizer, strategist, etc.)
│       ├── algorithms/      # Pre-computed algorithm library
│       ├── cache/           # Multi-layer caching system
│       ├── router/          # Smart routing with pattern matching
│       ├── utils/
│       │   ├── providers/   # LLM providers (Azure, OpenAI, Gemini)
│       │   ├── credential_store.py
│       │   └── request_context.py
│       ├── pipeline.py      # 5-agent orchestration
│       └── main.py          # FastAPI application
└── Architecture.md          # Detailed system documentation
```

---

## How It Works

1. **Submit a Problem** - Paste any DSA problem
2. **Learn the Approach** - Understand problem breakdown and algorithm selection
3. **Deep Dive** - Learn the recommended algorithm in detail
4. **Visualize** - Watch the algorithm solve your specific problem
5. **Practice** - Answer quizzes to reinforce learning

---

## Security Features

- **Encrypted Credentials:** API keys encrypted at rest using Fernet (AES-128)
- **Session Isolation:** Each user session is completely isolated
- **No Cloud Storage:** All sensitive data stays local
- **CORS Protection:** Configurable origin whitelist

---

## License

MIT
