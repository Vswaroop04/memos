from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]


@router.post("/", response_model=QueryResponse)
async def query(body: QueryRequest):
    # TODO: embed question → retrieve from chroma → generate answer with LLM
    return QueryResponse(answer="placeholder", sources=[])
