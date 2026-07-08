import traceback
from typing import AsyncGenerator
import json

from agent import run_agent_async

from models import generate_session_id


class ChatService:
    async def stream_chat(self, message: str, session_id: str | None) -> AsyncGenerator[str, None]:
        """
        流式聊天生成器
        注意：yield 的内容必须是 str 或 bytes
        """
        # 如果没有提供session_id，生成一个新的
        if not session_id:
            session_id = generate_session_id()

        try:
            # 模拟从 LLM API 获取流式响应
            # 实际场景中替换为 openai / anthropic 等 SDK 的 async stream
            async for chunk in run_agent_async(message, session_id):
                # ✅ SSE 协议格式：以 "data: " 开头，以 "\n\n" 结尾
                data = json.dumps(
                    {
                        "content": chunk["content"],
                        "reasoning_content": chunk.get("reasoning_content"),
                        "tool_calls": chunk["tool_calls"],
                        "session_id": session_id,
                        "done": False,
                    },
                    ensure_ascii=False,
                )
                yield f"data: {data}\n\n"

            # ✅ 发送结束标记
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            traceback.print_exc()
            # ✅ 错误也要通过 SSE 格式返回，不要直接抛异常
            error_data = json.dumps({"error": str(e), "done": True})
            yield f"data: {error_data}\n\n"
