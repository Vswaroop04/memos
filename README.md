# MEMOS

The Idea is to build a RAG that Ingests PersonalNotes/PersonalKB into a Vector DB allowing you to query and retrieve information from your own personal knowledge.

I want to build this without using any AI tool just like old times research and build

##  History

A few days ago I built the simplest possible RAG system just to make sure I fully experiment the core concepts. It was probably around 50 lines of Python. Since then I’ve been experimenting with different parts of the stack and testing different approaches to see what works best.

Now I’m trying to take it beyond the prototype stage and think more about how to make it production-friendly.

Stack -

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
