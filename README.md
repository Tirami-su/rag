# Knowledge RAG

一个 RAG Demo，模拟企业内部知识库的智能问答系统。覆盖从文档预处理、混合检索、Agentic 决策到 http 服务的完整链路。

## 技术要点

- **语义切分** 按照自然段落切分 chunk

- **Contextual Retrieval** 用模型给 chunk 补充上下文，指代消解，使其语义完整

- **混合检索** 语义检索 + BM25检索 + RRF融合排序 + Cross-Encoder重排序

- **Agentic RAG** 让模型判断是否需要查询、优化查询关键词、判断是否需要拆分成多个子查询，以及信息不足时判断是否需要再次查询

- **其他** 

    - 向量数据库使用 milvus

    - 模型没有使用最强模型，而是够用的便宜模型，优化成本

    - 流式输出模型返回的文本和工具调用

    - 对话历史持久化

    - 没有使用 langchain / langgraph 等框架

```
用户问题 → Agent 决策层
              ↓ 需要检索？
        优化搜索关键词/子查询
              ↓
    ┌─ 混合检索 ─────────────────────────────┐
    │  语义检索（Qwen Embedding, COSINE）     │
    │  + BM25 关键词检索（Milvus 内置）        │
    │  → RRF 融合排序（Milvus 内置）           │
    │  → Cross-Encoder 重排序（Qwen3-Rerank） │
    └───────────────────────────────────────┘
              ↓ 返回 top_k 片段
        模型综合生成回答（带 source_id 引用）
              ↓
        信息不足？→ 补充检索（最多 2 轮）
```

## 项目结构

```
├── main.py              # FastAPI 入口
├── routes.py            # /api/chat, /api/sessions/{id}/history
├── services.py          # ChatService，SSE 流式包装
├── models.py            # Pydantic 请求/响应模型
├── agent.py             # Agentic RAG 核心逻辑（同步 + 异步流式）
├── provider.py          # 多模型配置（GLM、Qwen、DeepSeek、MiniMax 等）
├── chunk_extract.py     # Markdown 语义解析器
├── chunk_rewrite.py     # Contextual Retrieval 上下文补全
├── chunk_embedding.py   # Qwen Embedding 向量化
├── chunk_search.py      # 混合检索 + RRF + Cross-Encoder 重排序
├── chunk.py             # Milvus Collection 创建 & 数据写入
├── api_docs/            # API 接口文档
├── dataset/             # 3 个示例文档
├── history/             # 对话历史持久化目录
├── experiment1.ipynb    # 交互式实验 Notebook
└── pyproject.toml       # uv 项目配置
```

## 结果表现

混合检索的召回率是 100%，但是因为数据集小，不太能说明什么。在做这个项目之前，我有尝试寻找公开数据集进行评测，但是我发现 RAG 数据集基本都是公网新闻，这和 RAG 现在的真实使用场景不同，因此没有采用

整个 Agentic RAG 的流程以及最终的回答也很理想，能够做到**判断是否需要查询、优化查询关键词、判断是否需要拆分成多个子查询、信息不足时判断是否需要再次查询、拒绝回答无关问题、查不到有效信息时不编造**等。这方面和模型本身能力以及 prompt 有关，在测试过程中能发现，有些模型的指令遵循能力不足，有时候会没有按照要求用`<source_id>`表示参考片段，或者给出了文章标题，如果换用更强的模型表现则会更好