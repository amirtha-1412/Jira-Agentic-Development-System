"""
workflows/state.py
---------------------------------------------
Shared Workflow State
TypedDict that all LangGraph agents read/write.

All agents share this single state object so that:
  - requirements  -> developer node
  - generated code -> QA node
  - test results  -> PR node
  - reasoning traces -> audit log

State is immutable between nodes — each node
returns a partial dict that LangGraph merges.
"""

from __future__ import annotations
from typing import TypedDict, Optional, Any


# ─────────────────────────────────────────────
# Workflow State
# ─────────────────────────────────────────────

class WorkflowState(TypedDict, total=False):
    """
    Shared memory between all agents in the pipeline.
    Every field is Optional — agents write only their outputs.

    Pipeline flow:
      ticket_id + ticket_data
          ↓ RequirementNode
      requirements + reasoning_trace
          ↓ DeveloperNode
      generated_code + affected_files
          ↓ QANode
      test_results + test_status
          ↓ PRNode
      pr_description + pr_ready
    """

    # ── Input ─────────────────────────────────
    ticket_id:          str                   # e.g. "SCRUM-1"
    ticket_data:        dict[str, Any]        # raw Jira ticket dict

    # ── Requirement Analyst output ─────────────
    requirements:       dict[str, Any]        # full AnalysisResult.to_dict()
    summary:            str                   # one-line ticket summary
    functional_reqs:    list[str]             # bullet list of func requirements
    technical_reqs:     list[str]             # bullet list of tech requirements
    implementation_steps: list[str]           # ordered dev steps
    affected_files:     list[str]             # files that will change
    risk_level:         str                   # LOW / MEDIUM / HIGH
    reasoning_trace:    str                   # explainable reasoning output
    edge_cases:         str                   # edge case analysis output
    engineering_tasks:  str                   # TASK-N breakdown output

    # ── Developer Agent output ─────────────────
    generated_code:     dict[str, str]        # {filename: code_string}
    code_diff:          str                   # unified diff string
    code_ready:         bool                  # True when code generation done

    # ── QA Agent output ────────────────────────
    test_cases:         list[str]             # generated test descriptions
    test_results:       dict[str, Any]        # {test_name: pass/fail}
    test_status:        str                   # PASSED / FAILED / PARTIAL
    qa_notes:           str                   # QA agent narrative

    # ── PR Agent output ────────────────────────
    pr_title:           str                   # pull request title
    pr_description:     str                   # full PR body markdown
    pr_labels:          list[str]             # PR labels (feature, bugfix, etc.)
    reviewers_suggested: list[str]            # suggested reviewers
    pr_ready:           bool                  # True when PR is ready

    # ── Pipeline metadata ──────────────────────
    current_stage:      str                   # requirement/developer/qa/pr
    completed_stages:   list[str]             # stages finished
    errors:             list[str]             # any errors encountered
    pipeline_status:    str                   # running / completed / failed
    retry_count:        int                   # current retry attempt count
    max_retries:        int                   # maximum allowed retries


# ─────────────────────────────────────────────
# Initial State Factory
# ─────────────────────────────────────────────

def create_initial_state(ticket_id: str, ticket_data: dict = None) -> WorkflowState:
    """
    Creates a fresh WorkflowState for a new pipeline run.

    Args:
        ticket_id:   Jira ticket ID (e.g. "SCRUM-1")
        ticket_data: Optional pre-fetched ticket dict

    Returns:
        WorkflowState: Initialized state ready for pipeline
    """
    return WorkflowState(
        ticket_id          = ticket_id,
        ticket_data        = ticket_data or {},
        requirements       = {},
        summary            = "",
        functional_reqs    = [],
        technical_reqs     = [],
        implementation_steps = [],
        affected_files     = [],
        risk_level         = "MEDIUM",
        reasoning_trace    = "",
        edge_cases         = "",
        engineering_tasks  = "",
        generated_code     = {},
        code_diff          = "",
        code_ready         = False,
        test_cases         = [],
        test_results       = {},
        test_status        = "NOT_RUN",
        qa_notes           = "",
        pr_title           = "",
        pr_description     = "",
        pr_labels          = [],
        reviewers_suggested = [],
        pr_ready           = False,
        current_stage      = "initialized",
        completed_stages   = [],
        errors             = [],
        pipeline_status    = "initialized",
        retry_count        = 0,
        max_retries        = 2,
    )


def state_summary(state: WorkflowState) -> str:
    """Returns a human-readable summary of state progress."""
    lines = [
        f"Ticket       : {state.get('ticket_id', 'N/A')}",
        f"Stage        : {state.get('current_stage', 'N/A')}",
        f"Status       : {state.get('pipeline_status', 'N/A')}",
        f"Completed    : {state.get('completed_stages', [])}",
        f"Summary      : {state.get('summary', '')[:60]}",
        f"Func Reqs    : {len(state.get('functional_reqs', []))} items",
        f"Steps        : {len(state.get('implementation_steps', []))} items",
        f"Risk         : {state.get('risk_level', 'N/A')}",
        f"Code Ready   : {state.get('code_ready', False)}",
        f"Test Status  : {state.get('test_status', 'NOT_RUN')}",
        f"PR Ready     : {state.get('pr_ready', False)}",
        f"Errors       : {len(state.get('errors', []))}",
    ]
    return "\n  ".join(lines)
