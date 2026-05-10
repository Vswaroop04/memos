"""
End-to-end pipeline test: ingest a few text chunks, then query them.
Runs directly against the local services (postgres/chroma/redis on localhost).
Uses a well-known open-source text: a short excerpt from Wikipedia's "Python (programming language)" article.
"""

import os
import sys
import uuid
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

SAMPLE_TEXT = """
Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code
readability, with the use of significant indentation. Python is dynamically typed and garbage-collected.
It supports multiple programming paradigms, including structured, object-oriented and functional programming.

Python was created by Guido van Rossum and first released in 1991. The language grew in popularity
through the 1990s and 2000s, largely due to its simple syntax, which made it accessible to beginners
while still being powerful enough for professionals.

Python 3.0 was released in December 2008, introducing several breaking changes from Python 2.
It improved Unicode support, changed print from a statement to a function, and made integer division
return a float by default. Python 2 reached end-of-life in 2020.

The Python Package Index (PyPI) is the official repository for third-party Python packages.
As of 2024, PyPI hosts more than 500,000 packages. Tools like pip are used to install packages
from PyPI, making it straightforward to add libraries to a Python project.

Python is widely used in data science, machine learning, web development, automation, and scientific computing.
Popular libraries include NumPy, pandas, scikit-learn, TensorFlow, Django, and Flask.
"""


def step(label):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")


def main():
    doc_id = str(uuid.uuid4())
    source = "wikipedia:python_language"

    step("1. Chunking text")
    from core.chunker import chunk
    chunks = chunk(SAMPLE_TEXT)
    print(f"  Produced {len(chunks)} chunks")
    for c in chunks:
        print(f"    [{c['index']}] ({c['type']}) {c['text'][:60].strip()!r}...")

    step("2. Embedding chunks with OpenAI text-embedding-3-small")
    from core.embedder import embed
    texts = [c["text"] for c in chunks]
    embeddings = embed(texts)
    print(f"  Got {len(embeddings)} embeddings, dim={len(embeddings[0])}")

    step("3. Storing in ChromaDB")
    from db.chroma import store
    store(doc_id, chunks, embeddings, source)
    print(f"  Stored {len(chunks)} chunks for doc_id={doc_id}")

    step("4. Saving document record in Postgres")
    from db.postgres import save_document, update_status
    saved_id = save_document(source=source, source_type="text")
    update_status(saved_id, "done")
    print(f"  Document saved: id={saved_id}, status=done")

    step("5. Retrieval test (hybrid BM25 + dense + rerank)")
    from core.retriever import retrieve

    questions = [
        "Who created Python and when was it first released?",
        "What is PyPI and how many packages does it have?",
        "What changed in Python 3 compared to Python 2?",
    ]

    for q in questions:
        print(f"\n  Q: {q}")
        sources = retrieve(q, top_k=2)
        if not sources:
            print("  [no results]")
        else:
            for i, s in enumerate(sources):
                print(f"  [{i+1}] score={s['score']:.4f} | {s['text'][:80].strip()!r}")

    step("6. Full RAG answer generation")
    from core.generator import generate
    question = "Who created Python and what is PyPI?"
    sources = retrieve(question, top_k=3)
    answer = generate(question, sources)
    print(f"\n  Q: {question}")
    print(f"\n  A: {answer}")
    print(f"\n  Sources used:")
    for s in sources:
        print(f"    - {s['source']} | {s['text'][:60].strip()!r}")

    print("\n\n✓ All steps passed.\n")


if __name__ == "__main__":
    main()
