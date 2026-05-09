import os
from typing import cast
import chromadb
from chromadb.api.types import Embeddings
from core.chunker import Chunk

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        host = os.environ.get("CHROMA_HOST", "localhost")
        port = int(os.environ.get("CHROMA_PORT", "8001"))
        _client = chromadb.HttpClient(host=host, port=port)
        _collection = _client.get_or_create_collection(
            name="memos",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def store(document_id: str, chunks: list[Chunk], embeddings: list[list[float]], source: str) -> None:
    collection = _get_collection()
    collection.add(
        ids=[f"{document_id}_{chunk['index']}" for chunk in chunks],
        embeddings=cast(Embeddings, embeddings),
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[
            {
                "document_id": document_id,
                "source": source,
                "chunk_index": chunk["index"],
                "chunk_type": chunk["type"],
            }
            for chunk in chunks
        ],
    )
