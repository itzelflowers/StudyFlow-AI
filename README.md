# 🧠 StudyFlow AI

> From the intention to learn to real progress, guided by AI.

StudyFlow AI is an **agentic learning coach** that transforms vague educational goals into structured, personalized study plans with actionable tasks, curated resources, and adaptive progress support.

## ✨ Features

- 🎯 **Smart Goal Analysis** — Enter any learning goal and get assessed
- 📝 **Diagnostic Quiz** — AI-generated questions to gauge your level
- 📋 **Personalized Study Plans** — Milestone-based roadmaps tailored to your time and level
- 📚 **Curated Resources** — Ranked learning materials from Khan Academy, MIT OCW, 3Blue1Brown, and more
- ✅ **Task Tracking** — Daily tasks with progress monitoring
- 🔄 **Adaptive Planning** — Automatic plan adjustment when you get stuck or advance faster
- 🧠 **AI Coaching** — Encouragement and guidance from a progress-aware coach

## 🏗️ Architecture

StudyFlow AI uses a **multi-agent system** powered by LangGraph:

| Agent | Role |
|-------|------|
| **Planning Agent** | Interprets goals, assesses level, creates milestones |
| **Research Agent** | Finds and ranks learning resources |
| **Coaching Agent** | Converts milestones into daily actionable tasks |
| **Progress Agent** | Monitors completion, detects bottlenecks, adapts the plan |

## 🛠️ Tech Stack

- **LLM**: Qwen3-30B-A3B (via Hugging Face Inference API)
- **Agent Orchestration**: LangGraph
- **Vector DB**: Qdrant (in-memory)
- **Embeddings**: FastEmbed (BGE-small-en-v1.5)
- **Backend**: FastAPI
- **Frontend**: Gradio
- **Database**: SQLite
- **Deployment**: Hugging Face Spaces

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/StudyFlow-AI.git
cd StudyFlow-AI
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
# Edit .env and add your HF_TOKEN
```

### 5. Run the application

```bash
python app/main.py
```

Open http://localhost:7860 in your browser.

## 📁 Project Structure

```
StudyFlow-AI/
├── app/                    # Gradio frontend
│   ├── main.py            # Entry point
│   ├── theme.py           # Custom theme + CSS
│   └── components/        # UI components
├── backend/               # FastAPI backend
│   ├── server.py          # REST API
│   ├── models/            # Pydantic schemas + DB
│   └── services/          # LLM client + session mgmt
├── agents/                # LangGraph agent system
│   ├── graph.py           # Workflow definition
│   ├── state.py           # Shared state schema
│   └── nodes/             # Agent implementations
├── rag/                   # RAG + Qdrant
│   ├── embeddings.py      # Embedding model
│   ├── indexer.py         # Resource indexing
│   └── retriever.py       # Semantic search
└── data/                  # Seed data
    └── sample_resources.json
```

## 📄 License

MIT License

## 👥 Team

Built for the AMD Hackathon 2026.
