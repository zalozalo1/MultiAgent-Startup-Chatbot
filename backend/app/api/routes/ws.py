"""WebSocket endpoint for the live research chat.

Protocol:
    client -> server: {"type": "chat", "content": "<user message>"}
    server -> client: run_started, then AgentEvents (workflow_started,
                      agent_started, handoff, tool_*, token, message,
                      agent_completed, ...), then run_completed | run_failed.

The conversation id doubles as the AI thread id, so reconnecting with the
same id continues the same research context.
"""

import logging
import uuid
from asyncio import Task, create_task

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["chat"])

logger = logging.getLogger(__name__)


@router.websocket("/ws/conversations/{conversation_id}")
async def chat_socket(websocket: WebSocket, conversation_id: uuid.UUID) -> None:
    await websocket.accept()
    current_run: Task | None = None

    def log_task_error(task: Task) -> None:
        if task.cancelled():
            return
        try:
            task.result()
        except Exception:
            logger.exception("Research task failed outside normal run handling")

    try:
        while True:
            data = await websocket.receive_json()
            if not isinstance(data, dict):
                await websocket.send_json(
                    {"type": "run_failed", "error": "Expected a JSON object"}
                )
                continue

            message_type = data.get("type")
            if message_type == "stop":
                if current_run is not None and not current_run.done():
                    current_run.cancel()
                continue

            if message_type != "chat":
                await websocket.send_json(
                    {
                        "type": "run_failed",
                        "error": "Expected {'type': 'chat', 'content': ...} or {'type': 'stop'}",
                    }
                )
                continue

            if current_run is not None and not current_run.done():
                await websocket.send_json(
                    {"type": "run_failed", "error": "A research run is already in progress."}
                )
                continue

            content = (data.get("content") or "").strip()
            if not content:
                continue

            service = websocket.app.state.research_service
            if service is None:
                await websocket.send_json(
                    {
                        "type": "run_failed",
                        "error": websocket.app.state.workflow_error
                        or "AI engine is not available. Check the backend configuration.",
                    }
                )
                continue

            # Runs sequentially; further client messages queue on the socket
            # until the current run finishes or the client sends stop.
            current_run = create_task(
                service.run(conversation_id, content, websocket.send_json)
            )
            current_run.add_done_callback(log_task_error)
    except WebSocketDisconnect:
        if current_run is not None and not current_run.done():
            current_run.cancel()
        logger.debug("Client disconnected from conversation %s", conversation_id)
