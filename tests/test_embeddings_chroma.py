"""
tests/test_embeddings_chroma.py
---------------------------------------------
Full Testing Phase:

Embedding Tests:
  - Embedding generated    -> Success
  - Vector length valid    -> Success
  - No model errors        -> Success

ChromaDB Tests:
  - ChromaDB runs          -> Success
  - Embeddings stored      -> Success
  - No duplicate errors    -> Success
"""

import sys
import io
import os
import tempfile
import unittest

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from vectorstore.repo_loader import RepoDocument
from vectorstore.chunker import CodeChunker, CodeChunk
from vectorstore.embeddings import EmbeddingGenerator, EMBEDDING_DIM
from vectorstore.chroma_store import ChromaStore


# =============================================================
# HELPERS
# =============================================================

def make_doc(content: str, ext: str = ".py") -> RepoDocument:
    tmp   = tempfile.mkdtemp()
    fpath = os.path.join(tmp, f"test{ext}")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    return RepoDocument(fpath, content, tmp)


def make_chunks(content: str = None, ext: str = ".py", n: int = 3) -> list[CodeChunk]:
    if content is None:
        content = "\n\n".join([
            f"def function_{i}():\n    return {i}\n" for i in range(n)
        ])
    doc     = make_doc(content, ext)
    chunker = CodeChunker(min_lines=1)
    return chunker.chunk(doc)


def temp_chroma_path() -> str:
    """Returns a fresh temp path for an isolated ChromaDB test."""
    return os.path.join(tempfile.mkdtemp(), "test_chroma_db")


# =============================================================
# EMBEDDING TESTS
# =============================================================

class TestEmbeddings(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load model once for all embedding tests."""
        print("\n  [Setup] Loading embedding model...")
        cls.embedder = EmbeddingGenerator()
        print(f"  [Setup] Model ready: {cls.embedder.model_name}")

    # ---------------------------------------------------------
    # TEST 1: Embedding generated
    # ---------------------------------------------------------
    def test_1_embedding_generated(self):
        """embed_text must return a non-empty list of floats."""
        print("\n[TEST 1] Embedding Generated")
        print("-" * 50)

        text      = "def fetch_ticket(ticket_id: str) -> dict:"
        embedding = self.embedder.embed_text(text)

        self.assertIsInstance(embedding, list)
        self.assertGreater(len(embedding), 0)
        self.assertTrue(all(isinstance(v, float) for v in embedding))

        print(f"  [OK] Type        : {type(embedding)}")
        print(f"  [OK] Length      : {len(embedding)}")
        print(f"  [OK] First 3 vals: {[round(v, 4) for v in embedding[:3]]}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 2: Vector length valid
    # ---------------------------------------------------------
    def test_2_vector_length_valid(self):
        """Embedding dimension must match the expected model output size."""
        print("\n[TEST 2] Vector Length Valid")
        print("-" * 50)

        texts = [
            "short text",
            "def complex_function(a, b, c):\n    return a + b + c",
            "A" * 500,   # very long string
        ]

        for text in texts:
            vec = self.embedder.embed_text(text)
            self.assertEqual(
                len(vec), EMBEDDING_DIM,
                f"Expected dim {EMBEDDING_DIM}, got {len(vec)} for text length {len(text)}"
            )
            print(f"  [OK] len={len(text):>5} chars -> dim={len(vec)}")

        self.assertEqual(self.embedder.dim, EMBEDDING_DIM)
        print(f"  [OK] Model dim   : {self.embedder.dim}")
        print("  => PASS — All embeddings have correct dimension")

    # ---------------------------------------------------------
    # TEST 3: No model errors on various inputs
    # ---------------------------------------------------------
    def test_3_no_model_errors(self):
        """Model must handle edge cases without crashing."""
        print("\n[TEST 3] No Model Errors")
        print("-" * 50)

        edge_cases = [
            ("Normal code",   "def hello(): return 'world'"),
            ("Empty string",  ""),
            ("Whitespace",    "   \n  \n  "),
            ("Unicode",       "# 你好世界 - こんにちは - مرحبا"),
            ("Special chars", "!@#$%^&*()_+-=[]{}|;':\",./<>?"),
            ("Long text",     "x = 1\n" * 200),
        ]

        for label, text in edge_cases:
            try:
                vec = self.embedder.embed_text(text)
                self.assertIsInstance(vec, list)
                self.assertEqual(len(vec), EMBEDDING_DIM)
                print(f"  [OK] {label:<20} -> dim={len(vec)}")
            except Exception as e:
                self.fail(f"Model crashed on '{label}': {e}")

        print("  => PASS — No model errors on any input")

    # ---------------------------------------------------------
    # TEST 4: Batch embedding
    # ---------------------------------------------------------
    def test_4_batch_embedding(self):
        """embed_chunks must embed multiple chunks correctly."""
        print("\n[TEST 4] Batch Embedding")
        print("-" * 50)

        chunks  = make_chunks(n=5)
        results = self.embedder.embed_chunks(chunks, show_progress=False)

        self.assertEqual(len(results), len(chunks))

        for r in results:
            self.assertIn("chunk_id",  r)
            self.assertIn("embedding", r)
            self.assertIn("metadata",  r)
            self.assertEqual(len(r["embedding"]), EMBEDDING_DIM)

        print(f"  [OK] Input chunks  : {len(chunks)}")
        print(f"  [OK] Output results: {len(results)}")
        for r in results:
            print(f"       {r['chunk_id'][:40]} -> dim={len(r['embedding'])}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 5: Query embedding
    # ---------------------------------------------------------
    def test_5_query_embedding(self):
        """embed_query must return a valid query vector."""
        print("\n[TEST 5] Query Embedding")
        print("-" * 50)

        query = "fetch Jira ticket and parse description"
        vec   = self.embedder.embed_query(query)

        self.assertIsInstance(vec, list)
        self.assertEqual(len(vec), EMBEDDING_DIM)

        print(f"  [OK] Query   : '{query}'")
        print(f"  [OK] Dim     : {len(vec)}")
        print(f"  [OK] First 3 : {[round(v, 4) for v in vec[:3]]}")
        print("  => PASS")


# =============================================================
# CHROMADB TESTS
# =============================================================

class TestChromaStore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Shared ChromaStore with isolated temp DB."""
        print("\n  [Setup] Initializing isolated ChromaDB...")
        cls.db_path = temp_chroma_path()
        cls.store   = ChromaStore(db_path=cls.db_path, collection_name="test_col")
        cls.chunks  = make_chunks(n=5)

    # ---------------------------------------------------------
    # TEST 6: ChromaDB runs
    # ---------------------------------------------------------
    def test_6_chromadb_runs(self):
        """ChromaDB client must initialize without errors."""
        print("\n[TEST 6] ChromaDB Runs")
        print("-" * 50)

        self.assertIsNotNone(self.store.client)
        self.assertIsNotNone(self.store.collection)
        stats = self.store.stats()

        self.assertIn("collection",   stats)
        self.assertIn("total_chunks", stats)
        self.assertIn("dim",          stats)
        self.assertEqual(stats["dim"], EMBEDDING_DIM)

        print(f"  [OK] Client ready      : {self.store.client is not None}")
        print(f"  [OK] Collection        : {stats['collection']}")
        print(f"  [OK] Embedding dim     : {stats['dim']}")
        print(f"  [OK] DB path           : {stats['db_path']}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 7: Embeddings stored
    # ---------------------------------------------------------
    def test_7_embeddings_stored(self):
        """store_chunks must persist all chunks in ChromaDB."""
        print("\n[TEST 7] Embeddings Stored")
        print("-" * 50)

        self.store.reset()   # clean slate
        result = self.store.store_chunks(self.chunks, show_progress=False)

        self.assertEqual(result["stored"], len(self.chunks))
        self.assertEqual(self.store.count(), len(self.chunks))

        print(f"  [OK] Chunks submitted  : {len(self.chunks)}")
        print(f"  [OK] Chunks stored     : {result['stored']}")
        print(f"  [OK] DB count          : {self.store.count()}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 8: No duplicate errors
    # ---------------------------------------------------------
    def test_8_no_duplicate_errors(self):
        """Storing the same chunks twice must not crash or duplicate."""
        print("\n[TEST 8] No Duplicate Errors")
        print("-" * 50)

        # Store same chunks a second time
        try:
            result2 = self.store.store_chunks(self.chunks, show_progress=False)
            count   = self.store.count()

            # Count must remain the same (dedup worked)
            self.assertEqual(count, len(self.chunks))
            self.assertEqual(result2["skipped"], len(self.chunks))
            self.assertEqual(result2["stored"],  0)

            print(f"  [OK] Second store skipped : {result2['skipped']}")
            print(f"  [OK] Second store stored  : {result2['stored']}")
            print(f"  [OK] DB count unchanged   : {count}")
            print("  => PASS — No duplicates, no crash")
        except Exception as e:
            self.fail(f"Duplicate store crashed: {e}")

    # ---------------------------------------------------------
    # TEST 9: Query returns results
    # ---------------------------------------------------------
    def test_9_query_returns_results(self):
        """query() must return relevant chunks for a text query."""
        print("\n[TEST 9] Query Returns Results")
        print("-" * 50)

        results = self.store.query("function that returns a value", n_results=3)

        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        for r in results:
            self.assertIn("content",    r)
            self.assertIn("metadata",   r)
            self.assertIn("similarity", r)
            self.assertIsInstance(r["similarity"], float)

        print(f"  [OK] Results returned : {len(results)}")
        for i, r in enumerate(results, 1):
            preview = r["content"][:50].replace("\n", " ")
            print(f"  [{i}] sim={r['similarity']:.4f} | '{preview}...'")
        print("  => PASS")


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  EMBEDDINGS + CHROMADB — FULL TEST PHASE")
    print("=" * 55)

    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite  = loader.loadTestsFromTestCase(TestEmbeddings)
    suite.addTests(loader.loadTestsFromTestCase(TestChromaStore))

    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 55)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    if result.wasSuccessful():
        print("  [ALL PASS] Embeddings + ChromaDB are production ready!")
    else:
        for f in result.failures + result.errors:
            print(f"  [FAIL] {f[0]}")
            print(f"         {f[1][:200]}")
    print("=" * 55 + "\n")
