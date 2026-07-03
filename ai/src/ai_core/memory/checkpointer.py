"""Short-term memory (LangGraph checkpointer) factory.

The checkpointer persists per-conversation graph state (messages, findings,
completed agents) keyed by ``thread_id``, which is what makes follow-up
questions cheap: the supervisor sees existing findings and can answer without
re-running research.

Backends:
    memory   — in-process, lost on restart (default; zero setup)
    postgres — durable across restarts (set AI_CHECKPOINTER=postgres and
               AI_CHECKPOINTER_POSTGRES_URL=postgresql://user:pass@host:5432/db)

To add a new backend (e.g. Redis, SQLite), add a branch here — nothing else
in the codebase needs to change.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver

from ai_core.config import get_settings


@asynccontextmanager
async def create_checkpointer() -> AsyncIterator[BaseCheckpointSaver]:
    settings = get_settings()

    if settings.checkpointer == "postgres":
        if not settings.checkpointer_postgres_url:
            raise ValueError(
                "AI_CHECKPOINTER=postgres requires AI_CHECKPOINTER_POSTGRES_URL "
                "(plain postgresql:// URL, no SQLAlchemy driver suffix)"
            )
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        async with AsyncPostgresSaver.from_conn_string(
            settings.checkpointer_postgres_url
        ) as saver:
            await saver.setup()
            yield saver
    else:
        yield InMemorySaver()
