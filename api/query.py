from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.retriever import retrieve, Source
from core.generator import generate

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    days: int | None = None   # e.g. 7 → only chunks from the last 7 days


class SourceOut(BaseModel):
    text: str
    source: str
    date: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceOut]


@router.post("/", response_model=QueryResponse)
async def query(body: QueryRequest):
    # Step 3+4: hybrid retrieval + rerank
    sources: list[Source] = retrieve(
        query=body.question,
        top_k=body.top_k,
        days=body.days,
    )

    if not sources:
        raise HTTPException(status_code=404, detail="No relevant notes found.")

    # Step 6: generate answer from retrieved chunks
    answer = generate(body.question, sources)

    # Step 7: return answer + sources for attribution
    return QueryResponse(
        answer=answer,
        sources=[
            SourceOut(text=s["text"], source=s["source"], date=s["date"])
            for s in sources
        ],
    )
