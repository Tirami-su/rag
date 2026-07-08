import json
import time
import provider


def rewrite(doc, chunk):
    config = provider.config["qwen3.5-flash"]
    client = config.client

    completion = client.chat.completions.create(  # type: ignore
        model=config.model,
        messages=[
            {"role": "system", "content": "你是一个文档分析助手，擅长从文档中提取片段的背景信息，输出简洁的上下文描述。"},
            {
                "role": "user",
                "content": f"""
请为下面从完整文档中截取的段落生成一段**上下文**，用于补充该段落缺失的背景信息，使其在独立使用时也能被完整理解。上下文应包括但不限于以下方面：
* 来源信息：所属的文档名称、章节标题、列表序号等。
* 主题概括：对该切片核心内容的精炼总结。
* 歧义消除：明确代词（如“它”、“该公司”）的具体指向。

例子
段落：该公司的收入比上一季度增长了3%。
上下文：这一块来自美国证券交易委员会提交的关于ACME公司2023年第二季度业绩的文件；上一季度的收入为3.14亿美元

完整文档
<document>
    {doc}
</document>

待处理的段落
<chunk>
    {chunk["content"]}
</chunk>

只回答简洁的上下文，用自然连贯的句子表示，不要用列表或编号，不输出原段落，不要包含其他说明。
""",
            },
        ],
        temperature=0.2,
        top_p=0.95,
    )

    return completion.choices[0].message.content


if __name__ == "__main__":
    file = "dataset/doc2.md"
    json_file = file[:-2] + "json"

    with open(json_file, "r", encoding="utf-8") as f:
        json_content = json.load(f)
        chunks = json_content["chunks"]

    with open(file, "r", encoding="utf-8") as f:
        doc = f.read()

    for i, chunk in enumerate(chunks):
        print(f"\n--- 改写第 {i + 1}/{len(chunks)} 段: {' > '.join(chunk['path'])} ---")
        rewritten = rewrite(doc, chunk)
        chunk["rewritten_content"] = f"{rewritten}\n{chunk['content']}"
        time.sleep(0.5)  # 避免触发限流

    json_content["chunks"] = chunks

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_content, f, ensure_ascii=False, indent=2)
