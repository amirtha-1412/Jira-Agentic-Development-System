"""
agents/requirement_analyst/requirement_routes.py
---------------------------------------------
FastAPI Requirement Analyst Routes
Exposes the full Requirement Analyst Agent
as REST endpoints for all 4 analysis modes.

Endpoints:
  POST /analyst/analyze          — Full analysis (7 sections)
  POST /analyst/engineering-tasks — Engineering task breakdown
  POST /analyst/edge-cases       — Edge case + security risks
  POST /analyst/reasoning        — Explainable reasoning trace
  POST /analyst/analyze-ticket   — Full pipeline from Jira ticket ID
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from agents.llm import call_llm
from agents.requirement_analyst.analyzer import RequirementAnalyst, AnalysisResult
from agents.requirement_analyst.prompt import (
    build_engineering_tasks_prompt,
    build_edge_case_prompt,
    build_reasoning_prompt,
    get_system_prompt,
)

router = APIRouter(prefix="/analyst", tags=["Requirement Analyst"])

# ─── Singleton analyst ────────────────────────
_analyst: RequirementAnalyst = None

def get_analyst() -> RequirementAnalyst:
    global _analyst
    if _analyst is None:
        _analyst = RequirementAnalyst(use_retriever=True)
    return _analyst


# ─────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────

class TicketInput(BaseModel):
    ticket_id:   str
    title:       str
    description: Optional[str] = "NOT SPECIFIED"
    status:      Optional[str] = "N/A"
    priority:    Optional[str] = "NONE"
    issue_type:  Optional[str] = "Task"
    assignee:    Optional[str] = "Unassigned"

class TicketIdInput(BaseModel):
    ticket_id: str


# ─────────────────────────────────────────────
# POST /analyst/analyze
# ─────────────────────────────────────────────

@router.post("/analyze", summary="Full requirement analysis (7 sections)")
async def analyze_ticket(body: TicketInput):
    """
    Runs the full Requirement Analyst Agent:
    Summary, Functional/Technical Reqs, Affected Files,
    Implementation Steps, Ambiguities, Risk Assessment.
    """
    try:
        analyst = get_analyst()
        result  = analyst.analyze(body.model_dump())

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return {
            "success": True,
            "mode":    "full_analysis",
            **result.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# POST /analyst/analyze-ticket
# ─────────────────────────────────────────────

@router.post("/analyze-ticket", summary="Fetch from Jira + full analysis")
async def analyze_from_jira(body: TicketIdInput):
    """
    Fetches a Jira ticket by ID, then runs the full
    Requirement Analyst pipeline end-to-end.
    """
    try:
        analyst = get_analyst()
        result  = analyst.analyze_from_id(body.ticket_id)

        if not result.success:
            raise HTTPException(status_code=404 if "not found" in result.error.lower()
                                else 500, detail=result.error)

        return {
            "success": True,
            "mode":    "jira_pipeline",
            **result.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# POST /analyst/engineering-tasks
# ─────────────────────────────────────────────

@router.post("/engineering-tasks", summary="Convert ticket to engineering tasks")
async def get_engineering_tasks(body: TicketInput):
    """
    Breaks a ticket into atomic TASK-N items,
    ordered execution plan, and acceptance criteria.
    """
    try:
        prompt = build_engineering_tasks_prompt(
            ticket_id   = body.ticket_id,
            title       = body.title,
            description = body.description,
            status      = body.status,
            priority    = body.priority,
            issue_type  = body.issue_type,
        )
        response = call_llm(
            user_prompt   = prompt,
            system_prompt = get_system_prompt(),
        )
        return {
            "success":   True,
            "mode":      "engineering_tasks",
            "ticket_id": body.ticket_id,
            "title":     body.title,
            "analysis":  response,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# POST /analyst/edge-cases
# ─────────────────────────────────────────────

@router.post("/edge-cases", summary="Identify edge cases and security risks")
async def get_edge_cases(body: TicketInput):
    """
    Analyzes the ticket for implementation edge cases,
    security vulnerabilities, performance risks, and mitigations.
    """
    try:
        prompt = build_edge_case_prompt(
            ticket_id   = body.ticket_id,
            title       = body.title,
            description = body.description,
            priority    = body.priority,
            issue_type  = body.issue_type,
        )
        response = call_llm(
            user_prompt   = prompt,
            system_prompt = get_system_prompt(),
        )
        return {
            "success":   True,
            "mode":      "edge_cases",
            "ticket_id": body.ticket_id,
            "title":     body.title,
            "analysis":  response,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# POST /analyst/reasoning
# ─────────────────────────────────────────────

@router.post("/reasoning", summary="Generate explainable reasoning trace")
async def get_reasoning(body: TicketInput):
    """
    Generates a transparent chain-of-thought reasoning
    trace for the ticket analysis, including confidence
    assessment and grounded evidence.
    """
    try:
        prompt = build_reasoning_prompt(
            ticket_id   = body.ticket_id,
            title       = body.title,
            description = body.description,
            status      = body.status,
            priority    = body.priority,
        )
        response = call_llm(
            user_prompt   = prompt,
            system_prompt = get_system_prompt(),
        )
        return {
            "success":   True,
            "mode":      "reasoning",
            "ticket_id": body.ticket_id,
            "title":     body.title,
            "reasoning": response,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# GET /analyst/health
# ─────────────────────────────────────────────

@router.get("/health", summary="Analyst agent health check")
async def analyst_health():
    """Returns health status of the Requirement Analyst Agent."""
    try:
        analyst  = get_analyst()
        from agents.llm import get_llm, DEFAULT_MODEL
        llm      = get_llm()
        return {
            "success":          True,
            "status":           "ready",
            "model":            DEFAULT_MODEL,
            "retriever_ready":  analyst._get_retriever() is not None
                                and analyst._get_retriever().is_ready(),
            "endpoints": [
                "POST /analyst/analyze",
                "POST /analyst/analyze-ticket",
                "POST /analyst/engineering-tasks",
                "POST /analyst/edge-cases",
                "POST /analyst/reasoning",
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
