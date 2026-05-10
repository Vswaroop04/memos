from __future__ import annotations

from datetime import datetime, timezone
from typing import TypedDict

from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from core.embedder import embed
from db.chroma import _get_collection

_reranker: CrossEncoder | None = None


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        # ~80MB model, loaded once and reused across all requests
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker


class Source(TypedDict):
    text: str
    source: str
    date: str
    score: float


def _build_date_filter(days: int | None) -> dict | None:
    # ChromaDB $gte filter on ingested_at (stored as Unix epoch int in chroma.py)
    if days is None:
        return None
    cutoff = int(datetime.now(timezone.utc).timestamp()) - days * 86400
    return {"ingested_at": {"$gte": cutoff}}


def _dense_search(
    query_vector: list[float],
    top_k: int,
    date_filter: dict | None,
) -> list[dict]:
    # Fetch 2x what we need — RRF needs a wider pool to merge from
    collection = _get_collection()
    kwargs: dict = {
        "query_embeddings": [query_vector],
        "n_results": top_k * 2,
        "include": ["documents", "metadatas", "distances"],
    }
    if date_filter:
        kwargs["where"] = date_filter

    results = collection.query(**kwargs)

    docs      = results["documents"][0]      # chunk texts
    metas     = results["metadatas"][0]      # metadata dicts
    distances = results["distances"][0]      # cosine distance, lower = closer

    return [
        {"text": doc, "meta": meta, "distance": dist}
        for doc, meta, dist in zip(docs, metas, distances)
    ]


def _sparse_search(query: str, candidates: list[dict]) -> list[tuple[int, float]]:
    # BM25 over the dense candidates — no separate index needed at this scale
    tokenized = [c["text"].lower().split() for c in candidates]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(query.lower().split())
    return list(enumerate(scores))


def _reciprocal_rank_fusion(
    dense_results: list[dict],
    bm25_scores: list[tuple[int, float]],
    k: int = 60,  # standard constant — dampens the outsized weight of rank 1
) -> list[dict]:
    # RRF: score(doc) = Σ 1/(k + rank_in_list)
    # Works across lists with incompatible score scales (distance vs BM25)
    dense_ranked  = sorted(range(len(dense_results)), key=lambda i: dense_results[i]["distance"])
    sparse_ranked = sorted(range(len(bm25_scores)),   key=lambda i: bm25_scores[i][1], reverse=True)

    rrf: dict[int, float] = {}
    for rank, idx in enumerate(dense_ranked):
        rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (k + rank + 1)
    for rank, idx in enumerate(sparse_ranked):
        rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (k + rank + 1)

    return [dense_results[i] for i in sorted(rrf, key=lambda i: rrf[i], reverse=True)]


def _rerank(query: str, candidates: list[dict], top_n: int) -> list[dict]:
    # Cross-encoder sees query + chunk together — catches negation/synonyms that
    # cosine similarity misses because it embeds query and chunk independently
    reranker = _get_reranker()
    pairs  = [(query, c["text"]) for c in candidates]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [c for c, _ in ranked[:top_n]]


def retrieve(
    query: str,
    top_k: int = 5,
    days: int | None = None,
) -> list[Source]:
    # Step 2: embed query into the same 1536-dim space as stored chunks
    query_vector = embed([query])[0]

    # Step 3a: dense retrieval via ChromaDB cosine similarity
    date_filter = _build_date_filter(days)
    dense = _dense_search(query_vector, top_k, date_filter)
    if not dense:
        return []

    # Steps 3b+3c: BM25 keyword scores + RRF merge
    bm25_scores = _sparse_search(query, dense)
    merged      = _reciprocal_rank_fusion(dense, bm25_scores)

    # Step 4: cross-encoder rerank, keep top_k
    reranked = _rerank(query, merged, top_n=top_k)

    return [
        Source(
            text=chunk["text"],
            source=str(chunk["meta"].get("source", "unknown")),
            date=str(chunk["meta"].get("ingested_at", "")),
            score=float(chunk.get("distance", 0.0)),
        )
        for chunk in reranked
    ]
