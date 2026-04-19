from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json

from ..services.chat_service import chat_service
from ..routers.auth import get_current_user
from ..database import User

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    context_messages: Optional[List[dict]] = []


@router.post("/")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """智能问答接口"""
    try:
        result = await chat_service.chat(
            query=request.query,
            conversation_id=request.conversation_id,
            context_messages=request.context_messages,
            user_id=current_user.id
        )
        return {"code": 0, "message": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """智能问答接口（流式输出）"""
    return StreamingResponse(
        chat_service.chat_stream(
            query=request.query,
            conversation_id=request.conversation_id,
            context_messages=request.context_messages,
            user_id=current_user.id
        ),
        media_type="text/event-stream"
    )


