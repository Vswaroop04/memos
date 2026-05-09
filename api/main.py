from fastapi import FastAPI
from api.ingest import router as ingest_router
from api.query import router as query_router

app = FastAPI(title="Memos API")

app.include_router(ingest_router, prefix="/ingest", tags=["ingest"])
app.include_router(query_router, prefix="/query", tags=["query"])


@app.get("/health")
def health():
    return {"status": "ok"}
