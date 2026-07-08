# RAG Agent API 接口文档

## 概述
RAG Agent API 是一个企业内部知识库助手接口，支持流式和非流式两种聊天模式。

## 基础信息
- **基础URL**: `http://localhost:8000`
- **内容类型**: `application/json`
- **流式响应**: `text/event-stream`

## 接口列表

### 1. 聊天接口

**POST** `/api/chat`

#### 请求参数
```json
{
    "message": "用户问题",
    "session_id": "可选的会话ID，不传则创建新会话"
}
```

#### 响应

**非流式响应**（当前版本默认流式）
```json
{
    "response": "回答内容",
    "session_id": "会话ID",
    "source_ids": ["源ID列表"],
    "timestamp": "2026-07-07T20:30:00Z"
}
```

**流式响应（SSE）**
```
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: response
data: {"type": "content", "content": "这是回答内容的第一部分"}

event: response
data: {"type": "content", "content": "这是回答内容的第二部分"}

event: tool_calls
data: {"type": "tool_calls", "queries": ["关键词1", "关键词2"]}

event: tool_results
data: {"type": "tool_results", "results_count": 4}

event: done
data: {"type": "done", "session_id": "32位会话ID", "source_ids": ["123", "456"]}
```

#### 响应事件类型说明
- `content`: 回答内容
- `tool_calls`: 工具调用，包含搜索关键词列表
- `tool_results`: 工具调用结果，返回结果数量
- `done`: 完成标志，包含会话ID和源ID列表
- `error`: 错误信息

### 2. 会话历史接口

**GET** `/api/sessions/{session_id}/history`

#### 路径参数
- `session_id`: 会话ID（32位字符串）

#### 响应
```json
{
    "session_id": "会话ID",
    "messages": [
        {
            "role": "user",
            "content": "用户消息"
        },
        {
            "role": "assistant",
            "content": "助手回复"
        },
        {
            "role": "tool",
            "tool_call_id": "xxx",
            "content": "工具调用结果"
        }
    ],
    "total_count": 3
}
```

### 3. 系统接口

**GET** `/`
返回API基本信息

**GET** `/health`
健康检查接口

## 使用示例

### Python 请求示例
```python
import requests

# 流式聊天
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "查询请假流程",
        "session_id": "可选的会话ID"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

### JavaScript 示例
```javascript
// 流式聊天
async function streamChat() {
    const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: '查询请假流程',
            session_id: '可选的会话ID'
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        console.log(chunk);
    }
}
```

### cURL 示例
```bash
# 流式聊天
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "查询请假流程", "session_id": "可选的会话ID"}' \
     --no-buffer
```

## Session ID 规则
- 格式：32位字母数字字符串
- 生成规则：UUID v4去掉连字符
- 示例：`f47ac10b58d4383655d0e6b7a1234567890123456`
- 验证规则：`^[a-zA-Z0-9]{32}$`

## 错误处理
- 400: 请求参数错误
- 500: 服务器内部错误
- 流式响应中的error事件包含错误详情

## 注意事项
1. 流式响应使用SSE格式，需要特殊处理
2. Session ID如果不传，服务器会自动生成新的
3. 会话历史保存在服务器的`history/`目录下
4. 过滤了模型的推理过程，只返回回答内容和工具调用结果