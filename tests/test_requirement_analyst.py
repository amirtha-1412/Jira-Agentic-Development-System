"""
tests/test_requirement_analyst.py
---------------------------------------------
Testing Phase:
  - Prompt loads              -> Success
  - Variables interpolate     -> Success
  - Requirement analysis generated -> Success
  - Logical structure maintained   -> Success
  - No empty output                -> Success
"""

import sys, io, os, unittest
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from agents.requirement_analyst.prompt import build_analysis_prompt, get_system_prompt, ANALYSIS_PROMPT_TEMPLATE
from agents.requirement_analyst.analyzer import RequirementAnalyst, AnalysisResult

SAMPLE_TICKET = {
    "ticket_id":   "SCRUM-1",
    "title":       "Add forgot password functionality",
    "description": "Users must be able to reset password via email. Token expires in 24h.",
    "status":      "TODO",
    "priority":    "HIGH",
    "issue_type":  "Task",
    "assignee":    "Unassigned",
}


class TestPromptTemplate(unittest.TestCase):

    def test_1_prompt_loads(self):
        print("\n[TEST 1] Prompt Loads")
        print("-" * 50)
        self.assertIsInstance(ANALYSIS_PROMPT_TEMPLATE, str)
        self.assertGreater(len(ANALYSIS_PROMPT_TEMPLATE), 100)
        sys_p = get_system_prompt()
        self.assertIn("Requirement Analyst", sys_p)
        print(f"  [OK] Template length   : {len(ANALYSIS_PROMPT_TEMPLATE)} chars")
        print(f"  [OK] System prompt len : {len(sys_p)} chars")
        print("  => PASS")

    def test_2_variables_interpolate(self):
        print("\n[TEST 2] Variables Interpolate")
        print("-" * 50)
        prompt = build_analysis_prompt(**SAMPLE_TICKET, code_context="# test context")
        for val in ["SCRUM-1", "forgot password", "HIGH", "TODO", "Task", "test context"]:
            self.assertIn(val, prompt, f"Missing '{val}' in prompt")
            print(f"  [OK] '{val}' found in prompt")
        print("  => PASS")

    def test_3_fallback_no_context(self):
        print("\n[TEST 3] Fallback Template (No Context)")
        print("-" * 50)
        prompt = build_analysis_prompt(**SAMPLE_TICKET, code_context="")
        self.assertIn("SCRUM-1", prompt)
        self.assertNotIn("Relevant Codebase Context", prompt)
        print(f"  [OK] No-context template used : len={len(prompt)}")
        print("  => PASS")


class TestAnalyzer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n  [Setup] Initializing analyst (no retriever)...")
        cls.analyst = RequirementAnalyst(use_retriever=False)

    def test_4_analysis_generated(self):
        print("\n[TEST 4] Requirement Analysis Generated")
        print("-" * 50)
        result = self.analyst.analyze(SAMPLE_TICKET)
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(result.success, f"Analysis failed: {result.error}")
        self.assertEqual(result.ticket_id, "SCRUM-1")
        print(f"  [OK] success      : {result.success}")
        print(f"  [OK] ticket_id    : {result.ticket_id}")
        print(f"  [OK] raw_response : {len(result.raw_response)} chars")
        print("  => PASS")

    def test_5_logical_structure_maintained(self):
        print("\n[TEST 5] Logical Structure Maintained")
        print("-" * 50)
        result = self.analyst.analyze(SAMPLE_TICKET)
        self.assertTrue(result.success)
        self.assertGreater(len(result.summary), 10, "Summary too short")
        self.assertGreater(len(result.functional_requirements), 0, "No func reqs")
        self.assertGreater(len(result.implementation_steps), 0, "No steps")
        self.assertIn(result.risk_level, ["LOW", "MEDIUM", "HIGH"])
        print(f"  [OK] summary       : '{result.summary[:70]}...'")
        print(f"  [OK] func_reqs     : {len(result.functional_requirements)}")
        print(f"  [OK] tech_reqs     : {len(result.technical_requirements)}")
        print(f"  [OK] steps         : {len(result.implementation_steps)}")
        print(f"  [OK] risk_level    : {result.risk_level}")
        print("  => PASS")

    def test_6_no_empty_output(self):
        print("\n[TEST 6] No Empty Output")
        print("-" * 50)
        result = self.analyst.analyze(SAMPLE_TICKET)
        self.assertTrue(result.success)
        self.assertNotEqual(result.summary.strip(), "")
        self.assertNotEqual(result.raw_response.strip(), "")
        self.assertGreater(len(result.functional_requirements), 0)
        self.assertGreater(len(result.implementation_steps), 0)
        print(f"  [OK] summary not empty       : True")
        print(f"  [OK] raw_response not empty  : True ({len(result.raw_response)} chars)")
        print(f"  [OK] func_reqs not empty     : {len(result.functional_requirements)} items")
        print(f"  [OK] steps not empty         : {len(result.implementation_steps)} items")
        print("  => PASS")

    def test_7_to_dict_valid(self):
        print("\n[TEST 7] to_dict() Returns Valid Structure")
        print("-" * 50)
        result = self.analyst.analyze(SAMPLE_TICKET)
        d = result.to_dict()
        required = ["ticket_id","title","summary","functional_requirements",
                    "technical_requirements","implementation_steps","risk_level","success"]
        for key in required:
            self.assertIn(key, d)
        print(f"  [OK] Dict keys : {list(d.keys())}")
        print("  => PASS")

    def test_8_error_handling(self):
        print("\n[TEST 8] Error Handling — Bad Ticket")
        print("-" * 50)
        result = self.analyst.analyze({})
        self.assertIsInstance(result, AnalysisResult)
        # Either succeeds with empty fields or fails gracefully
        print(f"  [OK] success : {result.success}")
        print(f"  [OK] error   : '{result.error[:60]}'")
        print("  => PASS — No crash")


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  REQUIREMENT ANALYST — FULL TEST PHASE")
    print("=" * 55)
    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite  = loader.loadTestsFromTestCase(TestPromptTemplate)
    suite.addTests(loader.loadTestsFromTestCase(TestAnalyzer))
    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)
    print("\n" + "=" * 55)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    if result.wasSuccessful():
        print("  [ALL PASS] Requirement Analyst is production ready!")
    else:
        for f in result.failures + result.errors:
            print(f"  [FAIL] {f[0]}\n         {f[1][:150]}")
    print("=" * 55 + "\n")
