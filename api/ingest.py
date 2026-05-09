import tempfile
import os

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from db.postgres import save_document
from workers.tasks import dispatch_ingest

router = APIRouter()


class URLIngestRequest(BaseModel):
    url: str


class TextIngestRequest(BaseModel):
    text: str
    title: str = "untitled"


@router.post("/pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    filename = file.filename or "upload.pdf"
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    document_id = save_document(source=filename, source_type="pdf")

    contents = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        from loaders.pdf import load
        text = load(tmp_path)
    finally:
        os.unlink(tmp_path)

    dispatch_ingest(document_id, text, filename)
    return {"document_id": document_id, "status": "queued"}


@router.post("/url")
async def ingest_url(body: URLIngestRequest):
    from loaders.url import load
    try:
        text = load(body.url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    document_id = save_document(source=body.url, source_type="url")
    dispatch_ingest(document_id, text, body.url)
    return {"document_id": document_id, "status": "queued"}


@router.post("/text")
async def ingest_text(body: TextIngestRequest):
    from loaders.text import load
    text = load(body.text)
    if not text:
        raise HTTPException(status_code=400, detail="Text is empty")

    document_id = save_document(source=body.title, source_type="text")
    dispatch_ingest(document_id, text, body.title)
    return {"document_id": document_id, "status": "queued"}
