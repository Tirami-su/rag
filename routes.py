from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models import ChatRequest, HistoryResponse
from services import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/api/chat")
async def chat(request: ChatRequest):
    """
    聊天接口

    支持流式和非流式两种模式，通过session_id管理会话
    """
    try:
        # 返回流式响应
        return StreamingResponse(chat_service.stream_chat(request.message, request.session_id), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """
    获取会话历史

    返回指定session_id的完整对话历史
    """
    try:
        import json
        import os

        history_file = f"history/{session_id}.jsonl"
        if not os.path.exists(history_file):
            return HistoryResponse(session_id=session_id, messages=[], total_count=0)

        messages = []
        with open(history_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    messages.append(json.loads(line))

        return HistoryResponse(session_id=session_id, messages=messages, total_count=len(messages))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
