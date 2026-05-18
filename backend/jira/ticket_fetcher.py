"""
backend/jira/ticket_fetcher.py
---------------------------------------------
Ticket Fetcher Module — Hardened & Reliable
High-level interface for fetching and formatting
Jira tickets into clean structured data ready
for consumption by AI agents.
Includes full defensive coding:
  - Input validation
  - Safe field access with fallbacks
  - Exception wrapping at every layer
"""

from backend.jira.connector import JiraConnector


# ---------------------------------------------
# Core Fetch Functions
# ---------------------------------------------

def fetch_ticket(ticket_id: str) -> dict:
    """
    Fetches a single Jira ticket and returns
    a clean, agent-ready structured payload.
    Fully hardened: validates input, wraps all
    exceptions, uses safe field access.

    Args:
        ticket_id (str): e.g. "SCRUM-1"

    Returns:
        dict: Structured ticket data or error dict
    """
    # ── Input validation ──────────────────────
    if not ticket_id or not isinstance(ticket_id, str):
        return {
            "success":   False,
            "ticket_id": str(ticket_id),
            "error":     "Invalid ticket ID: must be a non-empty string (e.g. 'SCRUM-1').",
        }

    ticket_id = ticket_id.strip().upper()
    if "-" not in ticket_id:
        return {
            "success":   False,
            "ticket_id": ticket_id,
            "error":     f"Invalid ticket format '{ticket_id}'. Expected format: PROJECT-123.",
        }

    # ── Fetch with exception wrapping ─────────
    try:
        connector = JiraConnector()
        raw       = connector.get_ticket(ticket_id)
    except EnvironmentError as e:
        return {"success": False, "ticket_id": ticket_id, "error": f"Config error: {e}"}
    except Exception as e:
        return {"success": False, "ticket_id": ticket_id, "error": f"Unexpected error: {e}"}

    if not raw.get("success"):
        return {
            "success":   False,
            "ticket_id": ticket_id,
            "error":     raw.get("error", "Unknown error from Jira API."),
        }

    # ── Safe field extraction — handles None AND missing keys ──
    return {
        "success":     True,
        "ticket_id":   raw.get("ticket_id")   or ticket_id,
        "summary":     raw.get("summary")     or "No summary provided.",
        "description": raw.get("description") or "No description provided.",
        "status":      raw.get("status")      or "Unknown",
        "priority":    raw.get("priority")    or "NONE",
        "issue_type":  raw.get("issue_type")  or "Task",
        "assignee":    raw.get("assignee")    or "Unassigned",
        "reporter":    raw.get("reporter")    or "Unknown",
        "labels":      raw.get("labels")      or [],
        "created":     raw.get("created")     or "",
        "updated":     raw.get("updated")     or "",
        "agent_input": _build_agent_input(raw),
    }


def fetch_multiple_tickets(ticket_ids: list) -> list:
    """
    Fetches multiple Jira tickets in sequence.

    Args:
        ticket_ids (list): e.g. ["SCRUM-1", "SCRUM-2"]

    Returns:
        list: List of structured ticket dicts
    """
    results = []
    for ticket_id in ticket_ids:
        result = fetch_ticket(ticket_id)
        results.append(result)
    return results


def fetch_open_tickets(max_results: int = 10) -> list:
    """
    Fetches all open/in-progress tickets from the project.
    Returns empty list on any failure (safe for agents).
    """
    try:
        connector = JiraConnector()
        result    = connector.get_open_tickets(max_results=max_results)
        if not result.get("success"):
            return []
        return result.get("tickets", [])
    except Exception:
        return []


# ---------------------------------------------
# Internal Helper
# ---------------------------------------------

def _build_agent_input(ticket: dict) -> str:
    """
    Builds a structured natural language prompt string
    from ticket data — ready to pass directly into an LLM agent.
    """
    return (
        f"Ticket ID   : {ticket['ticket_id']}\n"
        f"Summary     : {ticket['summary']}\n"
        f"Type        : {ticket['issue_type']}\n"
        f"Priority    : {ticket['priority']}\n"
        f"Status      : {ticket['status']}\n"
        f"Assignee    : {ticket['assignee']}\n"
        f"Description :\n{ticket['description']}\n"
    )


# ---------------------------------------------
# Test Runner
# ---------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  TICKET FETCHER - TEST RUN")
    print("=" * 55)

    # Test 1: Fetch single ticket
    print("\n[TEST 1] Fetch SCRUM-1")
    print("-" * 40)
    ticket = fetch_ticket("SCRUM-1")
    if ticket["success"]:
        print(f"  [OK] ID          : {ticket['ticket_id']}")
        print(f"  [OK] Summary     : {ticket['summary']}")
        print(f"  [OK] Type        : {ticket['issue_type']}")
        print(f"  [OK] Priority    : {ticket['priority']}")
        print(f"  [OK] Status      : {ticket['status']}")
        print(f"  [OK] Description : {ticket['description'][:80]}...")
        print(f"\n  --- Agent Input Preview ---")
        print(ticket["agent_input"])
    else:
        print(f"  [FAIL] {ticket['error']}")

    # Test 2: Fetch multiple tickets
    print("\n[TEST 2] Fetch SCRUM-1 & SCRUM-2")
    print("-" * 40)
    tickets = fetch_multiple_tickets(["SCRUM-1", "SCRUM-2"])
    for t in tickets:
        if t["success"]:
            print(f"  [OK] {t['ticket_id']} | {t['summary']} | {t['status']}")
        else:
            print(f"  [FAIL] {t['ticket_id']}: {t['error']}")

    # Test 3: Fetch all open tickets
    print("\n[TEST 3] Fetch All Open Tickets")
    print("-" * 40)
    open_tickets = fetch_open_tickets()
    if open_tickets:
        for t in open_tickets:
            print(f"  [OK] {t['ticket_id']} | {t['summary']} | {t['status']}")
    else:
        print("  [INFO] No open tickets found.")

    print("\n" + "=" * 55)
    print("  [DONE] All tests completed.")
    print("=" * 55 + "\n")
