from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

from ..database import SessionLocal, Conversation, Message

router = APIRouter()


class UpdateTitleRequest(BaseModel):
    title: str


class FeedbackRequest(BaseModel):
    feedback: str  # like, dislike, null


@router.get("/")
async def list_conversations() -> dict:
    """获取会话列表（置顶的排在前面）"""
    db = SessionLocal()
    try:
        conversations = db.query(Conversation).order_by(
            Conversation.pinned.desc(),
            Conversation.updated_at.desc()
        ).all()
        return {
            "code": 0,
            "message": "获取成功",
            "data": [conv.to_dict() for conv in conversations]
        }
    finally:
        db.close()


@router.post("/")
async def create_conversation(title: str = "新对话") -> dict:
    """创建会话"""
    import uuid
    db = SessionLocal()
    try:
        conv = Conversation(
            id=str(uuid.uuid4()),
            title=title
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return {"code": 0, "message": "创建成功", "data": conv.to_dict()}
    finally:
        db.close()


# 注意：具体路径路由必须放在动态路径路由之前
@router.put("/{conversation_id}/title")
async def update_conversation_title(conversation_id: str, request: UpdateTitleRequest) -> dict:
    """更新会话标题（重命名）"""
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return {"code": 1, "message": "会话不存在"}
        
        conv.title = request.title
        db.commit()
        return {"code": 0, "message": "更新成功", "data": conv.to_dict()}
    finally:
        db.close()


@router.put("/{conversation_id}/pin")
async def pin_conversation(conversation_id: str) -> dict:
    """置顶会话"""
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return {"code": 1, "message": "会话不存在"}
        
        conv.pinned = 1
        db.commit()
        return {"code": 0, "message": "置顶成功", "data": conv.to_dict()}
    finally:
        db.close()


@router.put("/{conversation_id}/unpin")
async def unpin_conversation(conversation_id: str) -> dict:
    """取消置顶会话"""
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return {"code": 1, "message": "会话不存在"}
        
        conv.pinned = 0
        db.commit()
        return {"code": 0, "message": "取消置顶成功", "data": conv.to_dict()}
    finally:
        db.close()


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str) -> dict:
    """获取会话详情（包含消息列表）"""
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()
        
        return {
            "code": 0,
            "message": "获取成功",
            "data": {
                "conversation": conv.to_dict(),
                "messages": [msg.to_dict() for msg in messages]
            }
        }
    finally:
        db.close()


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str) -> dict:
    """删除会话"""
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return {"code": 1, "message": "会话不存在"}
        
        # 删除关联消息
        db.query(Message).filter(Message.conversation_id == conversation_id).delete()
        db.delete(conv)
        db.commit()
        return {"code": 0, "message": "删除成功"}
    finally:
        db.close()


@router.put("/messages/{message_id}/feedback")
async def update_message_feedback(message_id: int, request: FeedbackRequest) -> dict:
    """更新消息反馈（点赞/踩）"""
    db = SessionLocal()
    try:
        msg = db.query(Message).filter(Message.id == message_id).first()
        if not msg:
            return {"code": 1, "message": "消息不存在"}
        
        msg.feedback = request.feedback if request.feedback != "null" else None
        db.commit()
        return {"code": 0, "message": "反馈成功", "data": msg.to_dict()}
    finally:
        db.close()