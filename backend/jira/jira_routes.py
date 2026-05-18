"""
backend/jira/jira_routes.py
---------------------------------------------
Jira API Routes
Exposes Jira ticket functionality as
FastAPI REST endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from backend.jira.parser import parse_ticket, parse_multiple_tickets, to_ai_format, to_ai_format_json
from backend.jira.ticket_fetcher import fetch_open_tickets

router = APIRouter(prefix="/jira", tags=["Jira"])


# ---------------------------------------------
# GET /jira/ticket/{ticket_id}
# ---------------------------------------------

@router.get("/ticket/{ticket_id}", summary="Fetch & parse a single Jira ticket")
async def get_ticket(ticket_id: str):
    """
    Fetches and parses a single Jira ticket.
    Returns clean structured data ready for agents.
    """
    result = parse_ticket(ticket_id.upper())

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result.get("error", f"Ticket '{ticket_id}' not found.")
        )

    return result


# ---------------------------------------------
# GET /jira/ticket/{ticket_id}/ai-format
# ---------------------------------------------

@router.get("/ticket/{ticket_id}/ai-format", summary="Get AI-ready JSON payload for a ticket")
async def get_ticket_ai_format(ticket_id: str):
    """
    Returns a fully structured, versioned AI-ready payload
    for a Jira ticket — ready to pass into any LLM agent.
    """
    result = to_ai_format(ticket_id.upper())

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result.get("error", f"Ticket '{ticket_id}' not found.")
        )

    return result


# ---------------------------------------------
# GET /jira/tickets/open
# ---------------------------------------------

@router.get("/tickets/open", summary="Fetch all open tickets from Jira project")
async def get_open_tickets(max_results: int = Query(default=10, ge=1, le=50)):
    """
    Returns a list of all open/in-progress tickets from
    the configured Jira project.
    """
    tickets = fetch_open_tickets(max_results=max_results)

    return {
        "success": True,
        "count":   len(tickets),
        "tickets": tickets,
    }


# ---------------------------------------------
# POST /jira/tickets/batch
# ---------------------------------------------

from pydantic import BaseModel

class BatchRequest(BaseModel):
    ticket_ids: list[str]

@router.post("/tickets/batch", summary="Fetch & parse multiple Jira tickets")
async def get_batch_tickets(body: BatchRequest):
    """
    Fetches and parses a list of Jira ticket IDs in one request.
    Returns a list of structured ticket payloads.
    """
    if not body.ticket_ids:
        raise HTTPException(status_code=400, detail="ticket_ids list cannot be empty.")

    if len(body.ticket_ids) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 tickets per batch request.")

    results  = parse_multiple_tickets([t.upper() for t in body.ticket_ids])
    success  = [r for r in results if r["success"]]
    failed   = [r for r in results if not r["success"]]

    return {
        "success":       True,
        "total":         len(results),
        "fetched":       len(success),
        "failed":        len(failed),
        "tickets":       success,
        "errors":        failed,
    }
