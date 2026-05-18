"""
agents/requirement_analyst/analyzer.py
---------------------------------------------
Requirement Analyst Agent
Analyzes Jira tickets using LLM + semantic retriever.
"""

import re
from dataclasses import dataclass, field
from agents.llm import call_llm
from agents.requirement_analyst.prompt import build_analysis_prompt, get_system_prompt


@dataclass
class AnalysisResult:
    ticket_id:               str
    title:                   str
    summary:                 str  = ""
    functional_requirements: list = field(default_factory=list)
    technical_requirements:  list = field(default_factory=list)
    affected_files:          list = field(default_factory=list)
    implementation_steps:    list = field(default_factory=list)
    ambiguities:             list = field(default_factory=list)
    risk_level:              str  = "MEDIUM"
    risk_reason:             str  = ""
    raw_response:            str  = ""
    success:                 bool = False
    error:                   str  = ""

    def to_dict(self) -> dict:
        return {
            "ticket_id":               self.ticket_id,
            "title":                   self.title,
            "summary":                 self.summary,
            "functional_requirements": self.functional_requirements,
            "technical_requirements":  self.technical_requirements,
            "affected_files":          self.affected_files,
            "implementation_steps":    self.implementation_steps,
            "ambiguities":             self.ambiguities,
            "risk_level":              self.risk_level,
            "risk_reason":             self.risk_reason,
            "success":                 self.success,
            "error":                   self.error,
        }


def _extract_section(text: str, header: str) -> str:
    pattern = rf"###\s+{re.escape(header)}\s*\n(.*?)(?=###|\Z)"
    match   = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _parse_bullets(text: str) -> list[str]:
    return [
        line[2:].strip() for line in text.strip().split("\n")
        if line.strip().startswith("- ") and line[2:].strip()
    ]


def _parse_numbered(text: str) -> list[str]:
    result = []
    for line in text.strip().split("\n"):
        m = re.match(r"^\d+\.\s+(.+)", line.strip())
        if m:
            result.append(m.group(1).strip())
    return result


def _parse_response(raw: str, ticket_id: str, title: str) -> AnalysisResult:
    r = AnalysisResult(ticket_id=ticket_id, title=title, raw_response=raw, success=True)
    r.summary                 = _extract_section(raw, "1. SUMMARY")
    r.functional_requirements = _parse_bullets(_extract_section(raw, "2. FUNCTIONAL REQUIREMENTS"))
    r.technical_requirements  = _parse_bullets(_extract_section(raw, "3. TECHNICAL REQUIREMENTS"))
    r.affected_files          = _parse_bullets(_extract_section(raw, "4. AFFECTED FILES"))
    r.implementation_steps    = _parse_numbered(_extract_section(raw, "5. IMPLEMENTATION STEPS"))
    r.ambiguities             = _parse_bullets(_extract_section(raw, "6. AMBIGUITIES"))
    risk_text = _extract_section(raw, "7. RISK ASSESSMENT")
    m = re.search(r"Risk Level:\s*(LOW|MEDIUM|HIGH)", risk_text, re.IGNORECASE)
    if m: r.risk_level = m.group(1).upper()
    m = re.search(r"Reason:\s*(.+)", risk_text)
    if m: r.risk_reason = m.group(1).strip()
    return r


class RequirementAnalyst:
    """AI agent that analyzes Jira tickets into structured requirements."""

    def __init__(self, use_retriever: bool = True):
        self.use_retriever = use_retriever
        self._retriever    = None

    def _get_retriever(self):
        if self._retriever is None:
            try:
                from vectorstore.retriever import CodeRetriever
                self._retriever = CodeRetriever()
            except Exception:
                self._retriever = None
        return self._retriever

    def analyze(self, ticket_data: dict) -> AnalysisResult:
        ticket_id   = ticket_data.get("ticket_id", "UNKNOWN")
        title       = ticket_data.get("title") or ticket_data.get("summary", "N/A")
        description = ticket_data.get("description", "NOT SPECIFIED")
        status      = ticket_data.get("status", "N/A")
        priority    = ticket_data.get("priority", "NONE")
        issue_type  = ticket_data.get("issue_type", "N/A")
        assignee    = ticket_data.get("assignee", "Unassigned")

        code_context = ""
        if self.use_retriever:
            try:
                r = self._get_retriever()
                if r and r.is_ready():
                    code_context = r.get_context(
                        query=f"{title} {description[:200]}", top_k=4, min_sim=0.20
                    )
            except Exception:
                code_context = ""

        user_prompt = build_analysis_prompt(
            ticket_id=ticket_id, title=title, description=description,
            status=status, priority=priority, issue_type=issue_type,
            assignee=assignee, code_context=code_context,
        )

        try:
            raw = call_llm(user_prompt=user_prompt, system_prompt=get_system_prompt())
            return _parse_response(raw, ticket_id, title)
        except Exception as e:
            return AnalysisResult(ticket_id=ticket_id, title=title,
                                  success=False, error=str(e))

    def analyze_from_id(self, ticket_id: str) -> AnalysisResult:
        try:
            from backend.jira.ticket_fetcher import fetch_ticket
            ticket = fetch_ticket(ticket_id)
            if not ticket.get("success"):
                return AnalysisResult(ticket_id=ticket_id, title="",
                                      success=False, error=ticket.get("error", "Fetch failed"))
            return self.analyze(ticket)
        except Exception as e:
            return AnalysisResult(ticket_id=ticket_id, title="",
                                  success=False, error=str(e))


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("\n" + "=" * 55)
    print("  ANALYZER - TEST RUN")
    print("=" * 55)
    ticket = {
        "ticket_id": "SCRUM-1", "title": "Add forgot password functionality",
        "description": "Users need to reset password via email. Token must expire in 24h.",
        "status": "TODO", "priority": "HIGH", "issue_type": "Task", "assignee": "Unassigned",
    }
    analyst = RequirementAnalyst(use_retriever=False)
    result  = analyst.analyze(ticket)
    print(f"\n  [OK] Success   : {result.success}")
    print(f"  [OK] Summary   : {result.summary[:80]}")
    print(f"  [OK] Func Reqs : {len(result.functional_requirements)}")
    print(f"  [OK] Steps     : {len(result.implementation_steps)}")
    print(f"  [OK] Risk      : {result.risk_level}")
    print("\n" + "=" * 55 + "\n")
