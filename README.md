# Startup Agent Lab

I Built this project just to show how langchain and langraph helps orchestrating agents. 
Built with. Project shows clearly how each agent is called.

- Next.js 16, React 19, TypeScript, Tailwind CSS 4
- FastAPI, WebSockets, SQLAlchemy, PostgreSQL
- LangChain 1.x and LangGraph 1.x
- Docker Compose for the full stack
- OpenRouter or direct model providers

See [ARCHITECTURE.md](ARCHITECTURE.md) for the Mermaid system diagram.

## Features

- Live multi-agent research workflow
- Streaming final report
- Agent activity feed with tools, handoffs, status, and errors
- Stop button that cancels an active research run
- Conversation persistence in PostgreSQL
- LangGraph checkpoint memory: in-process by default, optional PostgreSQL
- Model switching with direct providers or OpenRouter
- Dockerized frontend, backend, and database

## Agent Team

| Agent | Role |
|---|---|
| Supervisor | Plans work, assigns specialists, reviews findings, decides when to finish |
| Market Research | Market size, demand, trends, and timing |
| Competitor Analysis | Direct and indirect competitors, strengths, gaps |
| Customer Research | Segments, personas, pain points, willingness to pay |
| Product Strategy | Value proposition, MVP, pricing, business model |
| Risk Analysis | Market, execution, financial, legal, and technical risks |
| Marketing Strategy | Positioning, launch plan, channels, growth loops |
| Report Writer | Synthesizes findings into the final answer |

## Repository Layout

```text
ai/                  LangChain/LangGraph engine, prompts, tools, memory
backend/             FastAPI app, REST, WebSocket, persistence
frontend/            Next.js chat and live workflow UI
docker-compose.yml   Postgres, backend, frontend
ARCHITECTURE.md      Mermaid architecture diagram
```

## Quick Start With Docker

Create `ai/.env` from [ai/.env.example](ai/.env.example):

```powershell
Copy-Item .\ai\.env.example .\ai\.env
```

Set a model and API key. OpenRouter example:

```env
AI_MODEL=openrouter:openai/gpt-5-mini
OPENROUTER_API_KEY=sk-or-...
```

Direct provider example:

```env
AI_MODEL=openai:gpt-5-mini
OPENAI_API_KEY=sk-...
```

Run the full stack:

```powershell
docker compose up -d --build
```

Open:

```text
http://localhost:3000
```

If port 3000 is busy:

```powershell
$env:FRONTEND_PORT = "3001"
docker compose up -d --build
```

Then open:

```text
http://localhost:3001
```

Useful Docker commands:

```powershell
docker compose ps
docker compose logs -f backend
docker compose down
```

## Local Development

Start only PostgreSQL:

```powershell
docker compose up -d postgres
```

Install Python packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .\ai -e .\backend
```

Create `backend/.env` from [backend/.env.example](backend/.env.example) if you
need local backend overrides:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/startup_research
CORS_ORIGINS=["http://localhost:3000"]
```

Run the backend:

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

Run the frontend:

```powershell
cd frontend
npm install
npm run dev
```

Health check:

```text
http://localhost:8000/api/health
```

## Model Configuration

AI settings live in `ai/.env`. The real file is ignored by git; commit only
`ai/.env.example`.

Direct provider format:

```env
AI_MODEL=provider:model
```

Examples:

```env
AI_MODEL=openai:gpt-5-mini
OPENAI_API_KEY=sk-...
```

```env
AI_MODEL=google_genai:gemini-2.5-flash
GOOGLE_API_KEY=AIza...
```

OpenRouter format:

```env
AI_MODEL=openrouter:provider/model
OPENROUTER_API_KEY=sk-or-...
```

Example:

```env
AI_MODEL=openrouter:nousresearch/hermes-3-llama-3.1-405b:free
OPENROUTER_API_KEY=sk-or-...
```

Notes:

- OpenRouter model IDs are passed through unchanged after `openrouter:`.
- Direct provider models continue to use LangChain provider names.
- Some free OpenRouter models may not support this workflow reliably because
  the app uses tool-calling and structured supervisor routing.

## Runtime Configuration

| Variable | File | Purpose |
|---|---|---|
| `AI_MODEL` | `ai/.env` | Default model, direct or OpenRouter |
| `OPENROUTER_API_KEY` | `ai/.env` | Required for `AI_MODEL=openrouter:...` |
| `OPENAI_API_KEY` | `ai/.env` | OpenAI direct provider |
| `ANTHROPIC_API_KEY` | `ai/.env` | Anthropic direct provider |
| `GOOGLE_API_KEY` | `ai/.env` | Google Gemini direct provider |
| `TAVILY_API_KEY` | `ai/.env` | Optional Tavily search |
| `AI_CHECKPOINTER` | `ai/.env` | `memory` or `postgres` |
| `DATABASE_URL` | `backend/.env` | Backend persistence URL for local runs |
| `CORS_ORIGINS` | `backend/.env` | Allowed frontend origins |
| `FRONTEND_PORT` | shell/root env | Host port for Docker frontend |
| `BACKEND_PORT` | shell/root env | Host port for Docker backend |
| `POSTGRES_USER` | shell/root env | Docker Postgres user |
| `POSTGRES_PASSWORD` | shell/root env | Docker Postgres password |
| `POSTGRES_DB` | shell/root env | Docker Postgres database |

## How A Research Run Works

1. The browser opens a WebSocket to `/ws/conversations/{conversation_id}`.
2. A chat message starts a backend research task.
3. The backend sends `run_started`, workflow, agent, handoff, tool, token, and
   completion events to the frontend.
4. The supervisor chooses specialists one at a time.
5. Specialists call tools and return markdown findings.
6. The report writer streams the final report token by token.
7. Messages and run events are persisted to PostgreSQL when the database is up.
8. Pressing the stop button sends `{"type":"stop"}` and cancels the active run.

## Memory

The project has two memory layers:

- Conversation and run persistence in PostgreSQL.
- LangGraph checkpoint memory through `AI_CHECKPOINTER`.

Defaults:

```env
AI_CHECKPOINTER=memory
```

Durable checkpointing:

```env
AI_CHECKPOINTER=postgres
AI_CHECKPOINTER_POSTGRES_URL=postgresql://postgres:postgres@postgres:5432/startup_research
```

## Security Notes

- Do not commit `ai/.env`, `backend/.env`, or `frontend/.env.local`.
- Root `.gitignore` ignores env files recursively and keeps only `.env.example`
  files trackable.
- Avoid sharing `docker compose config` output because Compose expands env files
  and can print API keys.
- Change default Postgres credentials for shared or deployed environments.
- `npm audit --audit-level=moderate` currently reports zero vulnerabilities.
- `pip check` currently reports no broken Python requirements.

## Extending

- New agent: add `ai/src/ai_core/prompts/agents/<name>.yaml` and list it in the
  workflow YAML.
- New tool: add a factory in `ai/src/ai_core/tools/`, register it in
  `tools/registry.py`, and reference it from agent YAML.
- New model: change `AI_MODEL` or use a per-agent YAML override such as
  `model: { name: "openrouter:openai/gpt-5-mini" }`.
- New workflow: add a workflow YAML and compile it with
  `build_startup_research_graph(workflow_name=...)`.
