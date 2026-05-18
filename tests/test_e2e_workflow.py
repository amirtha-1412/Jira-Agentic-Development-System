"""
tests/test_e2e_workflow.py
---------------------------------------------
FINAL END-TO-END WORKFLOW VALIDATION

Flow:
  Jira Ticket ID
       -> Jira API
       -> Ticket Fetcher
       -> Parser
       -> Structured JSON
       -> FastAPI Endpoint
"""

import sys
import io
import json
import time
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

BASE_URL   = "http://localhost:8000"
TICKET_IDS = ["SCRUM-1", "SCRUM-2"]

PASS  = "[PASS]"
FAIL  = "[FAIL]"
SEP   = "=" * 60


def print_step(step: int, title: str):
    print(f"\n  STEP {step}: {title}")
    print("  " + "-" * 50)


def run_workflow(ticket_id: str) -> bool:
    """Runs the full pipeline for a single ticket. Returns True if all steps pass."""
    print(f"\n{SEP}")
    print(f"  WORKFLOW: {ticket_id}")
    print(SEP)
    all_pass = True

    # ─────────────────────────────────────────────
    # STEP 1: Python Layer — Ticket Fetcher
    # ─────────────────────────────────────────────
    print_step(1, "Ticket Fetcher (Python)")
    from backend.jira.ticket_fetcher import fetch_ticket
    result = fetch_ticket(ticket_id)

    if result["success"]:
        print(f"  {PASS} ticket_id   : {result['ticket_id']}")
        print(f"  {PASS} summary     : {result['summary']}")
        print(f"  {PASS} status      : {result['status']}")
        print(f"  {PASS} priority    : {result['priority']}")
    else:
        print(f"  {FAIL} Fetcher error: {result['error']}")
        all_pass = False

    # ─────────────────────────────────────────────
    # STEP 2: Python Layer — Parser
    # ─────────────────────────────────────────────
    print_step(2, "Parser — Clean + Normalize")
    from backend.jira.parser import parse_ticket
    parsed = parse_ticket(ticket_id)

    if parsed["success"]:
        print(f"  {PASS} title       : {parsed['title']}")
        print(f"  {PASS} priority    : {parsed['priority']}")
        print(f"  {PASS} status      : {parsed['status']}")
        print(f"  {PASS} agent_prompt: present ({len(parsed['agent_prompt'])} chars)")
    else:
        print(f"  {FAIL} Parser error: {parsed['error']}")
        all_pass = False

    # ─────────────────────────────────────────────
    # STEP 3: Python Layer — AI Format
    # ─────────────────────────────────────────────
    print_step(3, "AI Format — Structured JSON")
    from backend.jira.parser import to_ai_format, to_ai_format_json
    ai_data    = to_ai_format(ticket_id)
    ai_json_str = to_ai_format_json(ticket_id)

    if ai_data["success"]:
        t = ai_data["ticket"]
        print(f"  {PASS} schema_version : {ai_data['schema_version']}")
        print(f"  {PASS} generated_at   : {ai_data['generated_at']}")
        print(f"  {PASS} ticket.id      : {t['id']}")
        print(f"  {PASS} ticket.title   : {t['title']}")
        print(f"  {PASS} agent.target   : {ai_data['agent']['target']}")
        # Validate JSON is parseable
        try:
            json.loads(ai_json_str)
            print(f"  {PASS} JSON string    : valid ({len(ai_json_str)} chars)")
        except json.JSONDecodeError:
            print(f"  {FAIL} JSON string    : INVALID!")
            all_pass = False
    else:
        print(f"  {FAIL} AI format error: {ai_data['error']}")
        all_pass = False

    # ─────────────────────────────────────────────
    # STEP 4: FastAPI — GET /jira/ticket/{id}
    # ─────────────────────────────────────────────
    print_step(4, f"FastAPI GET /jira/ticket/{ticket_id}")
    try:
        resp = requests.get(f"{BASE_URL}/jira/ticket/{ticket_id}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  {PASS} HTTP Status   : {resp.status_code}")
            print(f"  {PASS} ticket_id     : {data.get('ticket_id')}")
            print(f"  {PASS} title         : {data.get('title')}")
        else:
            print(f"  {FAIL} HTTP {resp.status_code}: {resp.text[:80]}")
            all_pass = False
    except requests.exceptions.ConnectionError:
        print(f"  {FAIL} Backend not running. Start with: uvicorn backend.main:app --reload")
        all_pass = False

    # ─────────────────────────────────────────────
    # STEP 5: FastAPI — GET /jira/ticket/{id}/ai-format
    # ─────────────────────────────────────────────
    print_step(5, f"FastAPI GET /jira/ticket/{ticket_id}/ai-format")
    try:
        resp = requests.get(f"{BASE_URL}/jira/ticket/{ticket_id}/ai-format", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  {PASS} HTTP Status     : {resp.status_code}")
            print(f"  {PASS} schema_version  : {data.get('schema_version')}")
            print(f"  {PASS} ticket.priority : {data.get('ticket', {}).get('priority')}")
            print(f"  {PASS} agent.target    : {data.get('agent', {}).get('target')}")
        else:
            print(f"  {FAIL} HTTP {resp.status_code}")
            all_pass = False
    except requests.exceptions.ConnectionError:
        print(f"  {FAIL} Backend not running.")
        all_pass = False

    return all_pass


def run_open_tickets_test():
    """Tests GET /jira/tickets/open endpoint."""
    print(f"\n{SEP}")
    print("  STEP 6: FastAPI GET /jira/tickets/open")
    print(SEP)
    try:
        resp = requests.get(f"{BASE_URL}/jira/tickets/open", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  {PASS} HTTP Status : {resp.status_code}")
            print(f"  {PASS} Count       : {data.get('count')} open tickets")
            for t in data.get("tickets", []):
                print(f"         -> {t['ticket_id']} | {t['summary']} | {t['status']}")
            return True
        else:
            print(f"  {FAIL} HTTP {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  {FAIL} Backend not running.")
        return False


def run_404_test():
    """Tests that invalid tickets return HTTP 404."""
    print(f"\n{SEP}")
    print("  STEP 7: FastAPI 404 — Invalid Ticket")
    print(SEP)
    try:
        resp = requests.get(f"{BASE_URL}/jira/ticket/INVALID-99999", timeout=10)
        if resp.status_code == 404:
            print(f"  {PASS} HTTP 404 returned correctly for invalid ticket")
            print(f"  {PASS} Error: {resp.json().get('detail')}")
            return True
        else:
            print(f"  {FAIL} Expected 404, got {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  {FAIL} Backend not running.")
        return False


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":
    print(f"\n{SEP}")
    print("  JIRA AGENTIC SYSTEM - FINAL E2E WORKFLOW TEST")
    print(SEP)
    print(f"  Backend : {BASE_URL}")
    print(f"  Tickets : {TICKET_IDS}")

    results = []

    # Run full workflow for each ticket
    for tid in TICKET_IDS:
        results.append(run_workflow(tid))

    # Open tickets endpoint
    results.append(run_open_tickets_test())

    # 404 handling
    results.append(run_404_test())

    # Final summary
    passed = sum(results)
    total  = len(results)

    print(f"\n{SEP}")
    print(f"  FINAL RESULTS: {passed}/{total} workflows passed")
    if all(results):
        print("  [ALL PASS] Complete Jira workflow is VALIDATED!")
        print(f"\n  Full Pipeline:")
        print("  Jira Ticket ID -> Jira API -> Fetcher -> Parser -> JSON -> FastAPI")
    else:
        print("  [PARTIAL] Some steps failed — check output above.")
    print(f"{SEP}\n")
