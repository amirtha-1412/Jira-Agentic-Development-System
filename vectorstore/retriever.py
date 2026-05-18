"""
vectorstore/retriever.py
---------------------------------------------
Semantic Code Retriever
High-level interface for querying the ChromaDB
vector store with natural language.

Pipeline:
  Query String
       -> EmbeddingGenerator (encode query)
       -> ChromaDB (cosine similarity search)
       -> Ranked RetrievalResult objects
       -> Agent-ready context string
"""

from vectorstore.chroma_store import ChromaStore
from vectorstore.embeddings import EmbeddingGenerator

# ─── Defaults ────────────────────────────────
DEFAULT_TOP_K       = 5
DEFAULT_MIN_SIM     = 0.20   # minimum similarity threshold


# ─────────────────────────────────────────────
# Result Model
# ─────────────────────────────────────────────

class RetrievalResult:
    """Represents a single semantic search result."""

    def __init__(self, content: str, metadata: dict, similarity: float):
        self.content     = content
        self.metadata    = metadata
        self.similarity  = similarity
        # Convenience aliases
        self.source_path = metadata.get("source_path", "unknown")
        self.filename    = metadata.get("filename",    "unknown")
        self.extension   = metadata.get("extension",   "")
        self.start_line  = metadata.get("start_line",  0)
        self.end_line    = metadata.get("end_line",    0)
        self.chunk_type  = metadata.get("chunk_type",  "window")

    def to_context_block(self) -> str:
        """
        Formats this result as a readable context block
        for injection into an LLM prompt.
        """
        return (
            f"# File: {self.source_path} "
            f"(lines {self.start_line}-{self.end_line}, "
            f"similarity={self.similarity:.2f})\n"
            f"```{self.extension.lstrip('.')}\n"
            f"{self.content}\n"
            f"```"
        )

    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "filename":    self.filename,
            "start_line":  self.start_line,
            "end_line":    self.end_line,
            "chunk_type":  self.chunk_type,
            "similarity":  self.similarity,
            "content":     self.content,
        }

    def __repr__(self):
        return (
            f"RetrievalResult(src={self.source_path}, "
            f"lines={self.start_line}-{self.end_line}, "
            f"sim={self.similarity:.4f})"
        )


# ─────────────────────────────────────────────
# Retriever
# ─────────────────────────────────────────────

class CodeRetriever:
    """
    Semantic search engine over a ChromaDB-indexed
    repository. Accepts natural language queries and
    returns ranked, relevant code chunks.
    """

    def __init__(
        self,
        db_path:         str   = "./vectorstore/chroma_db",
        collection_name: str   = "repo_chunks",
        model_name:      str   = "all-MiniLM-L6-v2",
        top_k:           int   = DEFAULT_TOP_K,
        min_similarity:  float = DEFAULT_MIN_SIM,
    ):
        self.top_k          = top_k
        self.min_similarity = min_similarity
        self.store          = ChromaStore(
            db_path         = db_path,
            collection_name = collection_name,
            model_name      = model_name,
        )

    # ─────────────────────────────────────────
    # Core Search
    # ─────────────────────────────────────────

    def search(
        self,
        query:   str,
        top_k:   int   = None,
        min_sim: float = None,
        ext_filter: str = None,   # e.g. ".py" to restrict to Python files
    ) -> list[RetrievalResult]:
        """
        Runs a semantic search against the vector store.

        Args:
            query:      Natural language or code query
            top_k:      Max number of results (overrides default)
            min_sim:    Min similarity threshold (overrides default)
            ext_filter: Only return results from files with this extension

        Returns:
            list[RetrievalResult]: Ranked, filtered results
        """
        if not query or not query.strip():
            return []

        n     = top_k   or self.top_k
        min_s = min_sim or self.min_similarity

        if self.store.count() == 0:
            return []

        raw_results = self.store.query(query_text=query, n_results=n)

        results = []
        for r in raw_results:
            # Apply similarity filter
            if r["similarity"] < min_s:
                continue
            # Apply extension filter
            if ext_filter and r["metadata"].get("extension") != ext_filter:
                continue

            results.append(RetrievalResult(
                content    = r["content"],
                metadata   = r["metadata"],
                similarity = r["similarity"],
            ))

        # Sort descending by similarity
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results

    # ─────────────────────────────────────────
    # Context Builder (for LLM injection)
    # ─────────────────────────────────────────

    def get_context(
        self,
        query:      str,
        top_k:      int  = None,
        min_sim:    float = None,
        ext_filter: str  = None,
    ) -> str:
        """
        Returns a formatted context string from top results,
        ready to inject directly into an LLM prompt.

        Returns:
            str: Multi-block formatted code context
        """
        results = self.search(query, top_k, min_sim, ext_filter)

        if not results:
            return f"# No relevant code found for: '{query}'"

        header  = f"# Relevant Code Context for: '{query}'\n"
        header += f"# Found {len(results)} matching chunk(s)\n\n"
        blocks  = "\n\n".join(r.to_context_block() for r in results)
        return header + blocks

    # ─────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────

    def is_ready(self) -> bool:
        """Returns True if the vector store has indexed data."""
        return self.store.count() > 0

    def stats(self) -> dict:
        return {
            **self.store.stats(),
            "top_k":          self.top_k,
            "min_similarity":  self.min_similarity,
        }


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("\n" + "=" * 60)
    print("  RETRIEVER - TEST RUN")
    print("=" * 60)

    retriever = CodeRetriever()

    if not retriever.is_ready():
        print("  [INFO] Vector store empty. Indexing project now...")
        from vectorstore.repo_loader import RepoLoader
        from vectorstore.chunker import CodeChunker

        loader  = RepoLoader(repo_path=".")
        docs    = loader.load()
        chunks  = CodeChunker().chunk_all(docs)
        retriever.store.store_chunks(chunks)
        print(f"  [OK] Indexed {len(chunks)} chunks.")

    queries = [
        "fetch Jira ticket by ID",
        "authentication and API key setup",
        "parse and normalize ticket priority",
        "ChromaDB store and retrieve embeddings",
    ]

    for query in queries:
        print(f"\n  Query: '{query}'")
        print("  " + "-" * 50)
        results = retriever.search(query, top_k=3)
        if results:
            for i, r in enumerate(results, 1):
                print(f"  [{i}] sim={r.similarity:.4f} | "
                      f"{r.source_path} "
                      f"L{r.start_line}-{r.end_line}")
        else:
            print("  [INFO] No results above similarity threshold.")

    print(f"\n  --- Store Stats ---")
    for k, v in retriever.stats().items():
        print(f"  {k:<20}: {v}")

    print("\n" + "=" * 60)
    print("  [DONE] Retriever test complete.")
    print("=" * 60 + "\n")
