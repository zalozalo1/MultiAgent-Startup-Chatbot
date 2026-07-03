import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.models import Conversation
from app.schemas.conversation import ConversationDetail, ConversationOut

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _require_db(request: Request) -> None:
    if not request.app.state.db_ready:
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    request: Request, session: AsyncSession = Depends(get_session)
):
    _require_db(request)
    result = await session.execute(
        select(Conversation).order_by(Conversation.updated_at.desc()).limit(100)
    )
    return result.scalars().all()


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    _require_db(request)
    result = await session.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    _require_db(request)
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await session.delete(conversation)
    await session.commit()
