from pymilvus import AnnSearchRequest, MilvusClient, RRFRanker
import provider
import dashscope
from http import HTTPStatus

dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"


def text_rerank(query: str, chunks: list[str]) -> list[int]:
    resp = dashscope.TextReRank.call(
        model="qwen3-rerank",
        query=query,
        documents=chunks,
        top_n=10,
        instruct="Given a web search query, retrieve relevant passages that answer the query.",
    )
    print(resp)
    if resp.status_code == HTTPStatus.OK:
        return [i["index"] for i in resp.output.results]
    else:
        return []


db = MilvusClient("./milvus_demo.db")
collection_name = "my_collection"
db.load_collection(collection_name=collection_name)
print(db.get_collection_stats(collection_name=collection_name))


def search(queries: list[str], top_k: int = 5) -> list[list[dict]]:
    embedding_config = provider.config["qwen-embedding"]
    embedding_client = embedding_config.client

    embedding_result = embedding_client.embeddings.create(  # type: ignore
        model=embedding_config.model,
        input=queries,
    ).data
    queries_embeddings = [item.embedding for item in embedding_result]
    print([len(item) for item in queries_embeddings])

    search_param_1 = {
        "data": queries_embeddings,
        "anns_field": "text_dense",
        "param": {"nprobe": 3},
        "limit": top_k,
    }

    search_param_2 = {
        "data": queries,
        "anns_field": "text_sparse",
        "param": {},
        "limit": top_k,
    }

    res = db.hybrid_search(
        collection_name=collection_name,
        filter="category == '技术'",
        reqs=[AnnSearchRequest(**search_param_1), AnnSearchRequest(**search_param_2)],
        ranker=RRFRanker(),
        limit=top_k * 2,
        output_fields=["text"],
    )

    for i, hits in enumerate(res):
        print(f"\nTopK results for query {i} {queries[i]}:")
        for hit in hits:
            print(hit)

    result = []
    for i, hits in enumerate(res):
        chunks = [hits[i]["entity"]["text"] for i in range(len(hits))]
        result_idx = text_rerank(queries[i], chunks)
        result.append([hits[i]["entity"] for i in result_idx[:top_k]])
    for i, hits in enumerate(result):
        print(f"\nTopK results for query {i} {queries[i]}:")
        for hit in hits:
            print(hit)
    return result


if __name__ == "__main__":
    search(["请假", "报销"], top_k=4)
