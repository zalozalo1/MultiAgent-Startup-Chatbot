"""FastAPI application entrypoint.

Run from the backend/ directory (so .env is picked up):
    uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_core import ResearchWorkflowRunner, build_startup_research_graph, create_checkpointer
from app.api.routes import conversations, health, ws
from app.core.config import get_settings
from app.db.session import engine, init_db
from app.services.research_service import ResearchService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.db_ready = await init_db()
    app.state.workflow_error = None
    app.state.research_service = None

    stack = AsyncExitStack()
    try:
        checkpointer = await stack.enter_async_context(create_checkpointer())
        graph = build_startup_research_graph(checkpointer=checkpointer)
        runner = ResearchWorkflowRunner(graph)
        app.state.research_service = ResearchService(runner, db_ready=app.state.db_ready)
        logger.info("AI engine ready (db_ready=%s)", app.state.db_ready)
    except Exception as exc:
        # Boot anyway so /api/health can explain what's wrong (e.g. missing key).
        logger.exception("AI engine failed to initialize")
        app.state.workflow_error = str(exc)

    yield

    await stack.aclose()
    await engine.dispose()


app = FastAPI(title="Startup Research Assistant API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(conversations.router)
app.include_router(ws.router)
