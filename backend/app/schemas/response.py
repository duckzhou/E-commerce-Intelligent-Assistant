from pydantic import BaseModel, Field
from typing import Optional, List, Any


class SourceItem(BaseModel):
    """引用来源"""
    text: str = Field(..., description="原文片段")
    score: float = Field(..., description="相关度分数")
    doc_id: Optional[str] = Field(None, description="文档ID")


class ChatResponseData(BaseModel):
    """聊天响应数据"""
    answer: str = Field(..., description="AI回答")
    sources: List[SourceItem] = Field(default_factory=list, description="引用来源")
    confidence: str = Field(..., description="置信度等级：high/medium/low")
    conversation_id: str = Field(..., description="会话ID")
    tokens_used: int = Field(default=0, description="Token消耗")
    retrieval_time_ms: float = Field(default=0, description="检索耗时(ms)")
    generation_time_ms: float = Field(default=0, description="生成耗时(ms)")
    total_time_ms: float = Field(default=0, description="总耗时(ms)")


class APIResponse(BaseModel):
    """统一API响应"""
    code: int = Field(0, description="错误码，0表示成功")
    message: str = Field("success", description="消息")
    data: Optional[Any] = Field(None, description="响应数据")


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    doc_id: int = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    chunks_count: int = Field(..., description="切分块数")
    category: Optional[str] = Field(None, description="标签分类")


class ConversationResponse(BaseModel):
    """会话响应"""
    id: str = Field(..., description="会话ID")
    title: Optional[str] = Field(None, description="会话标题")
    user_id: Optional[str] = Field(None, description="用户标识")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    messages: List[dict] = Field(default_factory=list, description="消息列表")


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误信息")