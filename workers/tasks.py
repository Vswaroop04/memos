import os
from celery import Celery
from celery.app.task import Task

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

app = Celery("workers", broker=REDIS_URL, backend=REDIS_URL)


@app.task(bind=True, max_retries=3)
def ingest_document(self: Task, document_id: str, text: str, source: str):
    from core.chunker import chunk
    from core.embedder import embed
    from db.chroma import store
    from db.postgres import update_status

    try:
        chunks = chunk(text)
        embeddings = embed([c["text"] for c in chunks])
        store(document_id, chunks, embeddings, source)
        update_status(document_id, "done")
    except Exception as exc:
        update_status(document_id, "failed")
        raise self.retry(exc=exc, countdown=5)


def dispatch_ingest(document_id: str, text: str, source: str) -> None:
    ingest_document.delay(document_id, text, source)  # pyright: ignore[reportFunctionMemberAccess]
