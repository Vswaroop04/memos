# MEMOS

The Idea is to build a RAG that Ingests PersonalNotes/PersonalKB into a Vector DB allowing you to query and retrieve information from your own personal knowledge.

I built this without using any AI tool just like old times pure research and building.

##  History

A few days ago I built the simplest possible RAG system just to make sure I fully experiment the core concepts. It was probably around 50 lines of Python. Since then I have been experimenting with different parts of the stack and testing different approaches to see what works best.

Now I am trying to take it beyond the prototype stage and think more about how to make it production-friendly.

### Stack and why I choose what -

1. Fast API - The idea is to build this fast so Fast api felt like a good option
2. Vector DB 
So I researched a lot on this 
a. FAISS - Free and Fast to set it up but no persistence out of the box. I had to save/load the index manually. Fine for prototyping, annoying for production
b. LocalChromaDB - Simple, embedded mode, Not scalable 
c. Qdrant - Rust based so super fast but smaller community
d. Zilliz - Built for massive scale but complex to setup
I decided to go with Chroma DB because of its ease of use
3. Postgresql - to store metadata
4. Chunking - Went with Hybrid Chunking over only Semantic Chunking and Fixed size chunking to get the better match at retrieval
5. Retrieval - Dense (Semantic) vs Sparse (BM25 && only keyword search) vs Hybrid 
I decided to go with Hybrid as it is perfect for my usecase
6. Reranking(cross-encoder/ms-marco-MiniLM-L-6-v2 from HuggingFace) - The game changer When i implemented it in the prototype stage I almost didn't implement reranking. "Initial retrieval is good enough," I thought. Then I tried it the reranking among the docs increased accuracy from 70 to 85%
7. Embedding Model
text-embedding-3-large (OpenAI) - 1536 dims, excellent quality
embed-v4 or voyage-large-2 (latest) - 1536dms (default), Best openai alternative
all-MiniLM-L6-v2 (open source) - 384 dims, fast, good enough
bge-large-en-v1.5 or bge-m3 (BAAI) - 1024 dims, top open source options
I am going with text-embedding-3-small as it will give me 95% of the quality at a fraction of the cost
8. As for LLM there are lot of options I am going with GPT-4o-mini as its cheap and sufficient enough for my usecase
9. Chunking Strategy: The main issue with my use case is that a lot of the documents contain structured tables. Converting everything into plain text loses too much context, so I’m trying to preserve the structure as much as possible.

Right now the pipeline I’m thinking about is:
extract text → detect and preserve tables in Markdown format → split into chunks with overlap → retain metadata for retrieval.

## Setup

Copy .env.example to .env and fill in the values. You need an OpenAI key, a running Postgres instance, Redis, and Chroma. The docker-compose.yml spins up Postgres, Redis, and Chroma so you do not have to set those up manually.

```
cp .env.example .env
docker compose up -d
pip install -r requirments.txt
alembic upgrade head
uvicorn api.main:app --reload
```

That is it. Two endpoints are all you need to use this.

POST /ingest/text or /ingest/pdf or /ingest/url to push something into the knowledge base, and POST /query to ask a question against everything you have ingested. The ingest side queues the work through Celery so it returns immediately and processes in the background.

```bash
# ingest a quick note
curl -X POST http://localhost:8000/ingest/text \
  -H "Content-Type: application/json" \
  -d ‘{"text": "The mitochondria is the powerhouse of the cell", "title": "bio-notes"}’

# ingest a PDF
curl -X POST http://localhost:8000/ingest/pdf \
  -F "file=@/path/to/notes.pdf"

# ingest a URL
curl -X POST http://localhost:8000/ingest/url \
  -H "Content-Type: application/json" \
  -d ‘{"url": "https://example.com/article"}’

# query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d ‘{"question": "what do I know about mitochondria", "top_k": 5}’
```

If you only want results from the last week you can pass days as well.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d ‘{"question": "what do I know about mitochondria", "top_k": 5, "days": 7}’
```
