# AlgoInsight

**Interactive Algorithm Learning & Visualization Platform**

![AlgoInsight Demo](demo.gif)

AlgoInsight is an educational platform that helps developers master Data Structures and Algorithms through interactive visualizations, step-by-step learning journeys, and hands-on practice exercises.

## Features

- **Learning Journey** - Guided step-by-step problem analysis
- **Algorithm Deep Dive** - Comprehensive explanations with visual walkthroughs
- **Live Visualization** - Watch algorithms execute on your actual input data
- **Interactive Quizzes** - Test your understanding at key decision points
- **Dual Mode** - Learning mode for education, Quick mode for direct visualization

## Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS, Framer Motion
- **Backend**: Python, FastAPI, Azure OpenAI / Google Gemini
- **Build**: Vite

## Quick Start

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
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_API_VERSION=2024-08-01-preview
AZURE_DEPLOYMENT_NAME=gpt-4o
```

Or for Gemini:

```env
API_KEY=your_gemini_api_key
```

## Project Structure

```
algoinsight/
├── components/          # React UI components
├── services/            # API service layer
├── public/algorithms/   # Algorithm explanation data
├── backend/
│   └── app/
│       ├── agents/      # AI agents (normalizer, strategist, etc.)
│       ├── utils/       # Utilities (LLM provider, logger)
│       └── main.py      # FastAPI application
└── _dev_docs/           # Development documentation
```

## How It Works

1. **Submit a Problem** - Paste any DSA problem
2. **Learn the Approach** - Understand problem breakdown and algorithm selection
3. **Deep Dive** - Learn the recommended algorithm in detail
4. **Visualize** - Watch the algorithm solve your specific problem
5. **Practice** - Answer quizzes to reinforce learning

## License

MIT
