from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """聊天请求"""
    query: str = Field(..., description="用户问题", min_length=1, max_length=2000)
    conversation_id: Optional[str] = Field(None, description="会话ID，用于多轮对话")
    category: Optional[str] = Field(None, description="文档标签过滤（如：薪酬/排班/平台规则）")


class ChatHistoryItem(BaseModel):
    """历史消息"""
    role: str = Field(..., description="角色：user/assistant")
    content: str = Field(..., description="消息内容")


class ChatWithContextRequest(ChatRequest):
    """带上下文的聊天请求"""
    history: Optional[List[ChatHistoryItem]] = Field(None, description="对话历史")


class DocumentUploadRequest(BaseModel):
    """文档上传请求（通过multipart/form-data）"""
    category: Optional[str] = Field(None, description="文档标签分类")


class ConversationCreateRequest(BaseModel):
    """创建会话请求"""
    title: Optional[str] = Field(None, description="会话标题")
    user_id: Optional[str] = Field(None, description="用户标识")