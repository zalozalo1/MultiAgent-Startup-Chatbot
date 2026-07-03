"""Bridges the AI engine to clients: runs the workflow for a user message,
forwards every AgentEvent to the caller-supplied ``send`` callback (the
WebSocket), and persists the conversation trail to Postgres.

Persistence is best-effort: if the database is down the chat still works,
it just isn't stored.
"""

import logging
import uuid
from asyncio import CancelledError
from datetime import datetime, timezone
from typing import Awaitable, Callable

from sqlalchemy import select

from ai_core import AgentEvent, EventType, ResearchWorkflowRunner
from app.db.session import SessionLocal
from app.models import Conversation, Message, ResearchRun, RunEvent

logger = logging.getLogger(__name__)

Send = Callable[[dict], Awaitable[None]]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResearchService:
    def __init__(self, runner: ResearchWorkflowRunner, db_ready: bool):
        self._runner = runner
        self._db_ready = db_ready

    async def run(self, conversation_id: uuid.UUID, content: str, send: Send) -> None:
        run_id = uuid.uuid4()
        await self._start_run(conversation_id, run_id, content)
        await send({"type": "run_started", "run_id": str(run_id), "timestamp": _now_iso()})

        final_response: str | None = None
        error: str | None = None
        try:
            async for event in self._runner.astream(
                thread_id=str(conversation_id), message=content
            ):
                wire = event.to_wire()
                wire["run_id"] = str(run_id)
                await send(wire)
                if event.type == EventType.MESSAGE and event.content:
                    final_response = event.content
                if event.type != EventType.TOKEN:  # tokens are too chatty to store
                    await self._store_event(run_id, event)
        except CancelledError:
            logger.info("Research run %s cancelled", run_id)
            await self._finish_run(run_id, status="cancelled", error="Stopped by user")
            await send(
                {
                    "type": "run_cancelled",
                    "run_id": str(run_id),
                    "error": "Stopped by user",
                    "timestamp": _now_iso(),
                }
            )
            return
        except Exception as exc:
            logger.exception("Research run %s failed", run_id)
            error = str(exc)

        if error is None and final_response is None:
            error = "The workflow finished without producing a response."

        if error is not None:
            await self._finish_run(run_id, status="failed", error=error)
            await send(
                {"type": "run_failed", "run_id": str(run_id), "error": error, "timestamp": _now_iso()}
            )
            return

        await self._store_message(conversation_id, "assistant", final_response)
        await self._finish_run(run_id, status="completed")
        await send({"type": "run_completed", "run_id": str(run_id), "timestamp": _now_iso()})

    # -- persistence (best-effort) -------------------------------------------

    async def _start_run(self, conversation_id: uuid.UUID, run_id: uuid.UUID, content: str) -> None:
        if not self._db_ready:
            return
        try:
            async with SessionLocal() as session:
                conversation = await session.get(Conversation, conversation_id)
                if conversation is None:
                    conversation = Conversation(id=conversation_id)
                    session.add(conversation)
                if not conversation.title:
                    conversation.title = content[:120]
                session.add(
                    Message(conversation_id=conversation_id, role="user", content=content)
                )
                session.add(ResearchRun(id=run_id, conversation_id=conversation_id))
                await session.commit()
        except Exception:
            logger.warning("Could not persist run start", exc_info=True)

    async def _store_message(self, conversation_id: uuid.UUID, role: str, content: str) -> None:
        if not self._db_ready:
            return
        try:
            async with SessionLocal() as session:
                session.add(
                    Message(conversation_id=conversation_id, role=role, content=content)
                )
                await session.commit()
        except Exception:
            logger.warning("Could not persist %s message", role, exc_info=True)

    async def _store_event(self, run_id: uuid.UUID, event: AgentEvent) -> None:
        if not self._db_ready:
            return
        try:
            async with SessionLocal() as session:
                session.add(
                    RunEvent(
                        run_id=run_id,
                        type=str(event.type),
                        agent=event.agent,
                        payload=event.to_wire(),
                    )
                )
                await session.commit()
        except Exception:
            logger.warning("Could not persist run event", exc_info=True)

    async def _finish_run(self, run_id: uuid.UUID, status: str, error: str | None = None) -> None:
        if not self._db_ready:
            return
        try:
            async with SessionLocal() as session:
                result = await session.execute(
                    select(ResearchRun).where(ResearchRun.id == run_id)
                )
                run = result.scalar_one_or_none()
                if run is not None:
                    run.status = status
                    run.error = error
                    run.finished_at = datetime.now(timezone.utc)
                    await session.commit()
        except Exception:
            logger.warning("Could not persist run completion", exc_info=True)
