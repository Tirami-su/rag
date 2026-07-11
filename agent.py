import json
import os
from typing import List
from typing import AsyncGenerator

from chunk_search import search
import provider

from openai.types.chat import ChatCompletionToolParam, ChatCompletionMessageParam, ChatCompletionMessage

func_name = "inner_knowledge_search"

tools: List[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": func_name,
            "strict": True,
            "description": "搜索公司内部知识库，查询产品文档、技术文档、公司规章、项目进度、业务数据等等。支持批量查询，一次可提交多个搜索关键词",
            "parameters": {
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "description": "搜索关键词列表，每个关键词会独立搜索并返回各自的结果。例如用户问'A和B有什么区别'时，传入['A', 'B', 'A和B的区别']可以一次性获取全面信息",
                        "items": {
                            "type": "string",
                            "description": "单个优化后的搜索关键词",
                        },
                        "minItems": 1,
                        "maxItems": 5,
                    },
                },
                "required": ["queries"],
                "additionalProperties": False,
            },
        },
    }
]

system_prompt = f"""
你是一个企业的智能助手。你可以使用 `{func_name}` 工具来查询企业内部知识库。

## 工具调用准则
1. **何时调用**: 仅当用户问题涉及产品细节、公司规定、项目进度、数据、内部流程或你不确定答案时，必须调用工具。
2. **何时不调用**:
   - 用户问题和企业内部知识无关，比如只是打招呼
   - 上下文中已经包含了回答问题所需的全部信息
3. **批量查询优先**: `{func_name}` 支持批量查询。在调用工具前：
   - 将用户问题拆解为多个关键词或子问题，放入 `queries` 数组一次性提交
   - 例如：比较类问题（"A和B的区别"）应拆为 ['A', 'B', 'A和B的区别']
   - 例如：多方面问题（"项目X的进度、风险和预算"）应拆为 ['项目X进度', '项目X风险', '项目X预算']
   - 对于单一明确的问题，可以只传1个关键词
   - 单次最多5个关键词，避免过于宽泛
4. **补充查询**: 如果第一次批量查询的结果不够充分，可以再调用一次工具，使用更精确或补充的关键词。
5. **查询次数限制**: 如果查询次数达到限制，请根据已经获得的信息回答，不要继续调用工具。
6. **拒绝回答**: 如果查询不到有用信息，请诚实告知用户，不要编造。

## 回答风格
- 基于搜索结果回答时，必须在句末标记引用的片段的id，用<source_id></source_id>标记，比如<source_id>123</source_id>。
- 保持简洁专业。

如果用户问题与上述范围无关，且不是问候（例如：闲聊、生活常识、外部新闻、个人建议、非本企业的信息咨询），**必须**直接输出以下固定模板，**然后停止一切后续推理和工具调用**：
“抱歉，我是企业内部知识助手，仅能回答与本公司业务相关的问题。您的问题不在我的服务范围内。”
"""


config = provider.config["glm-4.7-flash"]
client = config.client


def load_conversation_history(session_id: str) -> List[ChatCompletionMessageParam]:
    """加载指定session的对话历史"""
    history_file = f"history/{session_id}.jsonl"
    if not os.path.exists(history_file):
        return []

    history = []
    with open(history_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                history.append(json.loads(line))
    return history


def append_to_conversation_history(session_id: str, messages: List[ChatCompletionMessageParam]):
    """追加新的对话历史到文件"""
    os.makedirs("history", exist_ok=True)
    history_file = f"history/{session_id}.jsonl"

    # 只追加非system消息
    new_messages = [msg for msg in messages if msg["role"] != "system"]

    with open(history_file, "a", encoding="utf-8") as f:
        for msg in new_messages:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")


def run_agent(new_message: str, session_id: str) -> str | None:
    """运行RAG Agent，支持对话历史持久化"""

    # 初始化消息列表
    messages: List[ChatCompletionMessageParam] = [{"role": "system", "content": system_prompt}]

    # 如果有session_id，加载历史对话
    if session_id:
        history = load_conversation_history(session_id)
        messages.extend(history)

    # 添加当前用户消息
    user_message: ChatCompletionMessageParam = {"role": "user", "content": new_message}
    messages.append(user_message)

    counter = 2
    append_user_message = False

    while counter > -1:
        response = client.chat.completions.create(  # type: ignore
            model=config.model,
            messages=messages,
            tools=tools,
            tool_choice="auto" if counter > 0 else "none",
            # stream=True,
            extra_body={
                "thinking": {
                    "type": "enabled",
                },
            },
        )

        msg = response.choices[0].message
        messages.append(msg.model_dump())  # type: ignore
        if not append_user_message:
            append_to_conversation_history(session_id, [user_message])
            append_user_message = True
        append_to_conversation_history(session_id, [msg.model_dump()])  # type: ignore

        print(msg)
        reasoning = getattr(msg, "reasoning_content", None)
        if reasoning:
            print("\nreasoning=> ", reasoning)
        print("\ncompletion=> ", msg.content)

        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                counter -= 1
                if tool_call.function.name == func_name:  # type: ignore
                    # 执行搜索
                    search_query: list[str] = json.loads(tool_call.function.arguments)["queries"]  # type: ignore
                    print("调用工具", search_query)
                    search_results = search(search_query, top_k=4)
                    dict_results = {query: results for query, results in zip(search_query, search_results)}

                    # 将工具结果追加到消息历史
                    tool_message: ChatCompletionMessageParam = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(dict_results),
                    }
                    messages.append(tool_message)
                    append_to_conversation_history(session_id, [tool_message])
        else:
            return msg.content


# run_agent("有哪些模型")
# run_agent("“nebula-code-v2模型的QPS上限是多少？企业租户调用它有什么特殊优惠？”")
# run_agent("请假要提前几天","1")


async def run_agent_async(new_message: str, session_id: str) -> AsyncGenerator[dict, None]:
    """运行RAG Agent（异步流式输出版本），支持对话历史持久化"""

    # 初始化消息列表
    messages: List[ChatCompletionMessageParam] = [{"role": "system", "content": system_prompt}]

    # 如果有session_id，加载历史对话
    if session_id:
        history = load_conversation_history(session_id)
        messages.extend(history)

    # 添加当前用户消息
    user_message: ChatCompletionMessageParam = {"role": "user", "content": new_message}
    messages.append(user_message)

    counter = 2
    append_user_message = False

    while counter > -1:
        # 异步流式请求
        stream = client.chat.completions.create(  # type: ignore
            model=config.model,
            messages=messages,
            tools=tools,
            tool_choice="auto" if counter > 0 else "none",
            stream=True,  # 启用流式输出
            extra_body={
                "thinking": {
                    "type": "enabled",
                },
            },
        )

        # 收集流式响应的完整消息
        collected_content = ""
        reasoning_content = ""
        collected_tool_calls = {}

        # 处理流式响应
        for chunk in stream:
            if chunk.choices[0].finish_reason:
                break

            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            yield delta.model_dump()

            if delta.content:
                collected_content += delta.content

            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                reasoning_content += reasoning  # type: ignore

            # 处理工具调用（只输出工具调用信息，不输出工具调用结果）
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    # 新的工具调用
                    if tool_call_delta.index not in collected_tool_calls:
                        collected_tool_calls[tool_call_delta.index] = {
                            "id": tool_call_delta.id or "",
                            "type": "function",
                            "function": {
                                "name": tool_call_delta.function.name if tool_call_delta.function else "",
                                "arguments": tool_call_delta.function.arguments if tool_call_delta.function else "",
                            },
                        }
                    elif tool_call_delta.function:
                        if tool_call_delta.function.name:
                            collected_tool_calls[tool_call_delta.index]["function"]["name"] += tool_call_delta.function.name
                        if tool_call_delta.function.arguments:
                            collected_tool_calls[tool_call_delta.index]["function"]["arguments"] += tool_call_delta.function.arguments

        # 构建完整的消息对象
        msg = ChatCompletionMessage(
            role="assistant",
            content=collected_content,
            reasoning_content=reasoning_content,  # type: ignore
            tool_calls=list(collected_tool_calls.values()),
        )

        messages.append(msg.model_dump())  # type: ignore

        if not append_user_message:
            append_to_conversation_history(session_id, [user_message])
            append_user_message = True
        append_to_conversation_history(session_id, [msg.model_dump()])  # type: ignore

        print(msg)
        reasoning = getattr(msg, "reasoning_content", None)
        if reasoning:
            print("\nreasoning=> ", reasoning)
        print("\ncompletion=> ", msg.content)  # type: ignore

        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                counter -= 1
                if tool_call.function.name == func_name:  # type: ignore
                    # 执行搜索
                    search_query: list[str] = json.loads(tool_call.function.arguments)["queries"]  # type: ignore
                    search_results = search(search_query, top_k=4)
                    dict_results = {query: results for query, results in zip(search_query, search_results)}

                    # 将工具结果追加到消息历史
                    tool_message: ChatCompletionMessageParam = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(dict_results),
                    }
                    messages.append(tool_message)
                    append_to_conversation_history(session_id, [tool_message])
        else:
            return


if __name__ == "__main__":
    run_agent("有什么模型", "2")
