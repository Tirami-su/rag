from pydantic import BaseModel, Field
from typing import Optional, List
import uuid


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID，不传则创建新会话")


class ChatResponse(BaseModel):
    """聊天响应模型（非流式）"""
    response: str = Field(..., description="回答内容")
    session_id: str = Field(..., description="会话ID")
    source_ids: List[str] = Field(default_factory=list, description="源ID列表")
    timestamp: str = Field(..., description="时间戳")


class SessionResponse(BaseModel):
    """会话响应模型"""
    session_id: str = Field(..., description="会话ID")
    message_count: int = Field(..., description="消息数量")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="最后更新时间")


class HistoryResponse(BaseModel):
    """历史记录响应模型"""
    session_id: str = Field(..., description="会话ID")
    messages: List[dict] = Field(..., description="消息历史")
    total_count: int = Field(..., description="总消息数")


def generate_session_id() -> str:
    """生成32位会话ID"""
    return str(uuid.uuid4()).replace('-', '')