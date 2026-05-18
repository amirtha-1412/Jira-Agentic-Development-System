"""
tests/test_chunker_phase.py
---------------------------------------------
Chunker Testing Phase:
  - Large text split     -> Success
  - Chunk sizes correct  -> Success
  - No empty chunks      -> Success
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


# =============================================================
# HELPER
# =============================================================

def make_doc(content: str, ext: str = ".py", name: str = "test_file") -> RepoDocument:
    tmp   = tempfile.mkdtemp()
    fname = f"{name}{ext}"
    fpath = os.path.join(tmp, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    return RepoDocument(fpath, content, tmp)


# =============================================================
# TEST SUITE
# =============================================================

class TestChunkerPhase(unittest.TestCase):

    # ---------------------------------------------------------
    # TEST 1: Large text split into multiple chunks
    # ---------------------------------------------------------
    def test_1_large_text_split(self):
        """A 500-line file must be split into multiple chunks."""
        print("\n[TEST 1] Large Text Split")
        print("-" * 50)

        # Create 500-line Python file with 10 functions
        blocks = []
        for i in range(10):
            block = (
                f"def function_{i}(x):\n"
                f"    \"\"\"Function {i}\"\"\"\n"
                + "\n".join([f"    step_{j} = x + {j}" for j in range(45)])
                + f"\n    return step_44\n"
            )
            blocks.append(block)

        content = "\n\n".join(blocks)
        doc     = make_doc(content, ".py")
        chunker = CodeChunker()
        chunks  = chunker.chunk(doc)

        self.assertGreater(len(chunks), 1, "Large file must produce multiple chunks")
        total_lines = sum(c.line_count for c in chunks)

        print(f"  [OK] File line count   : {doc.line_count}")
        print(f"  [OK] Total chunks      : {len(chunks)}")
        print(f"  [OK] Chunk types       : {set(c.chunk_type for c in chunks)}")
        print(f"  [OK] Lines across all  : {total_lines}")
        for c in chunks[:4]:
            print(f"       [{c.chunk_type}] lines {c.start_line}-{c.end_line} ({c.line_count} lines)")
        print("  => PASS — Large file split into multiple chunks")

    # ---------------------------------------------------------
    # TEST 2: Chunk sizes correct (window mode)
    # ---------------------------------------------------------
    def test_2_chunk_sizes_correct_window(self):
        """Window chunks must not exceed the configured window_size."""
        print("\n[TEST 2] Chunk Sizes Correct (Window Mode)")
        print("-" * 50)

        # 200 lines of JS code
        lines   = [f"const x_{i} = {i} * 2; // line {i}" for i in range(200)]
        content = "\n".join(lines)
        doc     = make_doc(content, ".js")

        window_size = 40
        overlap     = 8
        chunker     = CodeChunker(window_size=window_size, overlap=overlap)
        chunks      = chunker.chunk(doc)

        self.assertGreater(len(chunks), 1)

        oversized = [c for c in chunks if c.line_count > window_size]
        self.assertEqual(len(oversized), 0,
                         f"Oversized chunks found: {[(c.start_line, c.line_count) for c in oversized]}")

        print(f"  [OK] Window size       : {window_size} lines")
        print(f"  [OK] Overlap           : {overlap} lines")
        print(f"  [OK] Total chunks      : {len(chunks)}")
        print(f"  [OK] Oversized chunks  : {len(oversized)} (expected 0)")
        for c in chunks:
            print(f"       lines {c.start_line}-{c.end_line} ({c.line_count} lines)")
        print("  => PASS — All chunks within size limit")

    # ---------------------------------------------------------
    # TEST 3: Chunk sizes correct (Python semantic mode)
    # ---------------------------------------------------------
    def test_3_chunk_sizes_correct_python(self):
        """Python chunks must contain meaningful content, not single lines."""
        print("\n[TEST 3] Chunk Sizes Correct (Python Semantic)")
        print("-" * 50)

        content = (
            "import os\nimport sys\n\n"
            + "".join([
                f"def handler_{i}(request):\n"
                f"    data = request.get('key_{i}')\n"
                f"    result = data * {i + 1}\n"
                f"    return result\n\n"
                for i in range(8)
            ])
        )

        doc     = make_doc(content, ".py")
        chunker = CodeChunker(min_lines=2)
        chunks  = chunker.chunk(doc)

        self.assertGreater(len(chunks), 0)
        for c in chunks:
            self.assertGreaterEqual(c.line_count, 2,
                                    f"Chunk too small: {c.line_count} lines at {c.start_line}")

        sizes = [c.line_count for c in chunks]
        print(f"  [OK] Total chunks      : {len(chunks)}")
        print(f"  [OK] Min chunk lines   : {min(sizes)}")
        print(f"  [OK] Max chunk lines   : {max(sizes)}")
        print(f"  [OK] Avg chunk lines   : {sum(sizes)/len(sizes):.1f}")
        for c in chunks:
            print(f"       [{c.chunk_type}] lines {c.start_line}-{c.end_line} ({c.line_count} lines)")
        print("  => PASS — All chunks have correct sizes")

    # ---------------------------------------------------------
    # TEST 4: No empty chunks
    # ---------------------------------------------------------
    def test_4_no_empty_chunks(self):
        """No chunk should have empty content."""
        print("\n[TEST 4] No Empty Chunks")
        print("-" * 50)

        # Mix of file types
        test_cases = [
            ("def foo():\n    return 1\n\ndef bar():\n    return 2\n", ".py"),
            ("function a() {}\nfunction b() {}\n", ".js"),
            ("SELECT * FROM users;\nWHERE id = 1;\n", ".sql"),
            ("\n".join([f"line {i}" for i in range(100)]), ".md"),
        ]

        all_chunks = []
        for content, ext in test_cases:
            doc    = make_doc(content, ext)
            chunker = CodeChunker(window_size=30, overlap=5, min_lines=2)
            chunks = chunker.chunk(doc)
            all_chunks.extend(chunks)

        empty_chunks = [c for c in all_chunks if not c.content.strip()]
        self.assertEqual(len(empty_chunks), 0,
                         f"Found {len(empty_chunks)} empty chunks!")

        print(f"  [OK] Total chunks      : {len(all_chunks)}")
        print(f"  [OK] Empty chunks      : {len(empty_chunks)} (expected 0)")
        print(f"  [OK] All chunks have content")
        for c in all_chunks:
            preview = c.content[:40].replace("\n", " ")
            print(f"       [{c.extension}] '{preview}...'")
        print("  => PASS — Zero empty chunks")

    # ---------------------------------------------------------
    # TEST 5: Chunk IDs are unique
    # ---------------------------------------------------------
    def test_5_chunk_ids_unique(self):
        """Every chunk must have a unique chunk_id."""
        print("\n[TEST 5] Chunk IDs Unique")
        print("-" * 50)

        content = "\n".join([f"def fn_{i}():\n    return {i}\n" for i in range(20)])
        doc     = make_doc(content, ".py")
        chunker = CodeChunker()
        chunks  = chunker.chunk(doc)

        ids        = [c.chunk_id for c in chunks]
        unique_ids = set(ids)

        self.assertEqual(len(ids), len(unique_ids),
                         "Duplicate chunk IDs detected!")

        print(f"  [OK] Total chunks      : {len(chunks)}")
        print(f"  [OK] Unique IDs        : {len(unique_ids)}")
        print(f"  [OK] No duplicates     : True")
        print("  => PASS — All chunk IDs are unique")

    # ---------------------------------------------------------
    # TEST 6: Real project chunking
    # ---------------------------------------------------------
    def test_6_real_project_chunking(self):
        """Chunk the actual project repo and validate all chunks are valid."""
        print("\n[TEST 6] Real Project Chunking")
        print("-" * 50)

        from vectorstore.repo_loader import RepoLoader

        loader  = RepoLoader(repo_path=".")
        docs    = loader.load()
        chunker = CodeChunker(window_size=50, overlap=10)
        chunks  = chunker.chunk_all(docs)

        self.assertGreater(len(chunks), 0)

        empty   = [c for c in chunks if not c.content.strip()]
        no_meta = [c for c in chunks if not c.chunk_id]

        self.assertEqual(len(empty),   0, "Empty chunks found in real project!")
        self.assertEqual(len(no_meta), 0, "Chunks without ID found!")

        py_chunks  = [c for c in chunks if c.extension == ".py"]
        func_chunks = [c for c in chunks if c.chunk_type == "function"]
        win_chunks  = [c for c in chunks if c.chunk_type == "window"]

        print(f"  [OK] Docs loaded       : {len(docs)}")
        print(f"  [OK] Total chunks      : {len(chunks)}")
        print(f"  [OK] Python chunks     : {len(py_chunks)}")
        print(f"  [OK] Function chunks   : {len(func_chunks)}")
        print(f"  [OK] Window chunks     : {len(win_chunks)}")
        print(f"  [OK] Empty chunks      : {len(empty)} (expected 0)")
        print("  => PASS — Real project chunked successfully")


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  CHUNKER — FULL TESTING PHASE")
    print("=" * 55)

    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite  = loader.loadTestsFromTestCase(TestChunkerPhase)

    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 55)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    if result.wasSuccessful():
        print("  [ALL PASS] Chunker is production ready!")
    else:
        for f in result.failures + result.errors:
            print(f"  [FAIL] {f[0]}")
            print(f"         {f[1][:200]}")
    print("=" * 55 + "\n")
