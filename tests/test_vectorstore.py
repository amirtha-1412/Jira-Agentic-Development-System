"""
tests/test_vectorstore.py
---------------------------------------------
Full Testing Phase for RepoLoader + Chunker:

RepoLoader Tests:
  - Python files loaded        -> Success
  - JS files loaded            -> Success
  - Unsupported files ignored  -> Success
  - venv ignored               -> Success
  - node_modules ignored       -> Success
  - Only useful files indexed  -> Success

Chunker Tests:
  - Python semantic chunking   -> Success
  - Window chunking            -> Success
  - Chunk metadata valid       -> Success
  - Empty file safe            -> Success
"""

import sys
import io
import os
import tempfile
import unittest

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from vectorstore.repo_loader import RepoLoader, RepoDocument
from vectorstore.chunker import CodeChunker, CodeChunk


# =============================================================
# HELPER — Build a temp repo for isolated tests
# =============================================================

def create_temp_repo(files: dict) -> str:
    """
    Creates a temporary directory with given files.
    files = { "relative/path.py": "content", ... }
    Returns the temp dir path.
    """
    tmp = tempfile.mkdtemp()
    for rel_path, content in files.items():
        full_path = os.path.join(tmp, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
    return tmp


# =============================================================
# REPO LOADER TESTS
# =============================================================

class TestRepoLoader(unittest.TestCase):

    # ---------------------------------------------------------
    # TEST 1: Python files loaded
    # ---------------------------------------------------------
    def test_1_python_files_loaded(self):
        """Python .py files must be discovered and loaded."""
        print("\n[TEST 1] Python Files Loaded")
        print("-" * 50)

        tmp = create_temp_repo({
            "main.py":         "def hello():\n    return 'world'\n",
            "utils/helper.py": "def add(a, b):\n    return a + b\n",
        })

        loader = RepoLoader(repo_path=tmp)
        docs   = loader.load()

        py_docs = [d for d in docs if d.extension == ".py"]
        self.assertEqual(len(py_docs), 2)
        self.assertGreater(len(docs), 0)

        print(f"  [OK] Python files loaded : {len(py_docs)}")
        for d in py_docs:
            print(f"       -> {d.relative_path}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 2: JS files loaded
    # ---------------------------------------------------------
    def test_2_js_files_loaded(self):
        """JavaScript .js files must be discovered and loaded."""
        print("\n[TEST 2] JS Files Loaded")
        print("-" * 50)

        tmp = create_temp_repo({
            "app.js":        "function greet() { return 'hello'; }\n",
            "src/index.ts":  "const x: number = 42;\n",
        })

        loader = RepoLoader(repo_path=tmp)
        docs   = loader.load()

        js_docs = [d for d in docs if d.extension in {".js", ".ts"}]
        self.assertEqual(len(js_docs), 2)

        print(f"  [OK] JS/TS files loaded : {len(js_docs)}")
        for d in js_docs:
            print(f"       -> {d.relative_path} ({d.extension})")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 3: Unsupported files ignored
    # ---------------------------------------------------------
    def test_3_unsupported_files_ignored(self):
        """Binary, image, and other non-code files must be ignored."""
        print("\n[TEST 3] Unsupported Files Ignored")
        print("-" * 50)

        tmp = create_temp_repo({
            "main.py":    "print('hello')\n",
            "image.png":  "\x89PNG\r\n",
            "data.csv":   "col1,col2\n1,2\n",
            "binary.exe": "\x4d\x5a\x90\x00",
            "archive.zip":"PK\x03\x04",
        })

        loader = RepoLoader(repo_path=tmp)
        docs   = loader.load()

        extensions = {d.extension for d in docs}
        self.assertNotIn(".png", extensions)
        self.assertNotIn(".csv", extensions)
        self.assertNotIn(".exe", extensions)
        self.assertNotIn(".zip", extensions)
        self.assertIn(".py", extensions)

        print(f"  [OK] Loaded extensions : {extensions}")
        print(f"  [OK] .png ignored      : {'.png' not in extensions}")
        print(f"  [OK] .csv ignored      : {'.csv' not in extensions}")
        print(f"  [OK] .exe ignored      : {'.exe' not in extensions}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 4: venv ignored
    # ---------------------------------------------------------
    def test_4_venv_ignored(self):
        """Files inside venv/ must be completely excluded."""
        print("\n[TEST 4] venv Ignored")
        print("-" * 50)

        tmp = create_temp_repo({
            "main.py":                    "print('app')\n",
            "venv/lib/site.py":           "# venv internal\n",
            "venv/Scripts/activate.py":   "# venv activate\n",
        })

        loader = RepoLoader(repo_path=tmp)
        docs   = loader.load()

        paths = [d.relative_path for d in docs]
        venv_files = [p for p in paths if "venv" in p]

        self.assertEqual(len(venv_files), 0, f"venv files leaked: {venv_files}")
        self.assertEqual(len(docs), 1)

        print(f"  [OK] Total loaded      : {len(docs)}")
        print(f"  [OK] venv files found  : {len(venv_files)} (expected 0)")
        print(f"  [OK] Loaded files      : {paths}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 5: node_modules ignored
    # ---------------------------------------------------------
    def test_5_node_modules_ignored(self):
        """Files inside node_modules/ must be excluded."""
        print("\n[TEST 5] node_modules Ignored")
        print("-" * 50)

        tmp = create_temp_repo({
            "index.js":                          "const app = require('express');\n",
            "node_modules/express/index.js":     "module.exports = {};\n",
            "node_modules/lodash/lodash.js":     "var _ = {};\n",
        })

        loader = RepoLoader(repo_path=tmp)
        docs   = loader.load()

        paths      = [d.relative_path for d in docs]
        node_files = [p for p in paths if "node_modules" in p]

        self.assertEqual(len(node_files), 0)
        self.assertEqual(len(docs), 1)

        print(f"  [OK] Total loaded          : {len(docs)}")
        print(f"  [OK] node_modules files    : {len(node_files)} (expected 0)")
        print(f"  [OK] Loaded               : {paths}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 6: Only useful files indexed
    # ---------------------------------------------------------
    def test_6_only_useful_files(self):
        """pycache, .git, and other noise dirs must be excluded."""
        print("\n[TEST 6] Only Useful Files Indexed")
        print("-" * 50)

        tmp = create_temp_repo({
            "app.py":                      "def run(): pass\n",
            "__pycache__/app.cpython.pyc": "bytecode",
            ".git/config":                 "[core]\n",
            ".pytest_cache/v/cache.json":  "{}",
        })

        loader = RepoLoader(repo_path=tmp)
        docs   = loader.load()

        paths = [d.relative_path for d in docs]
        noise = [p for p in paths if any(n in p for n in
                 ["__pycache__", ".git", ".pytest_cache"])]

        self.assertEqual(len(noise), 0)

        print(f"  [OK] Total loaded : {len(docs)}")
        print(f"  [OK] Noise files  : {len(noise)} (expected 0)")
        print(f"  [OK] Clean paths  : {paths}")
        print("  => PASS")


# =============================================================
# CHUNKER TESTS
# =============================================================

class TestChunker(unittest.TestCase):

    def _make_doc(self, content: str, ext: str = ".py") -> RepoDocument:
        """Helper to create a RepoDocument from raw content."""
        import tempfile, os
        tmp = tempfile.mkdtemp()
        fname = f"test_file{ext}"
        fpath = os.path.join(tmp, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        return RepoDocument(fpath, content, tmp)

    # ---------------------------------------------------------
    # TEST 7: Python semantic chunking
    # ---------------------------------------------------------
    def test_7_python_semantic_chunking(self):
        """Python files should be split by def/class blocks."""
        print("\n[TEST 7] Python Semantic Chunking")
        print("-" * 50)

        content = (
            "import os\n\n"
            "def function_one():\n"
            "    x = 1\n"
            "    return x\n\n"
            "def function_two():\n"
            "    y = 2\n"
            "    return y\n\n"
            "class MyClass:\n"
            "    def method(self):\n"
            "        pass\n"
        )

        doc     = self._make_doc(content, ".py")
        chunker = CodeChunker()
        chunks  = chunker.chunk(doc)

        self.assertGreater(len(chunks), 0)
        func_chunks = [c for c in chunks if c.chunk_type == "function"]
        self.assertGreater(len(func_chunks), 0)

        print(f"  [OK] Total chunks      : {len(chunks)}")
        print(f"  [OK] Function chunks   : {len(func_chunks)}")
        for c in chunks:
            print(f"       [{c.chunk_type}] lines {c.start_line}-{c.end_line}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 8: Window chunking for non-Python
    # ---------------------------------------------------------
    def test_8_window_chunking(self):
        """Non-Python files should use sliding window chunking."""
        print("\n[TEST 8] Window Chunking (JS)")
        print("-" * 50)

        lines   = [f"const line_{i} = {i};" for i in range(120)]
        content = "\n".join(lines)
        doc     = self._make_doc(content, ".js")
        chunker = CodeChunker(window_size=50, overlap=10)
        chunks  = chunker.chunk(doc)

        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertEqual(c.chunk_type, "window")
            self.assertLessEqual(c.line_count, 50)

        print(f"  [OK] Total chunks    : {len(chunks)}")
        print(f"  [OK] All type=window : {all(c.chunk_type == 'window' for c in chunks)}")
        for c in chunks:
            print(f"       lines {c.start_line}-{c.end_line} ({c.line_count} lines)")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 9: Chunk metadata is valid
    # ---------------------------------------------------------
    def test_9_chunk_metadata_valid(self):
        """Each chunk must have all required metadata fields."""
        print("\n[TEST 9] Chunk Metadata Valid")
        print("-" * 50)

        content = "def hello():\n    return 'world'\n" * 5
        doc     = self._make_doc(content, ".py")
        chunker = CodeChunker()
        chunks  = chunker.chunk(doc)

        required = ["chunk_id", "doc_id", "source_path", "filename",
                    "extension", "chunk_index", "start_line",
                    "end_line", "chunk_type", "line_count"]

        for c in chunks:
            meta = c.to_metadata()
            for key in required:
                self.assertIn(key, meta, f"Missing metadata key: {key}")

        if chunks:
            print(f"  [OK] Metadata keys : {list(chunks[0].to_metadata().keys())}")
        print(f"  [OK] All {len(chunks)} chunks have valid metadata")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 10: Empty / tiny file safe
    # ---------------------------------------------------------
    def test_10_empty_file_safe(self):
        """Empty or near-empty files must not crash the chunker."""
        print("\n[TEST 10] Empty/Tiny File Safe")
        print("-" * 50)

        for content in ["", "\n", "  \n  \n"]:
            try:
                doc    = self._make_doc(content or "\n", ".py")
                doc.content = content
                chunker = CodeChunker()
                chunks  = chunker.chunk(doc)
                self.assertIsInstance(chunks, list)
                print(f"  [OK] content={repr(content[:10])} -> {len(chunks)} chunks (no crash)")
            except Exception as e:
                self.fail(f"Chunker crashed on empty content: {e}")

        print("  => PASS")


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  VECTORSTORE — FULL TEST PHASE")
    print("=" * 55)

    loader_suite  = unittest.TestLoader()
    loader_suite.sortTestMethodsUsing = None
    suite = loader_suite.loadTestsFromTestCase(TestRepoLoader)
    suite.addTests(loader_suite.loadTestsFromTestCase(TestChunker))

    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 55)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    if result.wasSuccessful():
        print("  [ALL PASS] VectorStore layer is production ready!")
    else:
        for f in result.failures + result.errors:
            print(f"  [FAIL] {f[0]}")
            print(f"         {f[1][:200]}")
    print("=" * 55 + "\n")
