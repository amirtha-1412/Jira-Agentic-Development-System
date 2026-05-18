"""
Jira Agentic Development System — Backend Entry Point
FastAPI server that orchestrates all AI agents and exposes REST APIs.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
from backend.jira.jira_routes import router as jira_router
from vectorstore.retrieval_routes import router as retrieval_router
from agents.requirement_analyst.requirement_routes import router as analyst_router
from workflows.workflow_routes import router as workflow_router

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Jira Agentic Development System",
    description="Multi-agent AI workflow to automate software development lifecycle tasks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware — allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Register Routers
# ─────────────────────────────────────────────
app.include_router(jira_router)
app.include_router(retrieval_router)
app.include_router(analyst_router)
app.include_router(workflow_router)


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "✅ Jira Agentic Dev System is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return JSONResponse(content={"status": "healthy", "service": "backend"})


# ─────────────────────────────────────────────
# Execute Ticket — Core Workflow Trigger
# ─────────────────────────────────────────────
@app.post("/execute-ticket/{ticket_id}", tags=["Workflow"])
async def execute_ticket(ticket_id: str):
    """
    Main entrypoint: Triggers the full multi-agent pipeline for a given Jira ticket.
    Agents involved: Requirement Analyst → Developer → QA → PR Generator
    
    This endpoint executes the complete LangGraph workflow with automatic
    retry logic for QA failures.
    """
    try:
        from workflows.orchestrator.graph import execute_workflow, get_workflow_status
        
        # Execute the full workflow
        final_state = execute_workflow(
            ticket_id=ticket_id.upper(),
            max_retries=2,
            verbose=True,
        )
        
        # Get status summary
        status = get_workflow_status(final_state)
        
        return {
            "success":         final_state.get("pipeline_status") == "completed",
            "ticket_id":       ticket_id.upper(),
            "status":          final_state.get("pipeline_status"),
            "current_stage":   final_state.get("current_stage"),
            "completed_stages": final_state.get("completed_stages", []),
            "retry_count":     final_state.get("retry_count", 0),
            "test_status":     final_state.get("test_status"),
            "pr_ready":        final_state.get("pr_ready", False),
            "summary":         final_state.get("summary", ""),
            "errors":          final_state.get("errors", []),
            "progress":        status.get("progress", {}),
            "stages": [
                "requirement_analysis",
                "code_generation",
                "test_generation",
                "pr_creation",
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


# ─────────────────────────────────────────────
# Agent Status Endpoints (Stubs — to be wired later)
# ─────────────────────────────────────────────
@app.get("/agents/status", tags=["Agents"])
async def agents_status():
    return {
        "requirement_agent": "idle",
        "developer_agent": "idle",
        "qa_agent": "idle",
        "pr_agent": "idle",
    }


# ─────────────────────────────────────────────
# Run Server
# ─────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
