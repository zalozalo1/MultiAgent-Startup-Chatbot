from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health(request: Request) -> dict:
    ai_error = getattr(request.app.state, "workflow_error", None)
    return {
        "status": "ok",
        "database": "up" if request.app.state.db_ready else "down",
        "ai_engine": "ready" if request.app.state.research_service else "unavailable",
        "ai_engine_error": ai_error,
    }
