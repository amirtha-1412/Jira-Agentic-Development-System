"""
tests/test_ticket_fetcher_full.py
---------------------------------------------
Full Testing Phase for Ticket Fetcher:
  - Valid ticket    -> JSON returned
  - Invalid ticket  -> Error response
  - Internet failure -> Graceful handling
"""

import sys
import io
import unittest
from unittest.mock import patch, MagicMock

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from backend.jira.ticket_fetcher import (
    fetch_ticket,
    fetch_multiple_tickets,
    fetch_open_tickets,
)


# =============================================================
# TEST SUITE
# =============================================================

class TestTicketFetcher(unittest.TestCase):

    # ---------------------------------------------------------
    # TEST 1: Valid Ticket -> JSON returned
    # ---------------------------------------------------------
    def test_1_valid_ticket_returns_json(self):
        """Valid ticket ID should return full structured JSON."""
        print("\n[TEST 1] Valid Ticket -> JSON Returned")
        print("-" * 50)

        result = fetch_ticket("SCRUM-1")

        self.assertTrue(result["success"],
                        f"Expected success=True, got error: {result.get('error')}")
        self.assertEqual(result["ticket_id"], "SCRUM-1")
        self.assertIn("summary",     result)
        self.assertIn("description", result)
        self.assertIn("status",      result)
        self.assertIn("priority",    result)
        self.assertIn("issue_type",  result)
        self.assertIn("agent_input", result)
        self.assertIsInstance(result["agent_input"], str)

        print(f"  [OK] ticket_id   : {result['ticket_id']}")
        print(f"  [OK] summary     : {result['summary']}")
        print(f"  [OK] status      : {result['status']}")
        print(f"  [OK] priority    : {result['priority']}")
        print(f"  [OK] issue_type  : {result['issue_type']}")
        print(f"  [OK] agent_input : present ({len(result['agent_input'])} chars)")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 2: Invalid Ticket -> Error Response
    # ---------------------------------------------------------
    def test_2_invalid_ticket_returns_error(self):
        """Non-existent ticket should return success=False with error message."""
        print("\n[TEST 2] Invalid Ticket -> Error Response")
        print("-" * 50)

        result = fetch_ticket("SCRUM-99999")

        self.assertFalse(result["success"],
                         "Expected success=False for invalid ticket.")
        self.assertIn("error", result)
        self.assertIsInstance(result["error"], str)
        self.assertTrue(len(result["error"]) > 0)

        print(f"  [OK] success     : {result['success']}")
        print(f"  [OK] error msg   : {result['error']}")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 3: Internet Failure -> Graceful Handling
    # ---------------------------------------------------------
    @patch("backend.jira.connector.requests.get")
    def test_3_internet_failure_graceful(self, mock_get):
        """Simulates a network failure — should return graceful error, not crash."""
        import requests as req
        print("\n[TEST 3] Internet Failure -> Graceful Handling")
        print("-" * 50)

        # Simulate connection error
        mock_get.side_effect = req.exceptions.ConnectionError("Network unreachable")

        result = fetch_ticket("SCRUM-1")

        self.assertFalse(result["success"],
                         "Expected success=False on network failure.")
        self.assertIn("error", result)
        self.assertNotIn("Traceback", str(result))  # No raw crash

        print(f"  [OK] success     : {result['success']}")
        print(f"  [OK] error msg   : {result['error']}")
        print("  => PASS — No crash, graceful error returned")

    # ---------------------------------------------------------
    # TEST 4: Timeout -> Graceful Handling
    # ---------------------------------------------------------
    @patch("backend.jira.connector.requests.get")
    def test_4_timeout_graceful(self, mock_get):
        """Simulates a request timeout — should handle gracefully."""
        import requests as req
        print("\n[TEST 4] Request Timeout -> Graceful Handling")
        print("-" * 50)

        mock_get.side_effect = req.exceptions.Timeout("Request timed out")

        result = fetch_ticket("SCRUM-1")

        self.assertFalse(result["success"])
        self.assertIn("error", result)

        print(f"  [OK] success     : {result['success']}")
        print(f"  [OK] error msg   : {result['error']}")
        print("  => PASS — Timeout handled gracefully")

    # ---------------------------------------------------------
    # TEST 5: Multiple Tickets (valid + invalid mixed)
    # ---------------------------------------------------------
    def test_5_multiple_tickets_mixed(self):
        """Fetch multiple tickets where one is valid and one is invalid."""
        print("\n[TEST 5] Multiple Tickets — Mixed Valid/Invalid")
        print("-" * 50)

        results = fetch_multiple_tickets(["SCRUM-1", "SCRUM-INVALID-9999"])

        self.assertEqual(len(results), 2)

        valid   = results[0]
        invalid = results[1]

        self.assertTrue(valid["success"],
                        f"SCRUM-1 should succeed: {valid.get('error')}")
        self.assertFalse(invalid["success"],
                         "Invalid ticket should fail")

        print(f"  [OK] SCRUM-1         : success={valid['success']} | {valid['summary']}")
        print(f"  [OK] SCRUM-INVALID   : success={invalid['success']} | {invalid['error']}")
        print("  => PASS")


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  JIRA TICKET FETCHER — FULL TEST PHASE")
    print("=" * 55)

    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None  # Preserve order
    suite  = loader.loadTestsFromTestCase(TestTicketFetcher)

    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 55)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    if result.wasSuccessful():
        print("  [ALL PASS] Ticket Fetcher is production ready!")
    else:
        for f in result.failures + result.errors:
            print(f"  [FAIL] {f[0]}: {f[1][:100]}")
    print("=" * 55 + "\n")
