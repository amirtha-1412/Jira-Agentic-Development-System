"""
tests/test_workflow.py
---------------------------------------------
LangGraph Workflow Testing Phase:
  - LangGraph installed        -> Success
  - No dependency conflicts     -> Success
  - State structure valid       -> Success
  - Fields accessible           -> Success
  - Nodes execute               -> Success
  - State updates               -> Success
  - Reasoning trace logs        -> Success
"""

import sys, io, unittest
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from workflows.state import WorkflowState, create_initial_state, state_summary
from workflows.nodes import requirement_node, developer_node, qa_node, pr_node

SAMPLE_TICKET = {
    "ticket_id":   "SCRUM-1",
    "title":       "Add forgot password functionality",
    "description": "Users must reset password via secure email token. Token expires in 24h.",
    "status":      "TODO",
    "priority":    "HIGH",
    "issue_type":  "Task",
    "assignee":    "Unassigned",
    "success":     True,
}


class TestLangGraph(unittest.TestCase):

    def test_1_langgraph_installed(self):
        print("\n[TEST 1] LangGraph Installed")
        print("-" * 50)
        try:
            from langgraph.graph import StateGraph, END
            print(f"  [OK] StateGraph imported : {StateGraph}")
            print(f"  [OK] END sentinel        : {END}")
            print("  => PASS")
        except ImportError as e:
            self.fail(f"LangGraph not installed: {e}")

    def test_2_no_dependency_conflicts(self):
        print("\n[TEST 2] No Dependency Conflicts")
        print("-" * 50)
        try:
            from langgraph.graph import StateGraph, END
            from langchain_groq import ChatGroq
            from langchain_core.messages import HumanMessage
            from vectorstore.retriever import CodeRetriever
            print("  [OK] langgraph     : OK")
            print("  [OK] langchain_groq: OK")
            print("  [OK] langchain_core: OK")
            print("  [OK] retriever     : OK")
            print("  => PASS — No conflicts")
        except Exception as e:
            self.fail(f"Dependency conflict: {e}")


class TestState(unittest.TestCase):

    def test_3_state_structure_valid(self):
        print("\n[TEST 3] State Structure Valid")
        print("-" * 50)
        state = create_initial_state("SCRUM-1")
        self.assertIsInstance(state, dict)
        required_keys = [
            "ticket_id", "ticket_data", "requirements", "summary",
            "functional_reqs", "technical_reqs", "implementation_steps",
            "affected_files", "risk_level", "reasoning_trace",
            "generated_code", "code_ready", "test_cases",
            "test_results", "test_status", "pr_title", "pr_description",
            "pr_ready", "current_stage", "completed_stages",
            "errors", "pipeline_status",
        ]
        for key in required_keys:
            self.assertIn(key, state, f"Missing key: {key}")
        print(f"  [OK] Keys count  : {len(state)}")
        print(f"  [OK] All required: {len(required_keys)} keys present")
        print("  => PASS")

    def test_4_fields_accessible(self):
        print("\n[TEST 4] Fields Accessible")
        print("-" * 50)
        state = create_initial_state("SCRUM-1", SAMPLE_TICKET)

        self.assertEqual(state["ticket_id"], "SCRUM-1")
        self.assertEqual(state["pipeline_status"], "initialized")
        self.assertEqual(state["current_stage"], "initialized")
        self.assertIsInstance(state["functional_reqs"], list)
        self.assertIsInstance(state["errors"], list)
        self.assertFalse(state["code_ready"])
        self.assertFalse(state["pr_ready"])

        summary = state_summary(state)
        self.assertIn("SCRUM-1", summary)
        print(f"  [OK] ticket_id       : {state['ticket_id']}")
        print(f"  [OK] pipeline_status : {state['pipeline_status']}")
        print(f"  [OK] state_summary   :\n  {summary}")
        print("  => PASS")


class TestNodes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n  [Setup] Running full pipeline...")
        # Start with fresh state + ticket data
        cls.state = create_initial_state("SCRUM-1", SAMPLE_TICKET)

        # Run requirement node (live LLM)
        print("  [Setup] Running requirement_node (LLM call)...")
        req_update = requirement_node(cls.state)
        cls.state.update(req_update)
        print(f"  [Setup] Requirement node done: {req_update.get('current_stage')}")

        # Run developer node
        dev_update = developer_node(cls.state)
        cls.state.update(dev_update)

        # Run QA node
        qa_update  = qa_node(cls.state)
        cls.state.update(qa_update)

        # Run PR node
        pr_update  = pr_node(cls.state)
        cls.state.update(pr_update)
        print(f"  [Setup] Full pipeline done: {cls.state.get('pipeline_status')}")

    def test_5_nodes_execute(self):
        print("\n[TEST 5] All Nodes Execute")
        print("-" * 50)
        self.assertIn("requirement", self.state["completed_stages"])
        self.assertIn("developer",   self.state["completed_stages"])
        self.assertIn("qa",          self.state["completed_stages"])
        self.assertIn("pr",          self.state["completed_stages"])
        print(f"  [OK] Completed stages : {self.state['completed_stages']}")
        print(f"  [OK] Pipeline status  : {self.state['pipeline_status']}")
        print("  => PASS")

    def test_6_state_updates(self):
        print("\n[TEST 6] State Updates Correctly")
        print("-" * 50)
        # Requirements populated
        self.assertGreater(len(self.state.get("functional_reqs", [])), 0)
        self.assertNotEqual(self.state.get("summary", ""), "")
        self.assertIn(self.state.get("risk_level"), ["LOW", "MEDIUM", "HIGH"])
        # Developer output
        self.assertIsInstance(self.state.get("generated_code"), dict)
        # QA output
        self.assertGreater(len(self.state.get("test_cases", [])), 0)
        # PR output
        self.assertNotEqual(self.state.get("pr_title", ""), "")
        print(f"  [OK] summary         : '{self.state['summary'][:60]}...'")
        print(f"  [OK] func_reqs       : {len(self.state['functional_reqs'])} items")
        print(f"  [OK] risk_level      : {self.state['risk_level']}")
        print(f"  [OK] test_cases      : {len(self.state['test_cases'])} items")
        print(f"  [OK] pr_title        : '{self.state['pr_title'][:50]}'")
        print("  => PASS")

    def test_7_reasoning_trace_logged(self):
        print("\n[TEST 7] Reasoning Trace Logged")
        print("-" * 50)
        trace = self.state.get("reasoning_trace", "")
        self.assertIsInstance(trace, str)
        self.assertGreater(len(trace), 50, "Reasoning trace too short")
        # Should have step-by-step reasoning
        self.assertTrue(
            any(kw in trace for kw in ["Step", "UNDERSTANDING", "REASONING", "password"]),
            f"Reasoning trace doesn't look valid: {trace[:100]}"
        )
        print(f"  [OK] Reasoning trace length : {len(trace)} chars")
        print(f"  [OK] Preview               : '{trace[:80]}...'")
        print("  => PASS")

    def test_8_engineering_tasks_generated(self):
        print("\n[TEST 8] Engineering Tasks Generated")
        print("-" * 50)
        tasks = self.state.get("engineering_tasks", "")
        self.assertGreater(len(tasks), 50)
        print(f"  [OK] Engineering tasks : {len(tasks)} chars")
        print(f"  [OK] Preview           : '{tasks[:80]}...'")
        print("  => PASS")

    def test_9_edge_cases_generated(self):
        print("\n[TEST 9] Edge Cases Generated")
        print("-" * 50)
        edges = self.state.get("edge_cases", "")
        self.assertGreater(len(edges), 50)
        print(f"  [OK] Edge cases : {len(edges)} chars")
        print(f"  [OK] Preview    : '{edges[:80]}...'")
        print("  => PASS")

    def test_10_pipeline_complete(self):
        print("\n[TEST 10] Full Pipeline State Summary")
        print("-" * 50)
        self.assertEqual(self.state["pipeline_status"], "completed")
        self.assertEqual(self.state["current_stage"], "completed")
        summary = state_summary(self.state)
        print(f"\n  --- Final Pipeline State ---")
        for line in summary.split("\n"):
            print(f"  {line}")
        print("  => PASS")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  LANGGRAPH WORKFLOW — FULL TEST PHASE")
    print("=" * 60)
    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite  = loader.loadTestsFromTestCase(TestLangGraph)
    suite.addTests(loader.loadTestsFromTestCase(TestState))
    suite.addTests(loader.loadTestsFromTestCase(TestNodes))
    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)
    print("\n" + "=" * 60)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    if result.wasSuccessful():
        print("  [ALL PASS] LangGraph Workflow is production ready!")
    else:
        for f in result.failures + result.errors:
            print(f"  [FAIL] {f[0]}\n         {f[1][:200]}")
    print("=" * 60 + "\n")
