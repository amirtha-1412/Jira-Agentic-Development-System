"""
tests/test_ai_format.py
---------------------------------------------
Testing Phase for AI-Ready Format:
  - JSON structure valid   -> Yes
  - Empty fields handled   -> Yes
  - Stable format          -> Yes
"""

import sys
import io
import json
import unittest
from unittest.mock import patch

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from backend.jira.parser import to_ai_format, to_ai_format_json


# =============================================================
# MOCK HELPERS
# =============================================================

def _mock_parse(overrides: dict = {}):
    base = {
        "success":     True,
        "ticket_id":   "SCRUM-1",
        "title":       "Add forgot password functionality",
        "description": "Create password reset API using email verification.",
        "priority":    "HIGH",
        "status":      "TODO",
        "issue_type":  "Task",
        "assignee":    "Unassigned",
        "agent_prompt": (
            "Ticket    : SCRUM-1\n"
            "Title     : Add forgot password functionality\n"
            "Priority  : HIGH\nStatus    : TODO\n"
            "Type      : Task\nAssignee  : Unassigned\n"
            "\nDescription:\nCreate password reset API.\n"
        ),
    }
    base.update(overrides)
    return base


# =============================================================
# TEST SUITE
# =============================================================

class TestAIFormat(unittest.TestCase):

    # ---------------------------------------------------------
    # TEST 1: JSON Structure Valid
    # ---------------------------------------------------------
    @patch("backend.jira.parser.parse_ticket")
    def test_1_json_structure_valid(self, mock_parse):
        """AI format must contain all required top-level keys and nested blocks."""
        print("\n[TEST 1] JSON Structure Valid")
        print("-" * 50)

        mock_parse.return_value = _mock_parse()
        result = to_ai_format("SCRUM-1")

        # Top-level keys
        self.assertIn("schema_version", result)
        self.assertIn("success",        result)
        self.assertIn("generated_at",   result)
        self.assertIn("ticket",         result)
        self.assertIn("agent",          result)
        self.assertTrue(result["success"])
        self.assertEqual(result["schema_version"], "1.0")

        # ticket block
        ticket = result["ticket"]
        for key in ["id", "title", "description", "priority", "status", "issue_type", "assignee"]:
            self.assertIn(key, ticket, f"Missing ticket.{key}")

        # agent block
        agent = result["agent"]
        for key in ["target", "prompt", "instructions"]:
            self.assertIn(key, agent, f"Missing agent.{key}")

        self.assertEqual(agent["target"], "requirement_analyst")

        print(f"  [OK] schema_version : {result['schema_version']}")
        print(f"  [OK] generated_at   : {result['generated_at']}")
        print(f"  [OK] ticket keys    : {list(ticket.keys())}")
        print(f"  [OK] agent.target   : {agent['target']}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 2: Valid JSON String Output
    # ---------------------------------------------------------
    @patch("backend.jira.parser.parse_ticket")
    def test_2_valid_json_string(self, mock_parse):
        """to_ai_format_json must return a valid parseable JSON string."""
        print("\n[TEST 2] Valid JSON String Output")
        print("-" * 50)

        mock_parse.return_value = _mock_parse()
        json_str = to_ai_format_json("SCRUM-1")

        self.assertIsInstance(json_str, str)
        try:
            parsed = json.loads(json_str)
            self.assertIn("ticket", parsed)
            self.assertIn("agent",  parsed)
            print(f"  [OK] JSON is valid and parseable")
            print(f"  [OK] Length : {len(json_str)} chars")
            print(f"  [OK] Keys   : {list(parsed.keys())}")
        except json.JSONDecodeError as e:
            self.fail(f"Invalid JSON output: {e}")

        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 3: Empty Fields Handled
    # ---------------------------------------------------------
    @patch("backend.jira.parser.parse_ticket")
    def test_3_empty_fields_handled(self, mock_parse):
        """Empty/None fields in parsed data must not crash AI format conversion."""
        print("\n[TEST 3] Empty Fields Handled")
        print("-" * 50)

        mock_parse.return_value = _mock_parse({
            "title":       "Not provided.",
            "description": "Not provided.",
            "priority":    "NONE",
            "status":      "NONE",
            "assignee":    "",
            "agent_prompt": "Ticket : SCRUM-1\n",
        })

        try:
            result = to_ai_format("SCRUM-1")
            self.assertTrue(result["success"])
            t = result["ticket"]
            self.assertEqual(t["title"],       "Not provided.")
            self.assertEqual(t["description"], "Not provided.")
            self.assertEqual(t["priority"],    "NONE")
            self.assertEqual(t["status"],      "NONE")

            print(f"  [OK] title       : '{t['title']}'")
            print(f"  [OK] description : '{t['description']}'")
            print(f"  [OK] priority    : '{t['priority']}'")
            print(f"  [OK] status      : '{t['status']}'")
            print("  => PASS — No crash on empty fields")
        except Exception as e:
            self.fail(f"Crashed on empty fields: {e}")

    # ---------------------------------------------------------
    # TEST 4: Stable Format (same input = same structure)
    # ---------------------------------------------------------
    @patch("backend.jira.parser.parse_ticket")
    def test_4_stable_format(self, mock_parse):
        """Same input must always produce identical structure (stable schema)."""
        print("\n[TEST 4] Stable Format")
        print("-" * 50)

        mock_parse.return_value = _mock_parse()

        result_1 = to_ai_format("SCRUM-1")
        result_2 = to_ai_format("SCRUM-1")

        # Structure must be identical (keys, nested keys)
        self.assertEqual(set(result_1.keys()),          set(result_2.keys()))
        self.assertEqual(set(result_1["ticket"].keys()), set(result_2["ticket"].keys()))
        self.assertEqual(set(result_1["agent"].keys()),  set(result_2["agent"].keys()))

        # Core values must be identical
        self.assertEqual(result_1["ticket"]["title"],    result_2["ticket"]["title"])
        self.assertEqual(result_1["ticket"]["priority"], result_2["ticket"]["priority"])
        self.assertEqual(result_1["agent"]["target"],    result_2["agent"]["target"])

        print(f"  [OK] Top-level keys  : {sorted(result_1.keys())}")
        print(f"  [OK] Ticket keys     : {sorted(result_1['ticket'].keys())}")
        print(f"  [OK] Agent keys      : {sorted(result_1['agent'].keys())}")
        print(f"  [OK] title match     : {result_1['ticket']['title'] == result_2['ticket']['title']}")
        print(f"  [OK] priority match  : {result_1['ticket']['priority'] == result_2['ticket']['priority']}")
        print("  => PASS — Schema is stable across calls")

    # ---------------------------------------------------------
    # TEST 5: Failed Parse -> Error Format Valid
    # ---------------------------------------------------------
    @patch("backend.jira.parser.parse_ticket")
    def test_5_failed_parse_error_format(self, mock_parse):
        """Failed parse must still return valid schema with error info."""
        print("\n[TEST 5] Failed Parse -> Error Format Valid")
        print("-" * 50)

        mock_parse.return_value = {
            "success":   False,
            "ticket_id": "SCRUM-99",
            "error":     "Ticket not found.",
        }

        result = to_ai_format("SCRUM-99")

        self.assertFalse(result["success"])
        self.assertIn("schema_version", result)
        self.assertIn("error",          result)
        self.assertIn("generated_at",   result)
        self.assertEqual(result["schema_version"], "1.0")

        print(f"  [OK] success        : {result['success']}")
        print(f"  [OK] schema_version : {result['schema_version']}")
        print(f"  [OK] error          : {result['error']}")
        print(f"  [OK] generated_at   : {result['generated_at']}")
        print("  => PASS")


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  PARSER AI FORMAT — FULL TEST PHASE")
    print("=" * 55)

    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite  = loader.loadTestsFromTestCase(TestAIFormat)

    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 55)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    if result.wasSuccessful():
        print("  [ALL PASS] AI format is production ready!")
    else:
        for f in result.failures + result.errors:
            print(f"  [FAIL] {f[0]}: {f[1][:120]}")
    print("=" * 55 + "\n")
