"""
agents/qa_agent/qa_agent.py
---------------------------------------------
QA Agent - Real Test Generation & Validation
Generates test cases and validates code quality.

Features:
  - LLM-powered test generation
  - Code quality analysis
  - Security vulnerability detection
  - Test case validation
  - Detailed feedback for developers
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from agents.llm import call_llm


# ─────────────────────────────────────────────
# QA Result
# ─────────────────────────────────────────────

@dataclass
class QAResult:
    """Result of QA validation."""
    success: bool
    test_status: str  # PASSED, FAILED, PARTIAL
    test_cases: List[str] = field(default_factory=list)
    test_results: Dict[str, str] = field(default_factory=dict)  # {test: status}
    issues_found: List[str] = field(default_factory=list)
    security_concerns: List[str] = field(default_factory=list)
    quality_score: int = 0  # 0-100
    feedback: str = ""
    error: str = ""
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "test_status": self.test_status,
            "test_cases": self.test_cases,
            "test_results": self.test_results,
            "issues_found": self.issues_found,
            "security_concerns": self.security_concerns,
            "quality_score": self.quality_score,
            "feedback": self.feedback,
            "error": self.error,
        }


# ─────────────────────────────────────────────
# QA Agent
# ─────────────────────────────────────────────

class QAAgent:
    """
    AI-powered QA validation agent.
    Generates tests and validates code quality.
    """
    
    def __init__(self):
        pass
    
    # ─────────────────────────────────────────
    # Main Validation Method
    # ─────────────────────────────────────────
    
    def validate_code(
        self,
        ticket_id: str,
        requirements: dict,
        generated_code: Dict[str, str],
        retry_count: int = 0,
    ) -> QAResult:
        """
        Validates generated code and creates test cases.
        
        Args:
            ticket_id: Jira ticket ID
            requirements: Functional requirements
            generated_code: Generated code files {filename: code}
            retry_count: Current retry attempt
        
        Returns:
            QAResult with validation results
        """
        try:
            functional_reqs = requirements.get("functional_requirements", [])
            edge_cases = requirements.get("edge_cases", "")
            
            # Build validation prompt
            prompt = self._build_validation_prompt(
                ticket_id=ticket_id,
                functional_reqs=functional_reqs,
                generated_code=generated_code,
                edge_cases=edge_cases,
                retry_count=retry_count,
            )
            
            # Run validation with LLM
            print(f"  [QAAgent] Validating code for {ticket_id}...")
            if retry_count > 0:
                print(f"  [QAAgent] Re-validation attempt #{retry_count}")
            
            response = call_llm(
                user_prompt=prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.2,  # Lower for consistent validation
            )
            
            # Parse response
            result = self._parse_validation_response(response, ticket_id)
            
            if result.success:
                print(f"  [QAAgent] ✅ Validation complete: {result.test_status}")
                print(f"  [QAAgent] Quality Score: {result.quality_score}/100")
                print(f"  [QAAgent] Test Cases: {len(result.test_cases)}")
                print(f"  [QAAgent] Issues Found: {len(result.issues_found)}")
            else:
                print(f"  [QAAgent] ❌ Validation failed: {result.error}")
            
            return result
        
        except Exception as e:
            print(f"  [QAAgent] ❌ Exception: {e}")
            return QAResult(
                success=False,
                test_status="ERROR",
                error=str(e),
            )
    
    # ─────────────────────────────────────────
    # Prompt Building
    # ─────────────────────────────────────────
    
    def _build_validation_prompt(
        self,
        ticket_id: str,
        functional_reqs: List[str],
        generated_code: Dict[str, str],
        edge_cases: str,
        retry_count: int,
    ) -> str:
        """Builds the validation prompt."""
        
        prompt = f"""# QA Validation Task

## Ticket: {ticket_id}

## Functional Requirements to Validate:
"""
        for i, req in enumerate(functional_reqs, 1):
            prompt += f"{i}. {req}\n"
        
        prompt += "\n## Generated Code:\n\n"
        for filename, code in generated_code.items():
            prompt += f"### {filename}\n"
            prompt += f"```python\n{code[:1000]}...\n```\n\n"
        
        if edge_cases:
            prompt += f"\n## Edge Cases to Consider:\n{edge_cases}\n"
        
        if retry_count > 0:
            prompt += f"\n**Note**: This is retry attempt #{retry_count}. Previous validation failed.\n"
        
        prompt += """
## Your Task:

Perform comprehensive QA validation of the generated code.

**Output Format**:

```
### TEST CASES:
1. [Test case 1 description]
2. [Test case 2 description]
3. [Test case 3 description]
...

### TEST RESULTS:
- Test 1: PASSED/FAILED - [reason]
- Test 2: PASSED/FAILED - [reason]
- Test 3: PASSED/FAILED - [reason]
...

### ISSUES FOUND:
- [Issue 1 - specific problem]
- [Issue 2 - specific problem]
(or "NONE" if no issues)

### SECURITY CONCERNS:
- [Security concern 1]
- [Security concern 2]
(or "NONE" if no concerns)

### QUALITY SCORE: [0-100]

### OVERALL STATUS: PASSED/FAILED/PARTIAL

### FEEDBACK FOR DEVELOPER:
[Detailed feedback on what needs to be fixed]
```

**Validation Criteria**:
1. All functional requirements implemented
2. Code is complete (no TODOs or placeholders)
3. Proper error handling present
4. Security best practices followed
5. Code is production-ready
6. Edge cases handled
7. Input validation present
8. No obvious bugs or issues
"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Returns system prompt for QA agent."""
        return """You are an expert QA engineer AI agent.

Your responsibilities:
1. Validate code against requirements
2. Generate comprehensive test cases
3. Identify bugs and issues
4. Check security vulnerabilities
5. Assess code quality
6. Provide actionable feedback

Rules:
- Be thorough and critical
- Look for edge cases and error scenarios
- Check for security vulnerabilities (SQL injection, XSS, etc.)
- Validate input handling
- Check error handling
- Assess code completeness
- Provide specific, actionable feedback
- Use PASSED only if ALL requirements are met
- Use FAILED if critical issues exist
- Use PARTIAL if minor issues exist
"""
    
    # ─────────────────────────────────────────
    # Response Parsing
    # ─────────────────────────────────────────
    
    def _parse_validation_response(
        self,
        response: str,
        ticket_id: str,
    ) -> QAResult:
        """Parses LLM validation response."""
        
        try:
            test_cases = []
            test_results = {}
            issues_found = []
            security_concerns = []
            quality_score = 0
            test_status = "UNKNOWN"
            feedback = ""
            
            # Extract test cases
            if "### TEST CASES:" in response:
                test_section = response.split("### TEST CASES:")[1].split("###")[0]
                for line in test_section.strip().split("\n"):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith("-")):
                        # Remove numbering
                        test_case = line.split(".", 1)[-1].strip() if "." in line else line[1:].strip()
                        if test_case:
                            test_cases.append(test_case)
            
            # Extract test results
            if "### TEST RESULTS:" in response:
                results_section = response.split("### TEST RESULTS:")[1].split("###")[0]
                for line in results_section.strip().split("\n"):
                    line = line.strip()
                    if ":" in line and ("PASSED" in line or "FAILED" in line):
                        parts = line.split(":", 1)
                        test_name = parts[0].strip("- ").strip()
                        status = "PASSED" if "PASSED" in parts[1] else "FAILED"
                        test_results[test_name] = status
            
            # Extract issues
            if "### ISSUES FOUND:" in response:
                issues_section = response.split("### ISSUES FOUND:")[1].split("###")[0]
                for line in issues_section.strip().split("\n"):
                    line = line.strip()
                    if line and line.startswith("-") and "NONE" not in line.upper():
                        issue = line[1:].strip()
                        if issue:
                            issues_found.append(issue)
            
            # Extract security concerns
            if "### SECURITY CONCERNS:" in response:
                security_section = response.split("### SECURITY CONCERNS:")[1].split("###")[0]
                for line in security_section.strip().split("\n"):
                    line = line.strip()
                    if line and line.startswith("-") and "NONE" not in line.upper():
                        concern = line[1:].strip()
                        if concern:
                            security_concerns.append(concern)
            
            # Extract quality score
            if "### QUALITY SCORE:" in response:
                score_section = response.split("### QUALITY SCORE:")[1].split("###")[0]
                score_text = score_section.strip().split()[0]
                try:
                    quality_score = int(score_text)
                except:
                    quality_score = 50
            
            # Extract overall status
            if "### OVERALL STATUS:" in response:
                status_section = response.split("### OVERALL STATUS:")[1].split("###")[0]
                status_text = status_section.strip().upper()
                if "PASSED" in status_text:
                    test_status = "PASSED"
                elif "FAILED" in status_text:
                    test_status = "FAILED"
                elif "PARTIAL" in status_text:
                    test_status = "PARTIAL"
            
            # Extract feedback
            if "### FEEDBACK FOR DEVELOPER:" in response:
                feedback = response.split("### FEEDBACK FOR DEVELOPER:")[1].strip()
            
            # Determine success
            success = test_status in ["PASSED", "PARTIAL", "FAILED"]
            
            return QAResult(
                success=success,
                test_status=test_status,
                test_cases=test_cases,
                test_results=test_results,
                issues_found=issues_found,
                security_concerns=security_concerns,
                quality_score=quality_score,
                feedback=feedback,
            )
        
        except Exception as e:
            return QAResult(
                success=False,
                test_status="ERROR",
                error=f"Failed to parse response: {str(e)}",
            )


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    
    print("\n" + "=" * 70)
    print("  QA AGENT - TEST RUN")
    print("=" * 70)
    
    # Mock requirements
    requirements = {
        "functional_requirements": [
            "User can login with email and password",
            "System validates credentials",
            "Return JWT token on success",
        ],
        "edge_cases": "Handle invalid credentials, expired tokens, SQL injection attempts",
    }
    
    # Mock generated code
    generated_code = {
        "backend/auth/login.py": """
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import bcrypt
import jwt

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    # Validate credentials
    user = get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check password
    if not bcrypt.checkpw(request.password.encode(), user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate JWT
    token = jwt.encode({"user_id": user.id}, "secret_key", algorithm="HS256")
    
    return {"token": token, "user_id": user.id}
""",
    }
    
    # Create agent
    agent = QAAgent()
    
    # Validate code
    print("\n[TEST] Validating login code...")
    result = agent.validate_code(
        ticket_id="TEST-1",
        requirements=requirements,
        generated_code=generated_code,
    )
    
    # Display results
    print(f"\n[RESULT] Success: {result.success}")
    print(f"[RESULT] Test Status: {result.test_status}")
    print(f"[RESULT] Quality Score: {result.quality_score}/100")
    print(f"[RESULT] Test Cases: {len(result.test_cases)}")
    print(f"[RESULT] Issues Found: {len(result.issues_found)}")
    
    if result.issues_found:
        print(f"\n[ISSUES]:")
        for issue in result.issues_found[:3]:
            print(f"  - {issue}")
    
    if result.security_concerns:
        print(f"\n[SECURITY]:")
        for concern in result.security_concerns[:3]:
            print(f"  - {concern}")
    
    print(f"\n[FEEDBACK]:")
    print(f"  {result.feedback[:200]}...")
    
    print("\n" + "=" * 70)
    print("  [DONE] QA agent test complete")
    print("=" * 70 + "\n")
