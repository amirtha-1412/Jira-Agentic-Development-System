"""
vectorstore/retrieval_routes.py
---------------------------------------------
FastAPI Retrieval Routes
Exposes semantic code search as REST endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from vectorstore.retriever import CodeRetriever

router = APIRouter(prefix="/retrieval", tags=["Semantic Retrieval"])

# ─── Singleton retriever ──────────────────────
_retriever: CodeRetriever = None

def get_retriever() -> CodeRetriever:
    global _retriever
    if _retriever is None:
        _retriever = CodeRetriever()
    return _retriever


# ─────────────────────────────────────────────
# POST /retrieval/search
# ─────────────────────────────────────────────

class SearchRequest(BaseModel):
    query:      str
    top_k:      int   = 5
    min_sim:    float = 0.20
    ext_filter: str   = None

@router.post("/search", summary="Semantic code search")
async def semantic_search(body: SearchRequest):
    """
    Performs semantic search over the indexed repository.
    Returns ranked code chunks most relevant to the query.
    """
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    retriever = get_retriever()

    if not retriever.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Vector store not indexed. POST /retrieval/index first."
        )

    results = retriever.search(
        query      = body.query,
        top_k      = body.top_k,
        min_sim    = body.min_sim,
        ext_filter = body.ext_filter,
    )

    return {
        "success":  True,
        "query":    body.query,
        "count":    len(results),
        "results":  [r.to_dict() for r in results],
    }


# ─────────────────────────────────────────────
# GET /retrieval/context
# ─────────────────────────────────────────────

@router.get("/context", summary="Get LLM-ready context for a query")
async def get_context(
    query: str = Query(..., description="Natural language or code query"),
    top_k: int = Query(default=5, ge=1, le=20),
):
    """
    Returns a formatted, LLM-ready context string
    for the most semantically relevant code chunks.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    retriever = get_retriever()

    if not retriever.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Vector store not indexed. POST /retrieval/index first."
        )

    context = retriever.get_context(query=query, top_k=top_k)

    return {
        "success": True,
        "query":   query,
        "context": context,
    }


# ─────────────────────────────────────────────
# POST /retrieval/index
# ─────────────────────────────────────────────

@router.post("/index", summary="Index the repository into ChromaDB")
async def index_repository(repo_path: str = "."):
    """
    Scans, chunks, embeds and stores the entire
    repository into ChromaDB for semantic retrieval.
    Skips already-indexed chunks (idempotent).
    """
    try:
        from vectorstore.repo_loader import RepoLoader
        from vectorstore.chunker import CodeChunker

        retriever = get_retriever()

        loader  = RepoLoader(repo_path=repo_path)
        docs    = loader.load()
        chunks  = CodeChunker().chunk_all(docs)
        result  = retriever.store.store_chunks(chunks, show_progress=False)
        stats   = loader.summary()

        return {
            "success":     True,
            "files_loaded": stats["total_files"],
            "total_lines":  stats["total_lines"],
            "chunks_total": result["total"],
            "chunks_stored": result["stored"],
            "chunks_skipped": result["skipped"],
            "db_count":     retriever.store.count(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


# ─────────────────────────────────────────────
# GET /retrieval/stats
# ─────────────────────────────────────────────

@router.get("/stats", summary="Vector store statistics")
async def retrieval_stats():
    """Returns current ChromaDB collection statistics."""
    retriever = get_retriever()
    return {
        "success": True,
        **retriever.stats(),
    }
