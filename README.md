# AlgoInsight
### The Human Algorithm Debugger

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

- **Agentic Pipeline** - A 5-stage AI pipeline (Normalizer → Strategist → Instrumenter → Tracer → Narrator) that ensures deterministic accuracy
- **Interactive Traces** - Scrubbable timelines of algorithm execution (not static GIFs)
- **Context-Aware** - Toggles for "Embedded Systems" or "High Frequency Trading" change the algorithm recommendations
- **Active Learning** - The system pauses to quiz you ("Why did the heap rebalance here?") to ensure retention
- **Privacy-First** - Code execution happens in a secure local sandbox, not on the cloud

---

## Technical Architecture

AlgoInsight is not a wrapper around ChatGPT. It uses a **Hybrid Execution Model**:

| Agent | Role |
|-------|------|
| **Normalizer** | Sanitizes input and detects User Intent (Learn vs. Production) |
| **Strategist** | Consults a local Heuristics DB to select the best architectural pattern |
| **Instrumenter** | Generates "Spy Code" – a hidden Python script designed to log internal states |
| **Tracer** | Executes the Spy Code locally to generate a precise JSON Trace |
| **Narrator** | Consumes the JSON Trace to generate commentary and educational quizzes |

**Tech Stack:**
- **Frontend:** React, TypeScript, Vite, TailwindCSS, Framer Motion
- **Backend:** Python, FastAPI, Pydantic, NetworkX
- **AI Layer:** Google Gemini / Azure OpenAI (Swappable)

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### Frontend

```bash
npm install
npm run dev
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Environment Variables

Create `.env` file in the backend directory:

```env
# For Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_API_VERSION=2024-08-01-preview
AZURE_DEPLOYMENT_NAME=gpt-4o

# Or for Gemini
API_KEY=your_gemini_api_key
```

---

## Project Structure

```
AlgoInsight/
├── components/          # React UI components
├── services/            # API service layer
├── public/algorithms/   # Algorithm explanation data
├── backend/
│   └── app/
│       ├── agents/      # AI agents (normalizer, strategist, etc.)
│       ├── utils/       # Utilities (LLM provider, logger)
│       └── main.py      # FastAPI application
```

---

## How It Works

1. **Submit a Problem** - Paste any DSA problem
2. **Learn the Approach** - Understand problem breakdown and algorithm selection
3. **Deep Dive** - Learn the recommended algorithm in detail
4. **Visualize** - Watch the algorithm solve your specific problem
5. **Practice** - Answer quizzes to reinforce learning

---

## License

MIT
