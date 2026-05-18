"""
tests/test_parser_full.py
---------------------------------------------
Full Testing Phase for Jira Parser:
  - Missing fields   -> Safe fallback
  - Empty values     -> No crash
  - Complex tickets  -> Correct parsing
"""

import sys
import io
import unittest
from unittest.mock import patch

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from backend.jira.parser import (
    parse_ticket,
    parse_multiple_tickets,
    _clean_text,
    _normalize_priority,
    _normalize_status,
)


# =============================================================
# MOCK HELPERS — Simulate fetch_ticket responses
# =============================================================

def _mock_fetch(overrides: dict = {}) -> dict:
    """Returns a base valid fetch_ticket response with optional overrides."""
    base = {
        "success":     True,
        "ticket_id":   "SCRUM-TEST",
        "summary":     "Test ticket summary",
        "description": "Test description text",
        "priority":    "High",
        "status":      "To Do",
        "issue_type":  "Task",
        "assignee":    "Unassigned",
        "reporter":    "Amirtha",
        "labels":      [],
        "created":     "2024-01-01",
        "updated":     "2024-01-02",
        "agent_input": "...",
    }
    base.update(overrides)
    return base


# =============================================================
# TEST SUITE
# =============================================================

class TestJiraParser(unittest.TestCase):

    # ---------------------------------------------------------
    # TEST 1: Missing Fields -> Safe Fallback
    # ---------------------------------------------------------
    @patch("backend.jira.parser.fetch_ticket")
    def test_1_missing_fields_safe_fallback(self, mock_fetch):
        """Missing priority/status/description should return safe defaults."""
        print("\n[TEST 1] Missing Fields -> Safe Fallback")
        print("-" * 50)

        mock_fetch.return_value = _mock_fetch({
            "priority":    None,
            "status":      None,
            "description": None,
            "summary":     None,
        })

        result = parse_ticket("SCRUM-TEST")

        self.assertTrue(result["success"])
        self.assertEqual(result["priority"],    "NONE")
        self.assertEqual(result["title"],       "Not provided.")
        self.assertEqual(result["description"], "Not provided.")
        # Status with None → should not crash
        self.assertIsInstance(result["status"], str)
        self.assertIn("agent_prompt", result)

        print(f"  [OK] priority    : {result['priority']}  (fallback from None)")
        print(f"  [OK] title       : {result['title']}     (fallback from None)")
        print(f"  [OK] description : {result['description']} (fallback from None)")
        print(f"  [OK] status      : {result['status']}")
        print(f"  [OK] agent_prompt: present ({len(result['agent_prompt'])} chars)")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 2: Empty String Values -> No Crash
    # ---------------------------------------------------------
    @patch("backend.jira.parser.fetch_ticket")
    def test_2_empty_values_no_crash(self, mock_fetch):
        """Empty strings should be handled gracefully without crashing."""
        print("\n[TEST 2] Empty Values -> No Crash")
        print("-" * 50)

        mock_fetch.return_value = _mock_fetch({
            "summary":     "",
            "description": "",
            "priority":    "",
            "status":      "",
            "assignee":    "",
            "issue_type":  "",
        })

        try:
            result = parse_ticket("SCRUM-TEST")
            self.assertTrue(result["success"])
            self.assertIsInstance(result["title"],       str)
            self.assertIsInstance(result["description"], str)
            self.assertIsInstance(result["priority"],    str)
            self.assertIsInstance(result["status"],      str)
            self.assertIsInstance(result["agent_prompt"],str)

            print(f"  [OK] title       : '{result['title']}'")
            print(f"  [OK] description : '{result['description']}'")
            print(f"  [OK] priority    : '{result['priority']}'")
            print(f"  [OK] status      : '{result['status']}'")
            print("  => PASS — No crash on empty values")
        except Exception as e:
            self.fail(f"Parser crashed on empty values: {e}")

    # ---------------------------------------------------------
    # TEST 3: Complex Ticket -> Correct Parsing
    # ---------------------------------------------------------
    @patch("backend.jira.parser.fetch_ticket")
    def test_3_complex_ticket_correct_parsing(self, mock_fetch):
        """Complex multi-line description should be flattened and parsed correctly."""
        print("\n[TEST 3] Complex Ticket -> Correct Parsing")
        print("-" * 50)

        complex_desc = (
            "  As a user, I want to reset my password.\n\n"
            "  Acceptance Criteria:\n"
            "  - Must send email OTP\n"
            "  - Token expires in 15 minutes\n"
            "  - Rate limit: 3 attempts per hour\n\n"
            "  Technical Notes:\n"
            "  - Use JWT for token generation\n"
            "  - Store hashed token in DB\n"
        )

        mock_fetch.return_value = _mock_fetch({
            "summary":     "  Implement Password Reset Flow  ",
            "description": complex_desc,
            "priority":    "Highest",
            "status":      "In Progress",
            "issue_type":  "Story",
        })

        result = parse_ticket("SCRUM-TEST")

        self.assertTrue(result["success"])
        # Title should be stripped of whitespace
        self.assertEqual(result["title"], "Implement Password Reset Flow")
        # Priority mapping
        self.assertEqual(result["priority"], "HIGH")
        # Status mapping
        self.assertEqual(result["status"], "IN_PROGRESS")
        # Description should be cleaned (no leading/trailing whitespace)
        self.assertNotIn("\n\n", result["description"])
        self.assertNotIn("  ", result["description"])

        print(f"  [OK] title       : '{result['title']}'  (whitespace stripped)")
        print(f"  [OK] priority    : '{result['priority']}'  (Highest -> HIGH)")
        print(f"  [OK] status      : '{result['status']}'  (In Progress -> IN_PROGRESS)")
        print(f"  [OK] description : '{result['description'][:70]}...'  (flattened)")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 4: Priority Normalization All Cases
    # ---------------------------------------------------------
    def test_4_priority_normalization(self):
        """All priority values should normalize correctly."""
        print("\n[TEST 4] Priority Normalization")
        print("-" * 50)

        cases = {
            "Highest": "HIGH",
            "High":    "HIGH",
            "Medium":  "MEDIUM",
            "Low":     "LOW",
            "Lowest":  "LOW",
            "None":    "NONE",
            "":        "NONE",
            "Unknown": "NONE",
        }

        for raw, expected in cases.items():
            result = _normalize_priority(raw)
            self.assertEqual(result, expected,
                             f"Priority '{raw}' should map to '{expected}', got '{result}'")
            print(f"  [OK] '{raw}' -> '{result}'")

        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 5: Status Normalization All Cases
    # ---------------------------------------------------------
    def test_5_status_normalization(self):
        """All status values should normalize correctly."""
        print("\n[TEST 5] Status Normalization")
        print("-" * 50)

        cases = {
            "To Do":       "TODO",
            "In Progress": "IN_PROGRESS",
            "In Review":   "IN_REVIEW",
            "Done":        "DONE",
            "Closed":      "DONE",
            "Resolved":    "DONE",
        }

        for raw, expected in cases.items():
            result = _normalize_status(raw)
            self.assertEqual(result, expected,
                             f"Status '{raw}' should map to '{expected}', got '{result}'")
            print(f"  [OK] '{raw}' -> '{result}'")

        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 6: Failed Fetch -> Error Propagated
    # ---------------------------------------------------------
    @patch("backend.jira.parser.fetch_ticket")
    def test_6_failed_fetch_propagated(self, mock_fetch):
        """If fetch fails, parser should propagate error cleanly."""
        print("\n[TEST 6] Failed Fetch -> Error Propagated")
        print("-" * 50)

        mock_fetch.return_value = {
            "success":   False,
            "ticket_id": "SCRUM-999",
            "error":     "Ticket not found.",
        }

        result = parse_ticket("SCRUM-999")

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Ticket not found.")

        print(f"  [OK] success  : {result['success']}")
        print(f"  [OK] error    : {result['error']}")
        print("  => PASS")


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  JIRA PARSER — FULL TEST PHASE")
    print("=" * 55)

    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite  = loader.loadTestsFromTestCase(TestJiraParser)

    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 55)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    if result.wasSuccessful():
        print("  [ALL PASS] Parser is production ready!")
    else:
        for f in result.failures + result.errors:
            print(f"  [FAIL] {f[0]}: {f[1][:120]}")
    print("=" * 55 + "\n")
