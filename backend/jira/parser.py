"""
backend/jira/parser.py
---------------------------------------------
Jira Ticket Parser
Strips noisy raw Jira JSON down to a clean,
minimal payload that agents actually need:
  - title (summary)
  - description (plain text)
  - priority
  - status
  - ai_payload (stable versioned schema for LLMs)
"""

import json
from datetime import datetime, timezone
from backend.jira.ticket_fetcher import fetch_ticket, fetch_multiple_tickets


# ---------------------------------------------
# Core Parser
# ---------------------------------------------

def parse_ticket(ticket_id: str) -> dict:
    """
    Fetches and parses a Jira ticket into a minimal
    agent-ready payload. Fully hardened with try/except
    and safe .get() fallbacks on every field.

    Args:
        ticket_id (str): e.g. "SCRUM-1"

    Returns:
        dict: { ticket_id, title, description, priority,
                status, issue_type, agent_prompt }
    """
    # ── Input guard ───────────────────────────
    if not ticket_id or not isinstance(ticket_id, str):
        return {
            "success":   False,
            "ticket_id": str(ticket_id),
            "error":     "Invalid ticket ID passed to parser.",
        }

    try:
        raw = fetch_ticket(ticket_id)

        if not raw.get("success"):
            return {
                "success":   False,
                "ticket_id": ticket_id,
                "error":     raw.get("error", "Failed to fetch ticket."),
            }

        # ── Safe field extraction with fallbacks ──
        parsed = {
            "success":     True,
            "ticket_id":   raw.get("ticket_id",   ticket_id),
            "title":       _clean_text(raw.get("summary",     "")),
            "description": _clean_text(raw.get("description", "")),
            "priority":    _normalize_priority(raw.get("priority", "")),
            "status":      _normalize_status(raw.get("status",   "")),
            "issue_type":  raw.get("issue_type",  "Task"),
            "assignee":    raw.get("assignee",    "Unassigned"),
        }

        parsed["agent_prompt"] = _build_agent_prompt(parsed)
        return parsed

    except Exception as e:
        return {
            "success":   False,
            "ticket_id": ticket_id,
            "error":     f"Parser crashed unexpectedly: {str(e)}",
        }


def parse_multiple_tickets(ticket_ids: list) -> list:
    """
    Parses a list of ticket IDs into clean payloads.

    Args:
        ticket_ids (list): e.g. ["SCRUM-1", "SCRUM-2"]

    Returns:
        list: List of parsed ticket dicts
    """
    return [parse_ticket(tid) for tid in ticket_ids]


def to_ai_format(ticket_id: str) -> dict:
    """
    Full pipeline: Fetch -> Parse -> Convert to stable AI-ready JSON.
    Produces a versioned, schema-stable payload safe to pass
    directly into any LLM agent.

    Args:
        ticket_id (str): e.g. "SCRUM-1"

    Returns:
        dict: Stable AI payload with metadata + structured fields
    """
    parsed = parse_ticket(ticket_id)

    if not parsed["success"]:
        return {
            "schema_version": "1.0",
            "success":        False,
            "ticket_id":      ticket_id,
            "error":          parsed.get("error", "Unknown error"),
            "generated_at":   _utc_now(),
        }

    return {
        # --- Schema metadata ---
        "schema_version": "1.0",
        "success":        True,
        "generated_at":   _utc_now(),

        # --- Core ticket fields (clean, normalized) ---
        "ticket": {
            "id":          parsed["ticket_id"],
            "title":       parsed["title"],
            "description": parsed["description"],
            "priority":    parsed["priority"],
            "status":      parsed["status"],
            "issue_type":  parsed["issue_type"],
            "assignee":    parsed["assignee"],
        },

        # --- Agent instructions ---
        "agent": {
            "target":  "requirement_analyst",
            "prompt":  parsed["agent_prompt"],
            "instructions": (
                "Analyze the ticket above. Extract: "
                "(1) functional requirements, "
                "(2) acceptance criteria, "
                "(3) technical tasks, "
                "(4) edge cases to handle."
            ),
        },
    }


def to_ai_format_json(ticket_id: str, indent: int = 2) -> str:
    """
    Returns the AI-ready payload as a formatted JSON string.
    Useful for logging, saving to file, or direct LLM injection.
    """
    return json.dumps(to_ai_format(ticket_id), indent=indent, ensure_ascii=False)


# ---------------------------------------------
# Internal Cleaners & Normalizers
# ---------------------------------------------

def _clean_text(text: str) -> str:
    """
    Strips excess whitespace, newlines, and noise
    from text fields.
    """
    if not text:
        return "Not provided."
    # Collapse multiple whitespace/newlines into single space
    cleaned = " ".join(text.split())
    return cleaned.strip()


def _normalize_priority(priority: str) -> str:
    """
    Normalizes priority to one of:
    HIGH / MEDIUM / LOW / NONE
    """
    mapping = {
        "highest": "HIGH",
        "high":    "HIGH",
        "medium":  "MEDIUM",
        "low":     "LOW",
        "lowest":  "LOW",
        "none":    "NONE",
    }
    return mapping.get(str(priority).lower(), "NONE")


def _normalize_status(status: str) -> str:
    """
    Normalizes status to one of:
    TODO / IN_PROGRESS / IN_REVIEW / DONE
    """
    if not status:
        return "NONE"
    mapping = {
        "to do":       "TODO",
        "in progress": "IN_PROGRESS",
        "in review":   "IN_REVIEW",
        "done":        "DONE",
        "closed":      "DONE",
        "resolved":    "DONE",
    }
    return mapping.get(str(status).lower(), str(status).upper().replace(" ", "_"))


def _build_agent_prompt(parsed: dict) -> str:
    """
    Builds a clean, minimal natural language prompt
    for the Requirement Analyst Agent from parsed fields.
    """
    return (
        f"Ticket    : {parsed['ticket_id']}\n"
        f"Title     : {parsed['title']}\n"
        f"Priority  : {parsed['priority']}\n"
        f"Status    : {parsed['status']}\n"
        f"Type      : {parsed['issue_type']}\n"
        f"Assignee  : {parsed['assignee']}\n"
        f"\nDescription:\n{parsed['description']}\n"
    )


def _utc_now() -> str:
    """Returns current UTC timestamp as ISO 8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------
# Quick Test
# ---------------------------------------------

if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("\n" + "=" * 60)
    print("  JIRA PARSER - AI FORMAT TEST RUN")
    print("=" * 60)

    for ticket_id in ["SCRUM-1", "SCRUM-2"]:
        print(f"\n--- AI Format: {ticket_id} ---")
        ai_payload = to_ai_format(ticket_id)

        if ai_payload["success"]:
            t = ai_payload["ticket"]
            print(f"  [OK] schema_version : {ai_payload['schema_version']}")
            print(f"  [OK] generated_at   : {ai_payload['generated_at']}")
            print(f"  [OK] ticket.id      : {t['id']}")
            print(f"  [OK] ticket.title   : {t['title']}")
            print(f"  [OK] ticket.priority: {t['priority']}")
            print(f"  [OK] ticket.status  : {t['status']}")
            print(f"  [OK] agent.target   : {ai_payload['agent']['target']}")
            print(f"\n  --- JSON Preview (first 400 chars) ---")
            print(to_ai_format_json(ticket_id)[:400] + "...")
        else:
            print(f"  [FAIL] {ai_payload['error']}")

    print("\n" + "=" * 60)
    print("  [DONE] AI format test complete.")
    print("=" * 60 + "\n")
