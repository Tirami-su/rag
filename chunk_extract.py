import json
import re
from typing import Any, Dict, List, Optional

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")


def _parse_heading(line: str) -> Optional[tuple[int, str]]:
    m = _HEADING_RE.match(line)
    if not m:
        return None
    return len(m.group(1)), m.group(2).strip()


_LIST_RE = re.compile(r"^(\s*)[-*+] (.+)$|^(\d+)\.\s+(.+)$")


def _parse_list_item(line: str) -> Optional[tuple[str, str]]:
    m = _LIST_RE.match(line)
    if not m:
        return None
    # unordered: (\s*)(-.*) -> indent, content
    # ordered: (\d+)\.(.*) -> indent, content
    indent = m.group(1) or m.group(3) or ""
    content = (m.group(2) or m.group(4)).rstrip()
    return indent, content


def parse_markdown_with_hierarchy(file_path: str) -> List[Dict[str, Any]]:
    """解析 Markdown 文件，返回带层级路径的正文块列表。"""
    chunks: List[Dict[str, Any]] = []
    headers: Dict[int, str] = {}
    pending: list[str] = []

    def _flush() -> None:
        nonlocal pending
        content = "\n".join(pending).strip()
        pending.clear()
        if content:
            chunks.append(
                {
                    "content": content,
                    "path": [v for _, v in sorted(headers.items())],
                }
            )

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            # 标题行 —— 先 flush 上文，再更新层级
            heading = _parse_heading(line)
            if heading is not None:
                _flush()
                level, text = heading
                if text:
                    headers = {k: v for k, v in headers.items() if k < level} | {level: text}
                continue

            # 检查是否是列表项，如果是，先 flush 当前段落
            if _parse_list_item(line) is not None:
                _flush()
                pending.append(line)
                continue

            # 空行分割段落
            if not line.strip():
                _flush()
                continue

            # 忽略 Setext 标题下划线（=== 或 ---），当作普通行处理即可
            # 正常正文/代码等
            pending.append(line)

    _flush()
    return chunks


if __name__ == "__main__":
    file = "dataset/doc2.md"

    chunks = parse_markdown_with_hierarchy(file)

    print(f"解析完成，共 {len(chunks)} 个块。\n")
    for i, chunk in enumerate(chunks):
        print(f"{i} {chunk['path']}")

    with open(file[:-2] + "json", "w", encoding="utf-8") as f:
        json.dump({"chunks": chunks, "category": "技术"}, f, ensure_ascii=False, indent=2)
