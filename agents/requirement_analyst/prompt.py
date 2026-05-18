"""
agents/requirement_analyst/prompt.py
---------------------------------------------
Structured Prompt Templates
Provides consistent, versioned prompt templates
for the Requirement Analyst Agent.

Design principles:
  - Clear role definition (system prompt)
  - Structured output format (prevents hallucination)
  - Variable interpolation via .format()
  - Versioned templates for stability
"""

# ─────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Senior Software Requirement Analyst AI agent.

Your responsibilities:
1. Analyze Jira tickets carefully and extract structured requirements
2. Identify what needs to be built, why, and how
3. Detect ambiguities and flag them clearly
4. Suggest technical implementation steps
5. Always reason from the codebase context provided

Rules:
- Be specific and actionable, never vague
- Use the provided codebase context to ground your analysis
- If a field is truly unknown, state "NOT SPECIFIED" — never guess
- Structure your response exactly as the template requires
- Keep implementation steps concise and developer-ready
"""


# ─────────────────────────────────────────────
# MAIN ANALYSIS PROMPT TEMPLATE
# ─────────────────────────────────────────────

ANALYSIS_PROMPT_TEMPLATE = """
## Jira Ticket Information

**Ticket ID**: {ticket_id}
**Title**: {title}
**Status**: {status}
**Priority**: {priority}
**Issue Type**: {issue_type}
**Assignee**: {assignee}

**Description**:
{description}

---

## Relevant Codebase Context

The following code from the repository is semantically relevant to this ticket:

{code_context}

---

## Your Task

Analyze this Jira ticket and produce a structured requirement analysis.
Respond in the EXACT format below — no extra sections, no markdown outside the template:

### 1. SUMMARY
[One sentence describing what this ticket requires]

### 2. FUNCTIONAL REQUIREMENTS
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]
(List all functional requirements extracted from the ticket)

### 3. TECHNICAL REQUIREMENTS
- [Technical constraint or technology involved]
- [API / DB / service affected]
(List technical requirements based on ticket + codebase context)

### 4. AFFECTED FILES
- [file path] — [reason it is affected]
(Based on the codebase context provided, list files that will likely need changes)

### 5. IMPLEMENTATION STEPS
1. [Step 1 — specific and actionable]
2. [Step 2]
3. [Step 3]
(List ordered implementation steps a developer should follow)

### 6. AMBIGUITIES
- [Any unclear or missing information in the ticket]
(List open questions or "NONE" if the ticket is fully specified)

### 7. RISK ASSESSMENT
- Priority: {priority}
- Risk Level: [LOW / MEDIUM / HIGH]
- Reason: [Brief reason for the risk level]
"""


# ─────────────────────────────────────────────
# NO-CONTEXT FALLBACK TEMPLATE
# ─────────────────────────────────────────────

NO_CONTEXT_PROMPT_TEMPLATE = """
## Jira Ticket Information

**Ticket ID**: {ticket_id}
**Title**: {title}
**Status**: {status}
**Priority**: {priority}
**Issue Type**: {issue_type}
**Assignee**: {assignee}

**Description**:
{description}

---

No codebase context is available for this ticket.
Analyze it based solely on the ticket information above.

Respond in the EXACT format:

### 1. SUMMARY
[One sentence describing what this ticket requires]

### 2. FUNCTIONAL REQUIREMENTS
- [Requirement 1]
- [Requirement 2]

### 3. TECHNICAL REQUIREMENTS
- [Technical constraint or technology involved]

### 4. AFFECTED FILES
- NOT SPECIFIED (no codebase context available)

### 5. IMPLEMENTATION STEPS
1. [Step 1]
2. [Step 2]

### 6. AMBIGUITIES
- [Any unclear or missing information]

### 7. RISK ASSESSMENT
- Priority: {priority}
- Risk Level: [LOW / MEDIUM / HIGH]
- Reason: [Brief reason]
"""


# ─────────────────────────────────────────────
# Template Builder
# ─────────────────────────────────────────────

def build_analysis_prompt(
    ticket_id:    str,
    title:        str,
    description:  str,
    status:       str,
    priority:     str,
    issue_type:   str,
    assignee:     str,
    code_context: str = "",
) -> str:
    """
    Builds the final user prompt by interpolating
    ticket data into the analysis template.

    Args:
        ticket_id:    Jira ticket ID (e.g. SCRUM-1)
        title:        Ticket summary/title
        description:  Full ticket description
        status:       Ticket status (TODO, IN_PROGRESS, etc.)
        priority:     Priority (HIGH, MEDIUM, LOW, NONE)
        issue_type:   Jira issue type (Story, Task, Bug, etc.)
        assignee:     Assigned developer or "Unassigned"
        code_context: Semantic search context string from retriever

    Returns:
        str: Fully interpolated prompt string
    """
    template = ANALYSIS_PROMPT_TEMPLATE if code_context.strip() \
               else NO_CONTEXT_PROMPT_TEMPLATE

    return template.format(
        ticket_id   = ticket_id   or "N/A",
        title       = title       or "N/A",
        description = description or "NOT SPECIFIED",
        status      = status      or "N/A",
        priority    = priority    or "NONE",
        issue_type  = issue_type  or "N/A",
        assignee    = assignee    or "Unassigned",
        code_context= code_context or "",
    )


def get_system_prompt() -> str:
    """Returns the system prompt for the analyst agent."""
    return SYSTEM_PROMPT.strip()


# ─────────────────────────────────────────────
# ENGINEERING TASKS PROMPT
# ─────────────────────────────────────────────

ENGINEERING_TASKS_TEMPLATE = """
## Ticket: {ticket_id} — {title}

**Priority**: {priority} | **Status**: {status} | **Type**: {issue_type}

**Description**:
{description}

**Relevant Code Context**:
{code_context}

---

## Your Task

Convert this Jira ticket into a precise engineering task breakdown.
Respond in the EXACT format below:

### 1. EPIC GOAL
[One sentence: what this ticket achieves for the user or system]

### 2. ENGINEERING TASKS
- TASK-1: [Specific engineering task with clear deliverable]
- TASK-2: [Specific engineering task]
- TASK-3: [Specific engineering task]
(Break the ticket into 3–7 atomic, testable tasks)

### 3. ORDERED EXECUTION PLAN
1. [First task to execute — no dependencies]
2. [Second task]
3. [Third task]
(Order by dependency: foundational tasks first)

### 4. ACCEPTANCE CRITERIA
- [ ] [Verifiable criterion 1]
- [ ] [Verifiable criterion 2]
- [ ] [Verifiable criterion 3]
(Each criterion must be testable by QA)

### 5. ESTIMATED COMPLEXITY
- Complexity: [XS / S / M / L / XL]
- Story Points: [1 / 2 / 3 / 5 / 8 / 13]
- Reason: [Brief justification]
"""


def build_engineering_tasks_prompt(
    ticket_id: str, title: str, description: str,
    status: str, priority: str, issue_type: str,
    code_context: str = "",
) -> str:
    """Builds the Engineering Tasks breakdown prompt."""
    return ENGINEERING_TASKS_TEMPLATE.format(
        ticket_id    = ticket_id    or "N/A",
        title        = title        or "N/A",
        description  = description  or "NOT SPECIFIED",
        status       = status       or "N/A",
        priority     = priority     or "NONE",
        issue_type   = issue_type   or "N/A",
        code_context = code_context or "No context available.",
    )


# ─────────────────────────────────────────────
# EDGE CASE ANALYZER PROMPT
# ─────────────────────────────────────────────

EDGE_CASE_TEMPLATE = """
## Ticket: {ticket_id} — {title}

**Priority**: {priority} | **Type**: {issue_type}

**Description**:
{description}

**Relevant Code Context**:
{code_context}

---

## Your Task

Analyze this ticket for implementation risks, edge cases, and security vulnerabilities.
Respond in the EXACT format below:

### 1. EDGE CASES
- EDGE-1: [Specific edge case that could break the feature]
- EDGE-2: [Another edge case]
- EDGE-3: [Another edge case]
(List all non-obvious scenarios: empty input, boundary values, concurrent access, etc.)

### 2. SECURITY RISKS
- SEC-1: [Specific security vulnerability or concern]
- SEC-2: [Another security risk]
(Consider: injection, auth bypass, data exposure, rate limiting, token theft, etc.)

### 3. PERFORMANCE RISKS
- PERF-1: [Potential performance bottleneck]
- PERF-2: [Another performance concern]
(Consider: N+1 queries, large payloads, missing indexes, slow external calls)

### 4. ERROR SCENARIOS
- ERR-1: [Failure mode that must be handled]
- ERR-2: [Another error scenario]
(Consider: network failures, DB errors, invalid tokens, expired sessions)

### 5. MITIGATION STRATEGIES
- EDGE-1 → [How to handle it]
- SEC-1  → [How to mitigate it]
- PERF-1 → [How to optimize it]
(Pair each risk with a concrete mitigation)

### 6. OVERALL RISK RATING
- Rating: [LOW / MEDIUM / HIGH / CRITICAL]
- Reason: [Brief justification]
"""


def build_edge_case_prompt(
    ticket_id: str, title: str, description: str,
    priority: str, issue_type: str,
    code_context: str = "",
) -> str:
    """Builds the Edge Case Analyzer prompt."""
    return EDGE_CASE_TEMPLATE.format(
        ticket_id    = ticket_id    or "N/A",
        title        = title        or "N/A",
        description  = description  or "NOT SPECIFIED",
        priority     = priority     or "NONE",
        issue_type   = issue_type   or "N/A",
        code_context = code_context or "No context available.",
    )


# ─────────────────────────────────────────────
# EXPLAINABLE REASONING PROMPT
# ─────────────────────────────────────────────

REASONING_TEMPLATE = """
## Ticket: {ticket_id} — {title}

**Priority**: {priority} | **Status**: {status}

**Description**:
{description}

**Relevant Code Context**:
{code_context}

---

## Your Task

Generate a transparent, step-by-step reasoning trace explaining your analysis of this ticket.
This reasoning will be shown to developers to build trust in the AI agent's decisions.

Respond in the EXACT format below:

### 1. INITIAL UNDERSTANDING
[What I understood from the ticket at first glance, in plain English]

### 2. REASONING CHAIN
Step 1: [First reasoning step — what I examined]
Step 2: [What I inferred from that]
Step 3: [How I connected it to the codebase context]
Step 4: [What conclusion I reached]
(Show your chain-of-thought clearly, 3–5 steps)

### 3. EVIDENCE FROM CONTEXT
- [Specific file or code snippet from the context that supports my analysis]
- [Another piece of evidence]
(Ground your reasoning in the provided codebase context)

### 4. ASSUMPTIONS MADE
- [Explicit assumption 1 I made during analysis]
- [Explicit assumption 2]
(Be transparent about what you assumed vs. what was stated)

### 5. CONFIDENCE ASSESSMENT
- Confidence: [LOW / MEDIUM / HIGH]
- Reason: [Why I am or am not confident in my analysis]
- What would increase confidence: [Additional info needed]

### 6. SUMMARY CONCLUSION
[One paragraph synthesizing the full reasoning into a final recommendation]
"""


def build_reasoning_prompt(
    ticket_id: str, title: str, description: str,
    status: str, priority: str,
    code_context: str = "",
) -> str:
    """Builds the Explainable Reasoning prompt."""
    return REASONING_TEMPLATE.format(
        ticket_id    = ticket_id    or "N/A",
        title        = title        or "N/A",
        description  = description  or "NOT SPECIFIED",
        status       = status       or "N/A",
        priority     = priority     or "NONE",
        code_context = code_context or "No context available.",
    )


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("\n" + "=" * 55)
    print("  PROMPT TEMPLATE - TEST RUN")
    print("=" * 55)

    prompt = build_analysis_prompt(
        ticket_id   = "SCRUM-1",
        title       = "Add forgot password functionality",
        description = "Create a password reset flow using email token verification.",
        status      = "TODO",
        priority    = "HIGH",
        issue_type  = "Task",
        assignee    = "Unassigned",
        code_context= "# File: backend/auth.py\ndef authenticate(email, api_key): ...",
    )

    print(f"\n  [OK] Prompt generated  : {len(prompt)} chars")
    print(f"  [OK] Contains ticket_id: {'SCRUM-1' in prompt}")
    print(f"  [OK] Contains title    : {'forgot password' in prompt}")
    print(f"  [OK] Contains context  : {'backend/auth.py' in prompt}")
    print(f"\n  Preview (first 400 chars):")
    print(f"  {prompt[:400]}")
    print("\n" + "=" * 55)
    print("  [DONE] Prompt template test complete.")
    print("=" * 55 + "\n")
