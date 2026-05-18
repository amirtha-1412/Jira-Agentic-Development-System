"""
tests/test_retriever.py
---------------------------------------------
Semantic Retriever Testing Phase:
  - Relevant files returned  -> Success
  - Query works              -> Success
  - No crashes               -> Success
"""

import sys
import io
import os
import tempfile
import unittest

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from vectorstore.repo_loader import RepoDocument
from vectorstore.chunker import CodeChunker
from vectorstore.chroma_store import ChromaStore
from vectorstore.retriever import CodeRetriever, RetrievalResult


# =============================================================
# SHARED FIXTURE — Builds an isolated indexed store
# =============================================================

SAMPLE_CONTENT = {
    "auth.py": (
        "def authenticate(email, api_key):\n"
        "    \"\"\"Verify Jira API credentials.\"\"\"\n"
        "    import base64\n"
        "    token = base64.b64encode(f'{email}:{api_key}'.encode()).decode()\n"
        "    return {'Authorization': f'Basic {token}'}\n"
    ),
    "connector.py": (
        "def fetch_ticket(ticket_id):\n"
        "    \"\"\"Fetch a Jira ticket by its ID.\"\"\"\n"
        "    url = f'/rest/api/3/issue/{ticket_id}'\n"
        "    response = requests.get(url)\n"
        "    return response.json()\n"
    ),
    "parser.py": (
        "def normalize_priority(priority):\n"
        "    \"\"\"Normalize priority to HIGH/MEDIUM/LOW/NONE.\"\"\"\n"
        "    mapping = {'high': 'HIGH', 'medium': 'MEDIUM', 'low': 'LOW'}\n"
        "    return mapping.get(str(priority).lower(), 'NONE')\n"
        "\n"
        "def normalize_status(status):\n"
        "    \"\"\"Normalize status to TODO/IN_PROGRESS/DONE.\"\"\"\n"
        "    mapping = {'to do': 'TODO', 'in progress': 'IN_PROGRESS'}\n"
        "    return mapping.get(str(status).lower(), status)\n"
    ),
    "embedder.py": (
        "def embed_text(text, model):\n"
        "    \"\"\"Generate vector embedding for text.\"\"\"\n"
        "    return model.encode(text).tolist()\n"
        "\n"
        "def store_in_chromadb(chunks, embeddings, collection):\n"
        "    \"\"\"Store chunk embeddings in ChromaDB collection.\"\"\"\n"
        "    collection.add(ids=[c.id for c in chunks],\n"
        "                   embeddings=embeddings,\n"
        "                   documents=[c.content for c in chunks])\n"
    ),
}


def build_fixture_store() -> tuple[CodeRetriever, str]:
    """
    Creates an isolated ChromaDB store with sample code,
    returns (retriever, tmp_db_path).
    """
    tmp_db = os.path.join(tempfile.mkdtemp(), "fixture_chroma")
    tmp_src = tempfile.mkdtemp()

    # Write sample files
    docs   = []
    chunks = []
    for fname, content in SAMPLE_CONTENT.items():
        fpath = os.path.join(tmp_src, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        doc = RepoDocument(fpath, content, tmp_src)
        docs.append(doc)
        chunks.extend(CodeChunker(min_lines=1).chunk(doc))

    # Index into isolated store
    store = ChromaStore(db_path=tmp_db, collection_name="fixture")
    store.store_chunks(chunks, show_progress=False)

    retriever = CodeRetriever.__new__(CodeRetriever)
    retriever.top_k          = 5
    retriever.min_similarity  = 0.15
    retriever.store           = store

    return retriever, tmp_db


# =============================================================
# TEST SUITE
# =============================================================

class TestRetriever(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n  [Setup] Building fixture vector store...")
        cls.retriever, cls.db_path = build_fixture_store()
        print(f"  [Setup] Indexed {cls.retriever.store.count()} chunks.")

    # ---------------------------------------------------------
    # TEST 1: Relevant files returned
    # ---------------------------------------------------------
    def test_1_relevant_files_returned(self):
        """Querying for ticket fetching must return connector.py as top result."""
        print("\n[TEST 1] Relevant Files Returned")
        print("-" * 50)

        results = self.retriever.search("fetch Jira ticket by ID", top_k=3)

        self.assertGreater(len(results), 0, "Expected at least 1 result")
        self.assertIsInstance(results[0], RetrievalResult)

        sources = [r.source_path for r in results]
        print(f"  [OK] Results count : {len(results)}")
        for r in results:
            print(f"       sim={r.similarity:.4f} | {r.source_path}")

        # connector.py should be in top results
        self.assertTrue(
            any("connector" in s for s in sources),
            f"Expected connector.py in results, got: {sources}"
        )
        print("  => PASS — Relevant files returned correctly")

    # ---------------------------------------------------------
    # TEST 2: Query works for authentication
    # ---------------------------------------------------------
    def test_2_query_authentication(self):
        """Auth-related query must surface auth.py."""
        print("\n[TEST 2] Query Works — Authentication")
        print("-" * 50)

        results = self.retriever.search("API key authentication base64", top_k=3)

        self.assertGreater(len(results), 0)
        sources = [r.source_path for r in results]

        print(f"  [OK] Results count : {len(results)}")
        for r in results:
            print(f"       sim={r.similarity:.4f} | {r.source_path}")

        self.assertTrue(
            any("auth" in s for s in sources),
            f"Expected auth.py in results, got: {sources}"
        )
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 3: Query works for parsing/normalization
    # ---------------------------------------------------------
    def test_3_query_parser(self):
        """Priority normalization query must surface parser.py."""
        print("\n[TEST 3] Query Works — Parser")
        print("-" * 50)

        results = self.retriever.search("normalize priority HIGH MEDIUM LOW", top_k=3)

        self.assertGreater(len(results), 0)
        sources = [r.source_path for r in results]

        print(f"  [OK] Results count : {len(results)}")
        for r in results:
            print(f"       sim={r.similarity:.4f} | {r.source_path}")

        self.assertTrue(
            any("parser" in s for s in sources),
            f"Expected parser.py in results, got: {sources}"
        )
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 4: No crashes on edge case queries
    # ---------------------------------------------------------
    def test_4_no_crashes(self):
        """All edge case queries must return safely without crashing."""
        print("\n[TEST 4] No Crashes on Edge Cases")
        print("-" * 50)

        edge_cases = [
            ("Empty query",      ""),
            ("Whitespace",       "   "),
            ("Gibberish",        "xyzxyzxyz_aaabbbccc_zzz"),
            ("Special chars",    "!!! @@@ ### $$$"),
            ("Very long query",  "fetch ticket " * 50),
            ("Code snippet",     "def foo(x):\n    return x * 2"),
        ]

        for label, query in edge_cases:
            try:
                results = self.retriever.search(query, top_k=3)
                self.assertIsInstance(results, list)
                print(f"  [OK] {label:<22} -> {len(results)} results (no crash)")
            except Exception as e:
                self.fail(f"Retriever crashed on '{label}': {e}")

        print("  => PASS — No crashes on any edge case")

    # ---------------------------------------------------------
    # TEST 5: RetrievalResult structure valid
    # ---------------------------------------------------------
    def test_5_result_structure_valid(self):
        """Each result must have all required fields."""
        print("\n[TEST 5] RetrievalResult Structure Valid")
        print("-" * 50)

        results = self.retriever.search("store embeddings ChromaDB", top_k=3)
        self.assertGreater(len(results), 0)

        for r in results:
            self.assertIsInstance(r.content,    str)
            self.assertIsInstance(r.source_path,str)
            self.assertIsInstance(r.similarity, float)
            self.assertIsInstance(r.start_line, int)
            self.assertIsInstance(r.end_line,   int)
            self.assertGreater(r.similarity, 0)

            d = r.to_dict()
            for key in ["source_path","filename","start_line",
                        "end_line","similarity","content"]:
                self.assertIn(key, d)

        print(f"  [OK] Results count : {len(results)}")
        print(f"  [OK] Fields valid  : all {len(results)} results")
        print(f"  [OK] Sample dict keys: {list(results[0].to_dict().keys())}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 6: get_context() returns LLM-ready string
    # ---------------------------------------------------------
    def test_6_get_context_llm_ready(self):
        """get_context() must return a non-empty formatted string."""
        print("\n[TEST 6] get_context() Returns LLM-Ready String")
        print("-" * 50)

        context = self.retriever.get_context(
            "fetch Jira ticket", top_k=2
        )

        self.assertIsInstance(context, str)
        self.assertGreater(len(context), 0)
        self.assertIn("Relevant Code Context", context)

        print(f"  [OK] Type    : {type(context)}")
        print(f"  [OK] Length  : {len(context)} chars")
        print(f"  [OK] Preview :")
        for line in context.split("\n")[:8]:
            print(f"       {line}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 7: Extension filter works
    # ---------------------------------------------------------
    def test_7_extension_filter(self):
        """ext_filter='.py' must only return Python files."""
        print("\n[TEST 7] Extension Filter Works")
        print("-" * 50)

        results = self.retriever.search(
            "function definition", top_k=5, ext_filter=".py"
        )

        for r in results:
            self.assertEqual(
                r.extension, ".py",
                f"Non-.py file leaked through: {r.source_path}"
            )

        print(f"  [OK] Results count  : {len(results)}")
        print(f"  [OK] All .py        : {all(r.extension == '.py' for r in results)}")
        if results:
            for r in results:
                print(f"       {r.source_path} ({r.extension})")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 8: is_ready() reflects store state
    # ---------------------------------------------------------
    def test_8_is_ready(self):
        """is_ready() must return True when store has data."""
        print("\n[TEST 8] is_ready() Reflects Store State")
        print("-" * 50)

        self.assertTrue(self.retriever.is_ready())
        print(f"  [OK] is_ready() : {self.retriever.is_ready()}")
        print(f"  [OK] chunk count: {self.retriever.store.count()}")
        print("  => PASS")


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  SEMANTIC RETRIEVER — FULL TEST PHASE")
    print("=" * 55)

    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite  = loader.loadTestsFromTestCase(TestRetriever)

    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 55)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    if result.wasSuccessful():
        print("  [ALL PASS] Semantic Retriever is production ready!")
    else:
        for f in result.failures + result.errors:
            print(f"  [FAIL] {f[0]}")
            print(f"         {f[1][:200]}")
    print("=" * 55 + "\n")
