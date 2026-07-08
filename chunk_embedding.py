import json
import time
from typing import List
import provider


def embed(text) -> List[float]:
    emb_config = provider.config["qwen-embedding"]
    client = emb_config.client

    result = client.embeddings.create(  # type: ignore
        model=emb_config.model,
        input=text,
    )
    return result.data[0].embedding


if __name__ == "__main__":
    file = "dataset/doc3.md"
    json_file = file[:-2] + "json"

    with open(json_file, "r", encoding="utf-8") as f:
        json_content = json.load(f)
        chunks = json_content["chunks"]

    for i, chunk in enumerate(chunks):
        print(f"\n--- embedding 第 {i + 1}/{len(chunks)} 段: {' > '.join(chunk['path'])} ---")
        embedding = embed(chunk["rewritten_content"])
        chunk["embedding"] = embedding
        print(f"维度: {len(embedding)}")
        time.sleep(0.5)

    json_content["chunks"] = chunks

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_content, f, ensure_ascii=False, indent=2)
