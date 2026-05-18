"""
vectorstore/chroma_store.py
---------------------------------------------
ChromaDB Vector Store
Stores and retrieves code chunk embeddings
in a persistent local ChromaDB collection.

Pipeline:
  CodeChunks -> EmbeddingGenerator -> ChromaDB
"""

import os
import chromadb
from chromadb.config import Settings
from vectorstore.embeddings import EmbeddingGenerator
from vectorstore.chunker import CodeChunk

# ─── DB config ───────────────────────────────
DEFAULT_DB_PATH   = "./vectorstore/chroma_db"
DEFAULT_COLLECTION = "repo_chunks"


# ─────────────────────────────────────────────
# ChromaDB Store
# ─────────────────────────────────────────────

class ChromaStore:
    """
    Manages a persistent ChromaDB collection for
    storing and querying code chunk embeddings.
    """

    def __init__(
        self,
        db_path:         str = DEFAULT_DB_PATH,
        collection_name: str = DEFAULT_COLLECTION,
        model_name:      str = "all-MiniLM-L6-v2",
    ):
        self.db_path         = os.path.abspath(db_path)
        self.collection_name = collection_name
        self.embedder        = EmbeddingGenerator(model_name)

        # Initialize persistent ChromaDB client
        os.makedirs(self.db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.db_path)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name     = self.collection_name,
            metadata = {"hnsw:space": "cosine"},   # cosine similarity
        )

        print(f"  [ChromaDB] Collection '{collection_name}' ready.")
        print(f"  [ChromaDB] Path: {self.db_path}")
        print(f"  [ChromaDB] Existing docs: {self.collection.count()}")

    # ─────────────────────────────────────────
    # Store
    # ─────────────────────────────────────────

    def store_chunks(
        self,
        chunks:       list[CodeChunk],
        batch_size:   int  = 32,
        skip_existing: bool = True,
        show_progress: bool = True,
    ) -> dict:
        """
        Embeds and stores CodeChunk objects in ChromaDB.
        Skips duplicates by chunk_id to prevent errors.

        Args:
            chunks:        List of CodeChunk to store
            batch_size:    Embedding batch size
            skip_existing: Skip already-stored chunk IDs

        Returns:
            dict: { stored, skipped, total }
        """
        if not chunks:
            return {"stored": 0, "skipped": 0, "total": 0}

        # ── Dedup by chunk_id ─────────────────
        if skip_existing:
            existing_ids = set(self.collection.get()["ids"])
            new_chunks   = [c for c in chunks if c.chunk_id not in existing_ids]
            skipped      = len(chunks) - len(new_chunks)
        else:
            new_chunks = chunks
            skipped    = 0

        if not new_chunks:
            print(f"  [ChromaDB] All {len(chunks)} chunks already stored. Skipping.")
            return {"stored": 0, "skipped": skipped, "total": len(chunks)}

        print(f"  [ChromaDB] Embedding {len(new_chunks)} new chunks...")
        embedded = self.embedder.embed_chunks(
            new_chunks,
            batch_size=batch_size,
            show_progress=show_progress,
        )

        # ── Batch upsert into ChromaDB ────────
        for i in range(0, len(embedded), batch_size):
            batch = embedded[i : i + batch_size]
            self.collection.add(
                ids        = [e["chunk_id"]  for e in batch],
                embeddings = [e["embedding"] for e in batch],
                documents  = [e["content"]   for e in batch],
                metadatas  = [e["metadata"]  for e in batch],
            )

        print(f"  [ChromaDB] Stored {len(new_chunks)} chunks successfully.")
        return {
            "stored":  len(new_chunks),
            "skipped": skipped,
            "total":   len(chunks),
        }

    # ─────────────────────────────────────────
    # Query
    # ─────────────────────────────────────────

    def query(self, query_text: str, n_results: int = 5) -> list[dict]:
        """
        Finds the most semantically similar chunks
        to the query text.

        Args:
            query_text: Natural language or code query
            n_results:  Number of results to return

        Returns:
            list[dict]: Ranked results with content + metadata
        """
        if self.collection.count() == 0:
            return []

        query_embedding = self.embedder.embed_query(query_text)
        n = min(n_results, self.collection.count())

        results = self.collection.query(
            query_embeddings = [query_embedding],
            n_results        = n,
            include          = ["documents", "metadatas", "distances"],
        )

        output = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            output.append({
                "content":    doc,
                "metadata":   meta,
                "similarity": round(1 - dist, 4),   # cosine: 1=identical
            })

        return output

    # ─────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────

    def count(self) -> int:
        """Returns total number of stored chunks."""
        return self.collection.count()

    def reset(self) -> None:
        """Deletes and recreates the collection (use carefully)."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name     = self.collection_name,
            metadata = {"hnsw:space": "cosine"},
        )
        print(f"  [ChromaDB] Collection '{self.collection_name}' reset.")

    def stats(self) -> dict:
        """Returns store statistics."""
        return {
            "collection":  self.collection_name,
            "db_path":     self.db_path,
            "total_chunks": self.count(),
            "model":       self.embedder.model_name,
            "dim":         self.embedder.dim,
        }


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    from vectorstore.repo_loader import RepoLoader
    from vectorstore.chunker import CodeChunker

    print("\n" + "=" * 55)
    print("  CHROMA STORE - TEST RUN")
    print("=" * 55)

    # Load + chunk project
    loader  = RepoLoader(repo_path=".")
    docs    = loader.load()
    chunker = CodeChunker()
    chunks  = chunker.chunk_all(docs)

    # Store in ChromaDB
    store  = ChromaStore()
    store.reset()   # fresh start for test
    result = store.store_chunks(chunks)

    print(f"\n  [OK] Stored  : {result['stored']}")
    print(f"  [OK] Skipped : {result['skipped']}")
    print(f"  [OK] Total   : {result['total']}")
    print(f"  [OK] DB count: {store.count()}")

    # Query test
    print(f"\n  --- Query Test ---")
    query   = "fetch Jira ticket by ID"
    results = store.query(query, n_results=3)
    print(f"  Query: '{query}'")
    for i, r in enumerate(results, 1):
        print(f"  [{i}] {r['metadata']['source_path']} "
              f"(sim={r['similarity']}) "
              f"| {r['content'][:60].replace(chr(10), ' ')}...")

    # Stats
    print(f"\n  --- Store Stats ---")
    for k, v in store.stats().items():
        print(f"  {k:<16}: {v}")

    print("\n" + "=" * 55)
    print("  [DONE] ChromaDB store test complete.")
    print("=" * 55 + "\n")
