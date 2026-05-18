"""
agents/pr_agent/pr_generator.py
---------------------------------------------
PR Agent - Real Pull Request Generation
Generates comprehensive PR descriptions with LLM.

Features:
  - LLM-powered PR description generation
  - Includes code changes summary
  - Test results integration
  - Risk assessment
  - Reviewer suggestions
  - Checklist generation
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from agents.llm import call_llm


# ─────────────────────────────────────────────
# PR Generation Result
# ─────────────────────────────────────────────

@dataclass
class PRResult:
    """Result of PR generation."""
    success: bool
    pr_title: str = ""
    pr_description: str = ""
    pr_labels: List[str] = None
    reviewers_suggested: List[str] = None
    pr_ready: bool = False
    error: str = ""
    
    def __post_init__(self):
        if self.pr_labels is None:
            self.pr_labels = []
        if self.reviewers_suggested is None:
            self.reviewers_suggested = []
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "pr_title": self.pr_title,
            "pr_description": self.pr_description,
            "pr_labels": self.pr_labels,
            "reviewers_suggested": self.reviewers_suggested,
            "pr_ready": self.pr_ready,
            "error": self.error,
        }


# ─────────────────────────────────────────────
# PR Agent
# ─────────────────────────────────────────────

class PRAgent:
    """
    AI-powered PR generation agent.
    Creates comprehensive pull request descriptions.
    """
    
    def __init__(self):
        pass
    
    # ─────────────────────────────────────────
    # Main Generation Method
    # ─────────────────────────────────────────
    
    def generate_pr(
        self,
        ticket_id: str,
        summary: str,
        requirements: dict,
        generated_code: Dict[str, str],
        test_status: str,
        qa_notes: str,
        retry_count: int = 0,
    ) -> PRResult:
        """
        Generates a comprehensive PR description.
        
        Args:
            ticket_id: Jira ticket ID
            summary: Ticket summary
            requirements: Functional requirements
            generated_code: Generated code files
            test_status: QA test status
            qa_notes: QA feedback
            retry_count: Number of retries
        
        Returns:
            PRResult with PR title and description
        """
        try:
            # Build PR generation prompt
            prompt = self._build_pr_prompt(
                ticket_id=ticket_id,
                summary=summary,
                requirements=requirements,
                generated_code=generated_code,
                test_status=test_status,
                qa_notes=qa_notes,
                retry_count=retry_count,
            )
            
            # Generate PR with LLM
            print(f"  [PRAgent] Generating PR for {ticket_id}...")
            
            response = call_llm(
                user_prompt=prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.3,
            )
            
            # Parse response
            result = self._parse_pr_response(response, ticket_id, summary)
            
            if result.success:
                print(f"  [PRAgent] ✅ PR generated successfully")
                print(f"  [PRAgent] Title: {result.pr_title[:60]}...")
                print(f"  [PRAgent] Labels: {', '.join(result.pr_labels)}")
            else:
                print(f"  [PRAgent] ❌ PR generation failed: {result.error}")
            
            return result
        
        except Exception as e:
            print(f"  [PRAgent] ❌ Exception: {e}")
            return PRResult(
                success=False,
                error=str(e),
            )
    
    # ─────────────────────────────────────────
    # Prompt Building
    # ─────────────────────────────────────────
    
    def _build_pr_prompt(
        self,
        ticket_id: str,
        summary: str,
        requirements: dict,
        generated_code: Dict[str, str],
        test_status: str,
        qa_notes: str,
        retry_count: int,
    ) -> str:
        """Builds the PR generation prompt."""
        
        functional_reqs = requirements.get("functional_requirements", [])
        risk_level = requirements.get("risk_level", "MEDIUM")
        
        prompt = f"""# Pull Request Generation Task

## Ticket: {ticket_id}
**Summary**: {summary}

## Functional Requirements Implemented:
"""
        for i, req in enumerate(functional_reqs, 1):
            prompt += f"{i}. {req}\n"
        
        prompt += f"\n## Code Changes:\n"
        prompt += f"**Files Modified/Created**: {len(generated_code)}\n"
        for filename in list(generated_code.keys())[:5]:
            prompt += f"  - {filename}\n"
        
        prompt += f"\n## Test Results:\n"
        prompt += f"**Status**: {test_status}\n"
        if qa_notes:
            prompt += f"**QA Notes**:\n{qa_notes[:500]}\n"
        
        prompt += f"\n## Risk Assessment:\n"
        prompt += f"**Risk Level**: {risk_level}\n"
        
        if retry_count > 0:
            prompt += f"\n**Development Iterations**: {retry_count} (code was refined based on QA feedback)\n"
        
        prompt += """
## Your Task:

Generate a comprehensive, professional pull request description.

**Output Format**:

```
### PR TITLE:
[Concise title starting with ticket ID]

### DESCRIPTION:

## 📋 Summary
[Brief overview of what this PR does]

## 🎯 Changes Made
- [Change 1]
- [Change 2]
- [Change 3]

## ✅ Testing
[Test status and coverage]

## 🔍 Review Focus
[What reviewers should pay attention to]

## 📝 Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes

### LABELS:
[Comma-separated labels: feature, bugfix, enhancement, etc.]

### REVIEWERS:
[Suggested reviewers based on code changes]
```

**Requirements**:
1. Title must be clear and concise (max 72 chars)
2. Description must be comprehensive but readable
3. Include all functional requirements implemented
4. Mention test status clearly
5. Add appropriate labels
6. Suggest relevant reviewers
7. Use professional tone
8. Include emojis for readability
"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Returns system prompt for PR agent."""
        return """You are an expert DevOps/Git workflow AI agent.

Your responsibilities:
1. Generate professional PR descriptions
2. Summarize code changes clearly
3. Highlight important review points
4. Suggest appropriate labels
5. Recommend reviewers
6. Create actionable checklists

Rules:
- Be concise but comprehensive
- Use clear, professional language
- Highlight risks and important changes
- Make descriptions scannable (use bullets, headers)
- Include test results prominently
- Suggest relevant reviewers based on code area
- Use appropriate labels (feature, bugfix, enhancement, etc.)
- Keep title under 72 characters
"""
    
    # ─────────────────────────────────────────
    # Response Parsing
    # ─────────────────────────────────────────
    
    def _parse_pr_response(
        self,
        response: str,
        ticket_id: str,
        summary: str,
    ) -> PRResult:
        """Parses LLM PR response."""
        
        try:
            pr_title = ""
            pr_description = ""
            pr_labels = []
            reviewers = []
            
            # Extract PR title
            if "### PR TITLE:" in response:
                title_section = response.split("### PR TITLE:")[1].split("###")[0]
                pr_title = title_section.strip().split("\n")[0].strip()
            
            # Extract description
            if "### DESCRIPTION:" in response:
                desc_section = response.split("### DESCRIPTION:")[1]
                # Get everything until LABELS or REVIEWERS
                if "### LABELS:" in desc_section:
                    pr_description = desc_section.split("### LABELS:")[0].strip()
                elif "### REVIEWERS:" in desc_section:
                    pr_description = desc_section.split("### REVIEWERS:")[0].strip()
                else:
                    pr_description = desc_section.strip()
            
            # Extract labels
            if "### LABELS:" in response:
                labels_section = response.split("### LABELS:")[1].split("###")[0]
                labels_text = labels_section.strip()
                pr_labels = [l.strip() for l in labels_text.split(",") if l.strip()]
            
            # Extract reviewers
            if "### REVIEWERS:" in response:
                reviewers_section = response.split("### REVIEWERS:")[1].strip()
                reviewers = [r.strip() for r in reviewers_section.split(",") if r.strip()]
            
            # Fallback title if not found
            if not pr_title:
                pr_title = f"[{ticket_id}] {summary[:50]}"
            
            # Fallback description if not found
            if not pr_description:
                pr_description = f"## Summary\n{summary}\n\nImplements requirements from {ticket_id}."
            
            # Determine if PR is ready
            pr_ready = len(pr_title) > 0 and len(pr_description) > 0
            
            return PRResult(
                success=True,
                pr_title=pr_title,
                pr_description=pr_description,
                pr_labels=pr_labels if pr_labels else ["feature"],
                reviewers_suggested=reviewers if reviewers else ["team-lead"],
                pr_ready=pr_ready,
            )
        
        except Exception as e:
            return PRResult(
                success=False,
                error=f"Failed to parse response: {str(e)}",
            )


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    
    print("\n" + "=" * 70)
    print("  PR AGENT - TEST RUN")
    print("=" * 70)
    
    # Mock data
    requirements = {
        "functional_requirements": [
            "User can register with email and password",
            "System validates email format",
            "Password is hashed with bcrypt",
        ],
        "risk_level": "MEDIUM",
    }
    
    generated_code = {
        "backend/auth/register.py": "...",
        "backend/auth/validators.py": "...",
        "tests/test_register.py": "...",
    }
    
    # Create agent
    agent = PRAgent()
    
    # Generate PR
    print("\n[TEST] Generating PR for registration feature...")
    result = agent.generate_pr(
        ticket_id="TEST-1",
        summary="Add user registration endpoint",
        requirements=requirements,
        generated_code=generated_code,
        test_status="PASSED",
        qa_notes="All tests passed. Code quality: 85/100",
        retry_count=1,
    )
    
    # Display results
    print(f"\n[RESULT] Success: {result.success}")
    if result.success:
        print(f"[RESULT] PR Title: {result.pr_title}")
        print(f"[RESULT] Labels: {', '.join(result.pr_labels)}")
        print(f"[RESULT] Reviewers: {', '.join(result.reviewers_suggested)}")
        print(f"[RESULT] PR Ready: {result.pr_ready}")
        print(f"\n[RESULT] Description Preview:")
        print(f"{result.pr_description[:300]}...")
    else:
        print(f"[RESULT] Error: {result.error}")
    
    print("\n" + "=" * 70)
    print("  [DONE] PR agent test complete")
    print("=" * 70 + "\n")
