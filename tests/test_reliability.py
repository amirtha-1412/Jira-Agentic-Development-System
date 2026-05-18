"""
tests/test_reliability.py
---------------------------------------------
Reliability Testing Phase:
  - Wrong ticket ID  -> No crash
  - API failure      -> Safe error
  - Missing fields   -> Graceful handling
"""

import sys
import io
import unittest
from unittest.mock import patch

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from backend.jira.ticket_fetcher import fetch_ticket, fetch_multiple_tickets, fetch_open_tickets
from backend.jira.parser import parse_ticket, to_ai_format


# =============================================================
# TEST SUITE
# =============================================================

class TestReliability(unittest.TestCase):

    # ---------------------------------------------------------
    # TEST 1: Wrong ticket ID -> No crash
    # ---------------------------------------------------------
    def test_1_wrong_ticket_id_no_crash(self):
        """Non-existent or malformed ticket IDs must not crash."""
        print("\n[TEST 1] Wrong Ticket ID -> No Crash")
        print("-" * 50)

        bad_ids = [
            "SCRUM-99999",     # valid format, doesn't exist
            "INVALID",         # no hyphen
            "",                # empty string
            "   ",             # whitespace only
            "123",             # numeric only
        ]

        for tid in bad_ids:
            try:
                result = fetch_ticket(tid)
                self.assertIsInstance(result, dict)
                self.assertIn("success", result)
                self.assertFalse(result["success"],
                                 f"Expected failure for bad ID '{tid}'")
                self.assertIn("error", result)
                print(f"  [OK] '{tid}' -> error: {result['error'][:60]}")
            except Exception as e:
                self.fail(f"fetch_ticket('{tid}') crashed: {e}")

        print("  => PASS — No crash on any bad ticket ID")

    # ---------------------------------------------------------
    # TEST 2: API failure -> Safe error
    # ---------------------------------------------------------
    @patch("backend.jira.connector.requests.get")
    def test_2_api_failure_safe_error(self, mock_get):
        """Simulated API failures must return structured errors, not crashes."""
        import requests as req
        print("\n[TEST 2] API Failure -> Safe Error")
        print("-" * 50)

        # 2a: Connection error
        mock_get.side_effect = req.exceptions.ConnectionError("Network down")
        result = fetch_ticket("SCRUM-1")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        print(f"  [OK] ConnectionError  -> '{result['error']}'")

        # 2b: Timeout
        mock_get.side_effect = req.exceptions.Timeout("Timed out")
        result = fetch_ticket("SCRUM-1")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        print(f"  [OK] Timeout          -> '{result['error']}'")

        # 2c: 500 server error
        mock_get.side_effect = None
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Internal Server Error"
        result = fetch_ticket("SCRUM-1")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        print(f"  [OK] HTTP 500         -> '{result['error']}'")

        # 2d: 401 unauthorized
        mock_get.return_value.status_code = 401
        mock_get.return_value.text = "Unauthorized"
        result = fetch_ticket("SCRUM-1")
        self.assertFalse(result["success"])
        print(f"  [OK] HTTP 401         -> '{result['error']}'")

        print("  => PASS — All API failures handled safely")

    # ---------------------------------------------------------
    # TEST 3: Missing fields -> Graceful handling
    # ---------------------------------------------------------
    @patch("backend.jira.ticket_fetcher.JiraConnector")
    def test_3_missing_fields_graceful(self, MockConnector):
        """Tickets with missing/null fields must not crash fetcher or parser."""
        print("\n[TEST 3] Missing Fields -> Graceful Handling")
        print("-" * 50)

        # Simulate connector returning sparse data
        mock_instance = MockConnector.return_value
        mock_instance.get_ticket.return_value = {
            "success":     True,
            "ticket_id":   "SCRUM-1",
            "summary":     None,        # null summary
            "description": None,        # null description
            "status":      None,        # null status
            "priority":    None,        # null priority
            "issue_type":  None,        # null type
            "assignee":    None,        # null assignee
            "reporter":    None,
            "labels":      None,        # null labels
            "created":     None,
            "updated":     None,
        }

        try:
            result = fetch_ticket("SCRUM-1")
            self.assertTrue(result["success"])
            # All fields must be strings, not None
            self.assertIsInstance(result["summary"],     str)
            self.assertIsInstance(result["description"], str)
            self.assertIsInstance(result["status"],      str)
            self.assertIsInstance(result["priority"],    str)
            self.assertIsInstance(result["issue_type"],  str)
            self.assertIsInstance(result["assignee"],    str)
            # labels must be a list
            self.assertIsInstance(result["labels"],      list)

            print(f"  [OK] summary     : '{result['summary']}'")
            print(f"  [OK] description : '{result['description']}'")
            print(f"  [OK] status      : '{result['status']}'")
            print(f"  [OK] priority    : '{result['priority']}'")
            print(f"  [OK] labels      : {result['labels']}")
            print("  => PASS — No crash on null fields")
        except Exception as e:
            self.fail(f"fetch_ticket crashed on missing fields: {e}")

    # ---------------------------------------------------------
    # TEST 4: Parser crash guard
    # ---------------------------------------------------------
    @patch("backend.jira.parser.fetch_ticket")
    def test_4_parser_crash_guard(self, mock_fetch):
        """If fetch_ticket raises an unexpected exception, parser must catch it."""
        print("\n[TEST 4] Parser Crash Guard")
        print("-" * 50)

        mock_fetch.side_effect = RuntimeError("Completely unexpected crash!")

        result = parse_ticket("SCRUM-1")

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("crashed", result["error"].lower())
        print(f"  [OK] success : {result['success']}")
        print(f"  [OK] error   : {result['error']}")
        print("  => PASS — Parser caught the crash gracefully")

    # ---------------------------------------------------------
    # TEST 5: Batch fetch — partial failure no crash
    # ---------------------------------------------------------
    def test_5_batch_partial_failure(self):
        """Batch fetch with mixed valid/invalid IDs must not crash."""
        print("\n[TEST 5] Batch Fetch — Partial Failure No Crash")
        print("-" * 50)

        ids = ["SCRUM-1", "SCRUM-99999", "", "INVALID"]

        try:
            results = fetch_multiple_tickets(ids)
            self.assertEqual(len(results), len(ids))
            for r in results:
                self.assertIsInstance(r, dict)
                self.assertIn("success", r)
            passed = sum(1 for r in results if r["success"])
            failed = sum(1 for r in results if not r["success"])
            print(f"  [OK] Total    : {len(results)}")
            print(f"  [OK] Passed   : {passed}")
            print(f"  [OK] Failed   : {failed} (expected — bad IDs)")
            print("  => PASS — Batch handled partial failures safely")
        except Exception as e:
            self.fail(f"fetch_multiple_tickets crashed: {e}")


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  RELIABILITY TEST PHASE")
    print("=" * 55)

    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite  = loader.loadTestsFromTestCase(TestReliability)

    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 55)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    if result.wasSuccessful():
        print("  [ALL PASS] System is crash-proof and reliable!")
    else:
        for f in result.failures + result.errors:
            print(f"  [FAIL] {f[0]}")
            print(f"         {f[1][:200]}")
    print("=" * 55 + "\n")
