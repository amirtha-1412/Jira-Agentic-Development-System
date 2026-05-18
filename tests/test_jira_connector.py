"""
tests/test_jira_connector.py
--------------------------------------------
Test Suite for Jira Auth + Connector modules.
Run with: python tests/test_jira_connector.py
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.jira.auth import test_jira_connection, get_jira_config
from backend.jira.connector import JiraConnector, test_jira_connector


def test_1_env_config():
    print("\n[TEST 1] Environment Config Loader")
    print("-" * 40)
    try:
        config = get_jira_config()
        print(f"  [OK] JIRA_BASE_URL      = {config['base_url']}")
        print(f"  [OK] JIRA_EMAIL         = {config['email']}")
        print(f"  [OK] JIRA_API_KEY       = {'*' * 8} (hidden)")
        print(f"  [OK] JIRA_PROJECT_KEY   = {config['project']}")
    except EnvironmentError as e:
        print(f"  [FAIL] Config Error: {e}")


def test_2_auth_connection():
    print("\n[TEST 2] Jira Auth — API Connection")
    print("-" * 40)
    result = test_jira_connection()
    if result["success"]:
        print(f"  [OK] Authenticated as : {result['user']}")
        print(f"  [OK] Email            : {result['email']}")
        print(f"  [OK] Account ID       : {result['account_id']}")
    else:
        print(f"  [FAIL] Auth Failed: {result['error']}")


def test_3_connector():
    print("\n[TEST 3] Jira Connector — Fetch Open Tickets")
    print("-" * 40)
    test_jira_connector()


def test_4_fetch_single_ticket():
    print("\n[TEST 4] Fetch Tickets — SCRUM-1 & SCRUM-2")
    print("-" * 40)
    try:
        connector = JiraConnector()

        for ticket_id in ["SCRUM-1", "SCRUM-2"]:
            print(f"\n  Fetching {ticket_id}...")
            result = connector.get_ticket(ticket_id)

            if result["success"]:
                print(f"  [OK] Ticket      : {result['ticket_id']}")
                print(f"  [OK] Summary     : {result['summary']}")
                print(f"  [OK] Status      : {result['status']}")
                print(f"  [OK] Priority    : {result['priority']}")
                print(f"  [OK] Assignee    : {result['assignee']}")
                print(f"  [OK] Issue Type  : {result['issue_type']}")
                print(f"  [OK] Description : {result['description'][:100]}...")
            else:
                print(f"  [WARN] {result['error']}")
    except EnvironmentError as e:
        print(f"  [FAIL] Config error: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("   JIRA AGENTIC SYSTEM - TEST SUITE")
    print("=" * 50)

    test_1_env_config()
    test_2_auth_connection()
    test_3_connector()
    test_4_fetch_single_ticket()

    print("\n[DONE] All tests completed.\n")
