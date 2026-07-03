# ai — Multi-Agent Research Engine

LangChain 1.x + LangGraph 1.x engine that powers the startup research
assistant. Installed as the `ai_core` package and consumed by the backend.

## Architecture

```
src/ai_core/
├── config.py            # AISettings — env-driven configuration (AI_* vars)
├── workflow.py          # ResearchWorkflowRunner — public streaming API
├── prompts/             # ALL agent behavior lives here, as YAML
│   ├── loader.py        #   YAML -> validated pydantic configs + {var} rendering
│   ├── agents/          #   one file per agent: role, prompts, tools, model
│   └── workflows/       #   workflow wiring: supervisor, specialists, limits
├── agents/              # YAML spec -> runnable agent (langchain create_agent)
├── graphs/              # LangGraph workflow: state, nodes, graph builder
├── tools/               # tool registry + instrumentation (live tool events)
├── models/              # chat model factory (provider:model via init_chat_model)
├── memory/              # checkpointer factory (in-memory | postgres)
├── streaming/           # AgentEvent emission (custom stream + contextvars)
└── schemas/             # AgentEvent / AgentInfo wire types
```

## How a run works

1. `ResearchWorkflowRunner.astream(thread_id, message)` invokes the graph.
2. `intake` resets per-run state and announces the roster (`workflow_started`).
3. `supervisor` (structured-output LLM) picks one specialist at a time and
   writes it a concrete task brief (`handoff` events).
4. Each specialist is a tool-calling agent (`create_agent`) that researches
   with instrumented tools and returns markdown findings.
5. When coverage is sufficient (or the iteration budget runs out), the
   supervisor routes to `report_writer`, which streams the final report
   token by token.
6. Every step emits typed `AgentEvent`s on LangGraph's `custom` stream —
   that is the only contract the backend/frontend depend on.

State is checkpointed per `thread_id`, so follow-up messages in the same
conversation reuse existing findings instead of re-running research.

## Extending

| To add…            | Do this                                                                 |
|--------------------|-------------------------------------------------------------------------|
| a new agent        | create `prompts/agents/<name>.yaml`, list it under `specialists` in the workflow YAML |
| a new tool         | add a factory in `tools/`, register it in `tools/registry.py`, reference by name in agent YAML |
| a new workflow     | add `prompts/workflows/<name>.yaml`, build with `build_startup_research_graph(workflow_name=...)` |
| a new model/provider | set `AI_MODEL=provider:model`, use `AI_MODEL=openrouter:provider/model`, or add a per-agent `model.name` override in YAML |
| a new memory backend | add a branch in `memory/checkpointer.py`                              |

## Configuration (env vars)

| Variable | Default | Purpose |
|---|---|---|
| `AI_MODEL` | `openai:gpt-5-mini` | default chat model (`provider:model` or `openrouter:provider/model`) |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` | — | direct provider credentials |
| `OPENROUTER_API_KEY` | — | required when `AI_MODEL` starts with `openrouter:` |
| `AI_CHECKPOINTER` | `memory` | `memory` or `postgres` |
| `AI_CHECKPOINTER_POSTGRES_URL` | — | plain `postgresql://` URL for durable memory |
| `AI_SEARCH_PROVIDER` | `auto` | `auto` / `duckduckgo` / `tavily` |
| `TAVILY_API_KEY` | — | enables Tavily search in `auto` mode |
| `AI_MAX_SEARCH_RESULTS` | `6` | results per search |
| `AI_AGENT_RECURSION_LIMIT` | `25` | per-specialist ReAct loop budget |

Examples:

```env
AI_MODEL=openrouter:openai/gpt-5-mini
OPENROUTER_API_KEY=sk-or-...
```

```env
AI_MODEL=openai:gpt-5-mini
OPENAI_API_KEY=sk-...
```
