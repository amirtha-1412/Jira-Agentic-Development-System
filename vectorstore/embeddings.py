"""
vectorstore/embeddings.py
---------------------------------------------
Embedding Generator Module
Converts CodeChunk text into dense vector
embeddings using sentence-transformers.

Model: all-MiniLM-L6-v2
  - Fast & lightweight (80MB)
  - 384-dimensional output
  - Great for code + natural language
"""

from sentence_transformers import SentenceTransformer
from vectorstore.chunker import CodeChunk

# ─── Model config ────────────────────────────
DEFAULT_MODEL  = "all-MiniLM-L6-v2"
EMBEDDING_DIM  = 384   # output dimension of default model

_model_cache: dict = {}  # singleton cache to avoid reloading


# ─────────────────────────────────────────────
# Model Loader (singleton)
# ─────────────────────────────────────────────

def load_model(model_name: str = DEFAULT_MODEL) -> SentenceTransformer:
    """
    Loads and caches a SentenceTransformer model.
    Returns the cached model on subsequent calls.
    """
    if model_name not in _model_cache:
        print(f"  [Embedder] Loading model: {model_name} ...")
        _model_cache[model_name] = SentenceTransformer(model_name)
        print(f"  [Embedder] Model loaded. Dim={EMBEDDING_DIM}")
    return _model_cache[model_name]


# ─────────────────────────────────────────────
# Embedding Generator
# ─────────────────────────────────────────────

class EmbeddingGenerator:
    """
    Generates vector embeddings from CodeChunk objects
    using a SentenceTransformer model.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.model      = load_model(model_name)
        self.dim        = self.model.get_embedding_dimension()

    def embed_text(self, text: str) -> list[float]:
        """
        Embeds a single text string.

        Returns:
            list[float]: Dense embedding vector
        """
        if not text or not text.strip():
            return [0.0] * self.dim

        vector = self.model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def embed_chunk(self, chunk: CodeChunk) -> dict:
        """
        Embeds a single CodeChunk.

        Returns:
            dict: { chunk_id, embedding, metadata }
        """
        embedding = self.embed_text(chunk.content)
        return {
            "chunk_id":  chunk.chunk_id,
            "embedding": embedding,
            "content":   chunk.content,
            "metadata":  chunk.to_metadata(),
        }

    def embed_chunks(
        self,
        chunks: list[CodeChunk],
        batch_size: int = 32,
        show_progress: bool = True,
    ) -> list[dict]:
        """
        Embeds a list of CodeChunks in batches for efficiency.

        Args:
            chunks:       List of CodeChunk objects
            batch_size:   Number of texts per encoding batch
            show_progress: Print progress info

        Returns:
            list[dict]: List of { chunk_id, embedding, metadata }
        """
        if not chunks:
            return []

        results = []
        total   = len(chunks)

        for i in range(0, total, batch_size):
            batch       = chunks[i : i + batch_size]
            texts       = [c.content for c in batch]
            embeddings  = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            for chunk, vector in zip(batch, embeddings):
                results.append({
                    "chunk_id":  chunk.chunk_id,
                    "embedding": vector.tolist(),
                    "content":   chunk.content,
                    "metadata":  chunk.to_metadata(),
                })

            if show_progress:
                done = min(i + batch_size, total)
                print(f"  [Embedder] {done}/{total} chunks embedded...")

        return results

    def embed_query(self, query: str) -> list[float]:
        """
        Embeds a natural language query for similarity search.

        Args:
            query: Search query string

        Returns:
            list[float]: Query embedding vector
        """
        return self.embed_text(query)


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    from vectorstore.repo_loader import RepoLoader
    from vectorstore.chunker import CodeChunker

    print("\n" + "=" * 55)
    print("  EMBEDDER - TEST RUN")
    print("=" * 55)

    loader  = RepoLoader(repo_path=".")
    docs    = loader.load()
    chunker = CodeChunker()
    chunks  = chunker.chunk_all(docs)[:5]   # test on first 5 chunks

    embedder = EmbeddingGenerator()

    print(f"\n  [OK] Model       : {embedder.model_name}")
    print(f"  [OK] Dimension   : {embedder.dim}")
    print(f"  [OK] Chunks      : {len(chunks)}")

    results = embedder.embed_chunks(chunks, show_progress=True)

    print(f"\n  Sample embedding results:")
    for r in results:
        vec = r["embedding"]
        print(f"  [OK] {r['metadata']['source_path']:<40} "
              f"dim={len(vec)}  "
              f"first3={[round(v,4) for v in vec[:3]]}")

    print("\n" + "=" * 55)
    print("  [DONE] Embedder test complete.")
    print("=" * 55 + "\n")
