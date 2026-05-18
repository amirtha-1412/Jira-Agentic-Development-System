"""
workflows/orchestrator/graph.py
---------------------------------------------
LangGraph Multi-Agent Workflow Orchestrator
Builds and executes the full pipeline:
  Jira Ticket → Requirement → Developer → QA → PR

Graph Structure:
  START
    ↓
  requirement_node
    ↓
  developer_node
    ↓
  qa_node ←──┐ (retry loop)
    ↓        │
  [conditional: test_passed?]
    ├─ YES → pr_node → END
    └─ NO  → developer_node (retry)

Features:
  - Automatic retry on QA failures
  - Transparent execution logs
  - State persistence
  - Error handling at every node
"""

from langgraph.graph import StateGraph, END
from workflows.state import WorkflowState, create_initial_state, state_summary
from workflows.nodes import (
    requirement_node,
    developer_node,
    qa_node,
    pr_node,
)


# ─────────────────────────────────────────────
# Conditional Edge: Should we retry development?
# ─────────────────────────────────────────────

def should_retry_development(state: WorkflowState) -> str:
    """
    Conditional routing after QA node.
    
    Returns:
        "pr_node"        → Tests passed, proceed to PR
        "developer_node" → Tests failed, retry development
        "end"            → Max retries exceeded or critical error
    """
    test_status = state.get("test_status", "NOT_RUN")
    errors      = state.get("errors", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)
    
    # Critical errors → abort
    if errors and any("CRITICAL" in e.upper() for e in errors):
        print(f"  [Conditional] Critical error detected → END")
        return "end"
    
    # Max retries exceeded → proceed to PR anyway (with warnings)
    if retry_count >= max_retries:
        print(f"  [Conditional] Max retries ({max_retries}) exceeded → PR")
        return "pr_node"
    
    # Tests passed → proceed to PR
    if test_status == "PASSED":
        print(f"  [Conditional] Tests PASSED → PR")
        return "pr_node"
    
    # Tests failed → retry development
    if test_status in ["FAILED", "PARTIAL"]:
        print(f"  [Conditional] Tests {test_status} → RETRY (attempt {retry_count + 1})")
        return "developer_node"
    
    # Default: proceed to PR
    print(f"  [Conditional] Default path → PR")
    return "pr_node"


# ─────────────────────────────────────────────
# Graph Builder
# ─────────────────────────────────────────────

def build_workflow_graph() -> StateGraph:
    """
    Constructs the LangGraph workflow with all nodes
    and conditional edges.
    
    Returns:
        StateGraph: Compiled executable graph
    """
    print("\n" + "=" * 60)
    print("  BUILDING LANGGRAPH WORKFLOW")
    print("=" * 60)
    
    # Initialize graph with WorkflowState schema
    graph = StateGraph(WorkflowState)
    
    # ── Add Nodes ─────────────────────────────
    print("  [Graph] Adding nodes...")
    graph.add_node("requirement_node", requirement_node)
    graph.add_node("developer_node",   developer_node)
    graph.add_node("qa_node",          qa_node)
    graph.add_node("pr_node",          pr_node)
    print("  [Graph] ✅ 4 nodes added")
    
    # ── Set Entry Point ───────────────────────
    graph.set_entry_point("requirement_node")
    print("  [Graph] ✅ Entry point: requirement_node")
    
    # ── Add Sequential Edges ──────────────────
    print("  [Graph] Adding edges...")
    graph.add_edge("requirement_node", "developer_node")
    graph.add_edge("developer_node",   "qa_node")
    graph.add_edge("pr_node",          END)
    print("  [Graph] ✅ Sequential edges added")
    
    # ── Add Conditional Edge (QA → retry or PR) ───
    graph.add_conditional_edges(
        "qa_node",
        should_retry_development,
        {
            "developer_node": "developer_node",  # Retry development
            "pr_node":        "pr_node",         # Proceed to PR
            "end":            END,               # Abort workflow
        }
    )
    print("  [Graph] ✅ Conditional edge added (QA retry logic)")
    
    print("=" * 60)
    print("  GRAPH CONSTRUCTION COMPLETE")
    print("=" * 60 + "\n")
    
    return graph


# ─────────────────────────────────────────────
# Graph Compiler
# ─────────────────────────────────────────────

def compile_workflow() -> StateGraph:
    """
    Builds and compiles the workflow graph.
    Ready for execution.
    
    Returns:
        Compiled StateGraph ready to invoke()
    """
    graph    = build_workflow_graph()
    compiled = graph.compile()
    
    print("  [Compiler] ✅ Workflow compiled successfully")
    print("  [Compiler] Ready for execution\n")
    
    return compiled


# ─────────────────────────────────────────────
# Workflow Executor
# ─────────────────────────────────────────────

def execute_workflow(
    ticket_id:   str,
    ticket_data: dict = None,
    max_retries: int  = 2,
    verbose:     bool = True,
) -> WorkflowState:
    """
    Executes the full multi-agent workflow for a Jira ticket.
    
    Args:
        ticket_id:   Jira ticket ID (e.g. "SCRUM-1")
        ticket_data: Optional pre-fetched ticket dict
        max_retries: Max QA retry attempts (default: 2)
        verbose:     Print execution logs
    
    Returns:
        WorkflowState: Final state after workflow completion
    """
    if verbose:
        print("\n" + "=" * 70)
        print(f"  EXECUTING WORKFLOW: {ticket_id}")
        print("=" * 70)
    
    # ── Initialize State ──────────────────────
    initial_state = create_initial_state(ticket_id, ticket_data)
    initial_state["max_retries"] = max_retries
    initial_state["retry_count"] = 0
    
    if verbose:
        print(f"\n  [Executor] Initial state created")
        print(f"  [Executor] Ticket ID: {ticket_id}")
        print(f"  [Executor] Max retries: {max_retries}")
    
    # ── Compile Graph ─────────────────────────
    workflow = compile_workflow()
    
    # ── Execute Workflow ──────────────────────
    try:
        if verbose:
            print(f"\n  [Executor] Starting workflow execution...")
            print("  " + "-" * 68 + "\n")
        
        final_state = workflow.invoke(initial_state)
        
        if verbose:
            print("\n  " + "-" * 68)
            print(f"  [Executor] ✅ Workflow completed")
            print(f"  [Executor] Final stage: {final_state.get('current_stage')}")
            print(f"  [Executor] Status: {final_state.get('pipeline_status')}")
            print(f"  [Executor] Retries used: {final_state.get('retry_count', 0)}")
            
            if final_state.get("errors"):
                print(f"  [Executor] ⚠️  Errors: {len(final_state['errors'])}")
                for err in final_state["errors"]:
                    print(f"    - {err}")
        
        return final_state
    
    except Exception as e:
        if verbose:
            print(f"\n  [Executor] ❌ Workflow execution failed: {e}")
        
        # Return error state
        return {
            **initial_state,
            "pipeline_status": "failed",
            "current_stage":   "error",
            "errors":          initial_state.get("errors", []) + [str(e)],
        }
    
    finally:
        if verbose:
            print("=" * 70 + "\n")


# ─────────────────────────────────────────────
# Workflow Status Checker
# ─────────────────────────────────────────────

def get_workflow_status(state: WorkflowState) -> dict:
    """
    Returns a human-readable status summary of the workflow.
    
    Args:
        state: Current or final WorkflowState
    
    Returns:
        dict: Status summary with progress indicators
    """
    completed = state.get("completed_stages", [])
    
    return {
        "ticket_id":        state.get("ticket_id", "N/A"),
        "pipeline_status":  state.get("pipeline_status", "unknown"),
        "current_stage":    state.get("current_stage", "unknown"),
        "progress": {
            "requirement": "✅" if "requirement" in completed else "⏳",
            "developer":   "✅" if "developer"   in completed else "⏳",
            "qa":          "✅" if "qa"          in completed else "⏳",
            "pr":          "✅" if "pr"          in completed else "⏳",
        },
        "retry_count":      state.get("retry_count", 0),
        "test_status":      state.get("test_status", "NOT_RUN"),
        "code_ready":       state.get("code_ready", False),
        "pr_ready":         state.get("pr_ready", False),
        "errors":           len(state.get("errors", [])),
        "summary":          state.get("summary", "")[:100],
    }


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    
    print("\n" + "=" * 70)
    print("  LANGGRAPH WORKFLOW - COMPILATION TEST")
    print("=" * 70)
    
    # Test 1: Graph compilation
    print("\n[TEST 1] Graph Compilation")
    print("-" * 70)
    try:
        workflow = compile_workflow()
        print("  ✅ Graph compiled successfully")
        print(f"  ✅ Type: {type(workflow)}")
    except Exception as e:
        print(f"  ❌ Compilation failed: {e}")
    
    # Test 2: Conditional logic
    print("\n[TEST 2] Conditional Edge Logic")
    print("-" * 70)
    
    test_states = [
        {"test_status": "PASSED", "retry_count": 0, "errors": []},
        {"test_status": "FAILED", "retry_count": 0, "errors": []},
        {"test_status": "FAILED", "retry_count": 2, "errors": [], "max_retries": 2},
        {"test_status": "FAILED", "retry_count": 0, "errors": ["CRITICAL: System crash"]},
    ]
    
    for i, state in enumerate(test_states, 1):
        result = should_retry_development(state)
        print(f"  Test {i}: status={state.get('test_status')}, "
              f"retry={state.get('retry_count')} → {result}")
    
    print("\n" + "=" * 70)
    print("  [DONE] Graph compilation test complete")
    print("=" * 70 + "\n")
