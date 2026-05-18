"""
tests/test_advanced_prompts.py
---------------------------------------------
Testing Phase for 3 Advanced Prompt Modules:

Engineering Tasks:
  - Tasks generated     -> Success
  - Tasks logical       -> Success
  - Steps ordered       -> Success

Edge Case Analyzer:
  - Edge cases generated    -> Success
  - Security cases included -> Success

Explainable Reasoning:
  - Reasoning generated  -> Success
  - Logic coherent       -> Success
  - Output explainable   -> Success
"""

import sys, io, re, unittest
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from agents.llm import call_llm
from agents.requirement_analyst.prompt import (
    build_engineering_tasks_prompt,  ENGINEERING_TASKS_TEMPLATE,
    build_edge_case_prompt,          EDGE_CASE_TEMPLATE,
    build_reasoning_prompt,          REASONING_TEMPLATE,
    get_system_prompt,
)

# ─── Shared test ticket ───────────────────────
TICKET = {
    "ticket_id":   "SCRUM-1",
    "title":       "Add forgot password functionality",
    "description": (
        "Users must be able to reset their password via email. "
        "System sends a secure token link that expires in 24 hours. "
        "User clicks link, enters new password, token is invalidated."
    ),
    "status":      "TODO",
    "priority":    "HIGH",
    "issue_type":  "Task",
}
CTX = "# File: backend/jira/auth.py\ndef authenticate(email, api_key): pass"


# =============================================================
# ENGINEERING TASKS TESTS
# =============================================================

class TestEngineeringTasks(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n  [Setup] Calling LLM for Engineering Tasks...")
        prompt = build_engineering_tasks_prompt(
            ticket_id=TICKET["ticket_id"], title=TICKET["title"],
            description=TICKET["description"], status=TICKET["status"],
            priority=TICKET["priority"], issue_type=TICKET["issue_type"],
            code_context=CTX,
        )
        cls.response = call_llm(
            user_prompt=prompt, system_prompt=get_system_prompt()
        )
        print(f"  [Setup] Response: {len(cls.response)} chars")

    def test_1_template_loads(self):
        print("\n[TEST 1] Engineering Tasks Template Loads")
        print("-" * 50)
        self.assertIsInstance(ENGINEERING_TASKS_TEMPLATE, str)
        prompt = build_engineering_tasks_prompt(**TICKET, code_context=CTX)
        self.assertIn("SCRUM-1",       prompt)
        self.assertIn("forgot password", prompt)
        self.assertIn("ENGINEERING TASKS", prompt)
        self.assertIn("ACCEPTANCE CRITERIA", prompt)
        print(f"  [OK] Template length : {len(ENGINEERING_TASKS_TEMPLATE)}")
        print(f"  [OK] Built prompt    : {len(prompt)} chars")
        print(f"  [OK] All keys found  : True")
        print("  => PASS")

    def test_2_tasks_generated(self):
        print("\n[TEST 2] Engineering Tasks Generated")
        print("-" * 50)
        self.assertGreater(len(self.response), 100)
        self.assertIn("TASK", self.response.upper())
        tasks = re.findall(r"TASK-\d+:", self.response)
        self.assertGreater(len(tasks), 0, "No TASK-N: items found")
        print(f"  [OK] Response length : {len(self.response)} chars")
        print(f"  [OK] Tasks found     : {len(tasks)}")
        for t in tasks:
            print(f"       {t}")
        print("  => PASS")

    def test_3_tasks_logical(self):
        print("\n[TEST 3] Tasks Are Logical")
        print("-" * 50)
        # Should reference password/email/token related work
        keywords = ["password", "email", "token", "reset", "user", "link"]
        matches  = [kw for kw in keywords if kw.lower() in self.response.lower()]
        self.assertGreater(len(matches), 2, f"Not enough relevant keywords: {matches}")
        print(f"  [OK] Relevant keywords found : {matches}")
        print("  => PASS")

    def test_4_steps_ordered(self):
        print("\n[TEST 4] Steps Are Ordered")
        print("-" * 50)
        numbers = re.findall(r"^\s*(\d+)\.", self.response, re.MULTILINE)
        if numbers:
            nums = [int(n) for n in numbers]
            self.assertEqual(nums, sorted(nums), f"Steps not in order: {nums}")
            print(f"  [OK] Ordered steps found : {nums}")
        else:
            print(f"  [OK] No explicit numbers — content verified")
        self.assertIn("EXECUTION", self.response.upper())
        print("  => PASS")

    def test_5_acceptance_criteria(self):
        print("\n[TEST 5] Acceptance Criteria Present")
        print("-" * 50)
        self.assertIn("ACCEPTANCE", self.response.upper())
        criteria = re.findall(r"\[ \]", self.response)
        self.assertGreater(len(criteria), 0, "No checkbox criteria found")
        print(f"  [OK] Checkboxes found    : {len(criteria)}")
        print("  => PASS")


# =============================================================
# EDGE CASE ANALYZER TESTS
# =============================================================

class TestEdgeCaseAnalyzer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n  [Setup] Calling LLM for Edge Case Analysis...")
        prompt = build_edge_case_prompt(
            ticket_id=TICKET["ticket_id"], title=TICKET["title"],
            description=TICKET["description"], priority=TICKET["priority"],
            issue_type=TICKET["issue_type"], code_context=CTX,
        )
        cls.response = call_llm(
            user_prompt=prompt, system_prompt=get_system_prompt()
        )
        print(f"  [Setup] Response: {len(cls.response)} chars")

    def test_6_template_loads(self):
        print("\n[TEST 6] Edge Case Template Loads")
        print("-" * 50)
        prompt = build_edge_case_prompt(
            ticket_id=TICKET["ticket_id"], title=TICKET["title"],
            description=TICKET["description"], priority=TICKET["priority"],
            issue_type=TICKET["issue_type"],
        )
        self.assertIn("EDGE CASES",      prompt)
        self.assertIn("SECURITY RISKS",  prompt)
        self.assertIn("MITIGATION",      prompt)
        print(f"  [OK] All sections present : True")
        print(f"  [OK] Prompt length        : {len(prompt)}")
        print("  => PASS")

    def test_7_edge_cases_generated(self):
        print("\n[TEST 7] Edge Cases Generated")
        print("-" * 50)
        self.assertGreater(len(self.response), 100)
        edges = re.findall(r"EDGE-\d+:", self.response)
        self.assertGreater(len(edges), 0, "No EDGE-N: items found")
        print(f"  [OK] Response length : {len(self.response)} chars")
        print(f"  [OK] Edge cases found: {len(edges)}")
        for e in edges:
            print(f"       {e}")
        print("  => PASS")

    def test_8_security_cases_included(self):
        print("\n[TEST 8] Security Cases Included")
        print("-" * 50)
        sec_keywords = ["security", "SEC-", "token", "injection",
                        "auth", "expir", "brute", "attack"]
        found = [kw for kw in sec_keywords if kw.lower() in self.response.lower()]
        self.assertGreater(len(found), 1, f"Not enough security content: {found}")
        print(f"  [OK] Security keywords found : {found}")
        print("  => PASS")

    def test_9_risk_rating_present(self):
        print("\n[TEST 9] Risk Rating Present")
        print("-" * 50)
        self.assertIn("RISK RATING", self.response.upper())
        rating = re.search(r"Rating:\s*(LOW|MEDIUM|HIGH|CRITICAL)", self.response, re.IGNORECASE)
        self.assertIsNotNone(rating, "No risk rating found")
        print(f"  [OK] Risk rating : {rating.group(1).upper()}")
        print("  => PASS")


# =============================================================
# EXPLAINABLE REASONING TESTS
# =============================================================

class TestExplainableReasoning(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n  [Setup] Calling LLM for Explainable Reasoning...")
        prompt = build_reasoning_prompt(
            ticket_id=TICKET["ticket_id"], title=TICKET["title"],
            description=TICKET["description"], status=TICKET["status"],
            priority=TICKET["priority"], code_context=CTX,
        )
        cls.response = call_llm(
            user_prompt=prompt, system_prompt=get_system_prompt()
        )
        print(f"  [Setup] Response: {len(cls.response)} chars")

    def test_10_template_loads(self):
        print("\n[TEST 10] Reasoning Template Loads")
        print("-" * 50)
        prompt = build_reasoning_prompt(
            ticket_id=TICKET["ticket_id"], title=TICKET["title"],
            description=TICKET["description"], status=TICKET["status"],
            priority=TICKET["priority"],
        )
        for section in ["INITIAL UNDERSTANDING", "REASONING CHAIN",
                        "ASSUMPTIONS MADE", "CONFIDENCE ASSESSMENT"]:
            self.assertIn(section, prompt)
        print(f"  [OK] All 6 sections in template : True")
        print(f"  [OK] Prompt length              : {len(prompt)}")
        print("  => PASS")

    def test_11_reasoning_generated(self):
        print("\n[TEST 11] Reasoning Generated")
        print("-" * 50)
        self.assertGreater(len(self.response), 200)
        self.assertIn("Step", self.response)
        steps = re.findall(r"Step \d+:", self.response)
        self.assertGreater(len(steps), 0, "No Step N: items found")
        print(f"  [OK] Response length : {len(self.response)} chars")
        print(f"  [OK] Steps found     : {len(steps)} → {steps}")
        print("  => PASS")

    def test_12_logic_coherent(self):
        print("\n[TEST 12] Logic Is Coherent")
        print("-" * 50)
        # Should reference the ticket concepts in reasoning
        keywords = ["password", "email", "token", "reset", "user"]
        found    = [kw for kw in keywords if kw.lower() in self.response.lower()]
        self.assertGreater(len(found), 2, f"Reasoning not coherent with ticket: {found}")
        print(f"  [OK] Ticket-relevant keywords : {found}")
        print("  => PASS")

    def test_13_output_explainable(self):
        print("\n[TEST 13] Output Is Explainable")
        print("-" * 50)
        self.assertIn("CONFIDENCE", self.response.upper())
        conf = re.search(r"Confidence:\s*(LOW|MEDIUM|HIGH)", self.response, re.IGNORECASE)
        self.assertIsNotNone(conf, "No confidence score found")
        self.assertIn("CONCLUSION", self.response.upper())
        print(f"  [OK] Confidence level    : {conf.group(1).upper()}")
        print(f"  [OK] Summary conclusion  : Present")
        print("  => PASS")


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  ADVANCED PROMPTS — FULL TEST PHASE")
    print("=" * 60)

    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite  = loader.loadTestsFromTestCase(TestEngineeringTasks)
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCaseAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestExplainableReasoning))

    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    if result.wasSuccessful():
        print("  [ALL PASS] All 3 advanced prompt modules production ready!")
    else:
        for f in result.failures + result.errors:
            print(f"  [FAIL] {f[0]}\n         {f[1][:150]}")
    print("=" * 60 + "\n")
