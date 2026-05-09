from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

router = APIRouter()


class URLIngestRequest(BaseModel):
    url: str


@router.post("/pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    # TODO: pass to loader → chunker → embedder → store in chroma
    return {"filename": file.filename, "status": "queued"}


@router.post("/url")
async def ingest_url(body: URLIngestRequest):
    # TODO: pass to url loader → chunker → embedder → store in chroma
    return {"url": body.url, "status": "queued"}


@router.post("/text")
async def ingest_text(body: dict):
    # TODO: pass to text loader → chunker → embedder → store in chroma
    return {"status": "queued"}
