"""
workflows/workflow_routes.py
---------------------------------------------
FastAPI Workflow Orchestration Routes
Exposes the LangGraph multi-agent workflow
as REST API endpoints.

Endpoints:
  POST /workflow/execute/{ticket_id}     — Execute full workflow
  GET  /workflow/status/{ticket_id}      — Get workflow status
  POST /workflow/execute-batch           — Execute multiple tickets
  GET  /workflow/health                  — Workflow system health
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import traceback

from workflows.orchestrator.graph import (
    execute_workflow,
    get_workflow_status,
    compile_workflow,
)
from workflows.state import create_initial_state

router = APIRouter(prefix="/workflow", tags=["Workflow Orchestration"])


# ─────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────

class WorkflowExecuteRequest(BaseModel):
    """Request model for workflow execution."""
    ticket_id: str = Field(..., description="Jira ticket ID (e.g., SCRUM-1)")
    max_retries: int = Field(default=2, ge=0, le=5, description="Maximum retry attempts")
    verbose: bool = Field(default=False, description="Enable detailed logs")
    ticket_data: Optional[dict] = Field(default=None, description="Pre-fetched ticket data")


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    success: bool
    ticket_id: str
    pipeline_status: str
    current_stage: str
    completed_stages: List[str]
    retry_count: int
    test_status: str
    pr_ready: bool
    summary: str
    errors: List[str]
    progress: dict


class BatchExecuteRequest(BaseModel):
    """Request model for batch execution."""
    ticket_ids: List[str] = Field(..., min_items=1, max_items=10)
    max_retries: int = Field(default=2, ge=0, le=5)
    verbose: bool = Field(default=False)


# ─────────────────────────────────────────────
# POST /workflow/execute/{ticket_id}
# ─────────────────────────────────────────────

@router.post("/execute/{ticket_id}", summary="Execute full multi-agent workflow")
async def execute_workflow_endpoint(
    ticket_id: str,
    max_retries: int = Query(default=2, ge=0, le=5, description="Max retry attempts"),
    verbose: bool = Query(default=False, description="Enable detailed logs"),
):
    """
    Executes the complete LangGraph multi-agent workflow for a Jira ticket.
    
    **Workflow Pipeline**:
    1. Requirement Analyst → Analyzes ticket
    2. Developer Agent → Generates code
    3. QA Agent → Runs tests
    4. Conditional Retry → If tests fail
    5. PR Agent → Creates pull request
    
    **Features**:
    - Automatic retry on QA failures
    - Explainable execution logs
    - Progress tracking
    - Error handling
    
    **Returns**:
    - Complete workflow state with results
    - Progress indicators for each stage
    - Retry count and test status
    - PR readiness flag
    """
    try:
        # Validate ticket ID format
        ticket_id = ticket_id.strip().upper()
        if not ticket_id or "-" not in ticket_id:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ticket ID format: '{ticket_id}'. Expected format: PROJECT-123"
            )
        
        # Execute workflow
        final_state = execute_workflow(
            ticket_id=ticket_id,
            max_retries=max_retries,
            verbose=verbose,
        )
        
        # Get status summary
        status = get_workflow_status(final_state)
        
        # Build response
        return {
            "success": final_state.get("pipeline_status") == "completed",
            "ticket_id": ticket_id,
            "pipeline_status": final_state.get("pipeline_status", "unknown"),
            "current_stage": final_state.get("current_stage", "unknown"),
            "completed_stages": final_state.get("completed_stages", []),
            "retry_count": final_state.get("retry_count", 0),
            "test_status": final_state.get("test_status", "NOT_RUN"),
            "pr_ready": final_state.get("pr_ready", False),
            "summary": final_state.get("summary", "")[:200],
            "errors": final_state.get("errors", []),
            "progress": status.get("progress", {}),
            "details": {
                "functional_requirements": len(final_state.get("functional_reqs", [])),
                "technical_requirements": len(final_state.get("technical_reqs", [])),
                "implementation_steps": len(final_state.get("implementation_steps", [])),
                "affected_files": len(final_state.get("affected_files", [])),
                "test_cases": len(final_state.get("test_cases", [])),
                "risk_level": final_state.get("risk_level", "UNKNOWN"),
            },
            "pr_info": {
                "title": final_state.get("pr_title", ""),
                "ready": final_state.get("pr_ready", False),
            } if final_state.get("pr_title") else None,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        # Log full traceback for debugging
        error_trace = traceback.format_exc()
        print(f"\n❌ Workflow execution failed for {ticket_id}:")
        print(error_trace)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "ticket_id": ticket_id,
                "message": "Workflow execution failed. Check server logs for details.",
            }
        )


# ─────────────────────────────────────────────
# POST /workflow/execute-with-data
# ─────────────────────────────────────────────

@router.post("/execute-with-data", summary="Execute workflow with pre-fetched ticket data")
async def execute_workflow_with_data(request: WorkflowExecuteRequest):
    """
    Executes workflow with pre-fetched ticket data.
    Useful when you already have ticket data and want to avoid re-fetching.
    
    **Request Body**:
    ```json
    {
      "ticket_id": "SCRUM-1",
      "max_retries": 2,
      "verbose": false,
      "ticket_data": {
        "title": "Add feature",
        "description": "...",
        "priority": "HIGH"
      }
    }
    ```
    """
    try:
        final_state = execute_workflow(
            ticket_id=request.ticket_id.upper(),
            ticket_data=request.ticket_data,
            max_retries=request.max_retries,
            verbose=request.verbose,
        )
        
        status = get_workflow_status(final_state)
        
        return {
            "success": final_state.get("pipeline_status") == "completed",
            "ticket_id": request.ticket_id.upper(),
            "pipeline_status": final_state.get("pipeline_status"),
            "current_stage": final_state.get("current_stage"),
            "completed_stages": final_state.get("completed_stages", []),
            "retry_count": final_state.get("retry_count", 0),
            "test_status": final_state.get("test_status"),
            "pr_ready": final_state.get("pr_ready", False),
            "summary": final_state.get("summary", "")[:200],
            "errors": final_state.get("errors", []),
            "progress": status.get("progress", {}),
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


# ─────────────────────────────────────────────
# POST /workflow/execute-batch
# ─────────────────────────────────────────────

@router.post("/execute-batch", summary="Execute workflow for multiple tickets")
async def execute_batch_workflow(request: BatchExecuteRequest):
    """
    Executes workflow for multiple Jira tickets in sequence.
    
    **Limitations**:
    - Maximum 10 tickets per batch
    - Sequential execution (not parallel)
    - Returns summary for each ticket
    
    **Request Body**:
    ```json
    {
      "ticket_ids": ["SCRUM-1", "SCRUM-2", "SCRUM-3"],
      "max_retries": 2,
      "verbose": false
    }
    ```
    """
    results = []
    
    for ticket_id in request.ticket_ids:
        try:
            final_state = execute_workflow(
                ticket_id=ticket_id.upper(),
                max_retries=request.max_retries,
                verbose=request.verbose,
            )
            
            results.append({
                "ticket_id": ticket_id.upper(),
                "success": final_state.get("pipeline_status") == "completed",
                "pipeline_status": final_state.get("pipeline_status"),
                "retry_count": final_state.get("retry_count", 0),
                "test_status": final_state.get("test_status"),
                "pr_ready": final_state.get("pr_ready", False),
                "errors": final_state.get("errors", []),
            })
        
        except Exception as e:
            results.append({
                "ticket_id": ticket_id.upper(),
                "success": False,
                "error": str(e),
            })
    
    # Summary
    total = len(results)
    successful = sum(1 for r in results if r.get("success"))
    failed = total - successful
    
    return {
        "success": failed == 0,
        "total": total,
        "successful": successful,
        "failed": failed,
        "results": results,
    }


# ─────────────────────────────────────────────
# GET /workflow/status/{ticket_id}
# ─────────────────────────────────────────────

@router.get("/status/{ticket_id}", summary="Get workflow status (placeholder)")
async def get_workflow_status_endpoint(ticket_id: str):
    """
    Gets the current status of a workflow execution.
    
    **Note**: This is a placeholder. In production, you would:
    - Store workflow states in a database
    - Track execution history
    - Provide real-time status updates
    
    For now, this endpoint returns a mock status.
    """
    return {
        "ticket_id": ticket_id.upper(),
        "status": "not_implemented",
        "message": "Status tracking requires persistent storage. Use /execute endpoint to run workflow.",
        "suggestion": "Store workflow states in Redis/PostgreSQL for status tracking.",
    }


# ─────────────────────────────────────────────
# GET /workflow/health
# ─────────────────────────────────────────────

@router.get("/health", summary="Workflow system health check")
async def workflow_health():
    """
    Checks the health of the workflow orchestration system.
    
    **Checks**:
    - LangGraph compilation
    - Node availability
    - LLM connectivity
    - Retriever readiness
    
    **Returns**:
    - Overall health status
    - Component statuses
    - Available endpoints
    """
    try:
        # Test graph compilation
        workflow = compile_workflow()
        graph_healthy = workflow is not None
        
        # Test LLM
        llm_healthy = True
        try:
            from agents.llm import get_llm
            llm = get_llm()
            llm_healthy = llm is not None
        except Exception:
            llm_healthy = False
        
        # Test retriever
        retriever_healthy = True
        try:
            from vectorstore.retriever import CodeRetriever
            retriever = CodeRetriever()
            retriever_healthy = retriever.is_ready()
        except Exception:
            retriever_healthy = False
        
        # Overall health
        all_healthy = graph_healthy and llm_healthy
        
        return {
            "success": True,
            "status": "healthy" if all_healthy else "degraded",
            "components": {
                "langgraph": "✅ healthy" if graph_healthy else "❌ unhealthy",
                "llm": "✅ healthy" if llm_healthy else "❌ unhealthy",
                "retriever": "✅ ready" if retriever_healthy else "⚠️  not ready (optional)",
            },
            "nodes": [
                "requirement_node",
                "developer_node",
                "qa_node",
                "pr_node",
            ],
            "features": [
                "Automatic retry on QA failures",
                "Explainable execution logs",
                "Progress tracking",
                "Conditional routing",
            ],
            "endpoints": [
                "POST /workflow/execute/{ticket_id}",
                "POST /workflow/execute-with-data",
                "POST /workflow/execute-batch",
                "GET  /workflow/status/{ticket_id}",
                "GET  /workflow/health",
            ],
        }
    
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "message": "Workflow system is not functioning properly",
        }


# ─────────────────────────────────────────────
# GET /workflow/info
# ─────────────────────────────────────────────

@router.get("/info", summary="Workflow system information")
async def workflow_info():
    """
    Returns information about the workflow orchestration system.
    
    **Returns**:
    - System architecture
    - Node descriptions
    - Retry logic details
    - Configuration options
    """
    return {
        "name": "Jira Agentic Development System - Workflow Orchestration",
        "version": "1.0.0",
        "description": "Multi-agent LangGraph workflow for automated software development",
        "architecture": {
            "framework": "LangGraph",
            "nodes": 4,
            "conditional_edges": 1,
            "retry_enabled": True,
        },
        "pipeline": [
            {
                "node": "requirement_node",
                "agent": "Requirement Analyst",
                "description": "Analyzes Jira ticket and extracts structured requirements",
                "outputs": ["functional_reqs", "technical_reqs", "implementation_steps"],
            },
            {
                "node": "developer_node",
                "agent": "Developer Agent",
                "description": "Generates code implementation based on requirements",
                "outputs": ["generated_code", "code_diff", "code_ready"],
            },
            {
                "node": "qa_node",
                "agent": "QA Agent",
                "description": "Generates and executes test cases",
                "outputs": ["test_cases", "test_results", "test_status"],
            },
            {
                "node": "pr_node",
                "agent": "PR Agent",
                "description": "Creates pull request with code and test results",
                "outputs": ["pr_title", "pr_description", "pr_ready"],
            },
        ],
        "retry_logic": {
            "enabled": True,
            "max_retries": "configurable (default: 2)",
            "trigger": "QA test failures",
            "strategies": ["targeted_fix", "full_regeneration", "conservative_fix"],
        },
        "features": [
            "Autonomous debugging loops",
            "Explainable AI reasoning",
            "Progress tracking",
            "Error handling",
            "Graceful degradation",
        ],
    }
