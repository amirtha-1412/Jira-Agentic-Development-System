"""
agents/developer_agent/developer_agent.py
---------------------------------------------
Developer Agent - Real Code Generation
Generates production-ready code based on requirements.

Features:
  - LLM-powered code generation
  - Context-aware synthesis
  - Multiple file support
  - Diff generation
  - Retry with QA feedback
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from agents.llm import call_llm


# ─────────────────────────────────────────────
# Code Generation Result
# ─────────────────────────────────────────────

@dataclass
class CodeGenerationResult:
    """Result of code generation."""
    success: bool
    generated_files: Dict[str, str] = field(default_factory=dict)  # {filename: code}
    code_diff: str = ""
    implementation_notes: str = ""
    error: str = ""
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "generated_files": self.generated_files,
            "code_diff": self.code_diff,
            "implementation_notes": self.implementation_notes,
            "error": self.error,
        }


# ─────────────────────────────────────────────
# Developer Agent
# ─────────────────────────────────────────────

class DeveloperAgent:
    """
    AI-powered code generation agent.
    Generates production-ready code from requirements.
    """
    
    def __init__(self, use_retriever: bool = True):
        self.use_retriever = use_retriever
        self._retriever = None
    
    def _get_retriever(self):
        """Lazy load retriever."""
        if self._retriever is None and self.use_retriever:
            try:
                from vectorstore.retriever import CodeRetriever
                self._retriever = CodeRetriever()
            except Exception:
                self._retriever = None
        return self._retriever
    
    # ─────────────────────────────────────────
    # Main Generation Method
    # ─────────────────────────────────────────
    
    def generate_code(
        self,
        ticket_id: str,
        requirements: dict,
        qa_feedback: Optional[str] = None,
        retry_count: int = 0,
    ) -> CodeGenerationResult:
        """
        Generates code based on requirements.
        
        Args:
            ticket_id: Jira ticket ID
            requirements: Structured requirements from analyst
            qa_feedback: Optional feedback from QA agent (on retry)
            retry_count: Current retry attempt number
        
        Returns:
            CodeGenerationResult with generated code
        """
        try:
            # Extract requirements
            functional_reqs = requirements.get("functional_requirements", [])
            technical_reqs = requirements.get("technical_requirements", [])
            implementation_steps = requirements.get("implementation_steps", [])
            affected_files = requirements.get("affected_files", [])
            
            # Get code context from retriever
            code_context = self._get_code_context(functional_reqs, affected_files)
            
            # Build prompt
            prompt = self._build_code_generation_prompt(
                ticket_id=ticket_id,
                functional_reqs=functional_reqs,
                technical_reqs=technical_reqs,
                implementation_steps=implementation_steps,
                affected_files=affected_files,
                code_context=code_context,
                qa_feedback=qa_feedback,
                retry_count=retry_count,
            )
            
            # Generate code with LLM
            print(f"  [DevAgent] Generating code for {ticket_id}...")
            if retry_count > 0:
                print(f"  [DevAgent] Retry attempt #{retry_count} with QA feedback")
            
            response = call_llm(
                user_prompt=prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.3,  # Lower for more deterministic code
            )
            
            # Parse response
            result = self._parse_code_response(response, ticket_id)
            
            if result.success:
                print(f"  [DevAgent] ✅ Generated {len(result.generated_files)} file(s)")
            else:
                print(f"  [DevAgent] ❌ Generation failed: {result.error}")
            
            return result
        
        except Exception as e:
            print(f"  [DevAgent] ❌ Exception: {e}")
            return CodeGenerationResult(
                success=False,
                error=str(e),
            )
    
    # ─────────────────────────────────────────
    # Code Context Retrieval
    # ─────────────────────────────────────────
    
    def _get_code_context(
        self,
        functional_reqs: List[str],
        affected_files: List[str],
    ) -> str:
        """Retrieves relevant code context from vector store."""
        if not self.use_retriever:
            return ""
        
        retriever = self._get_retriever()
        if not retriever or not retriever.is_ready():
            return ""
        
        try:
            # Build query from requirements
            query = " ".join(functional_reqs[:3])
            
            # Search for relevant code
            results = retriever.search(query, top_k=3, min_sim=0.25)
            
            if not results:
                return ""
            
            # Format context
            context = "# Relevant Existing Code:\n\n"
            for r in results:
                context += f"## {r.source_path}\n"
                context += f"```{r.extension.lstrip('.')}\n"
                context += f"{r.content[:500]}...\n"
                context += "```\n\n"
            
            return context
        
        except Exception:
            return ""
    
    # ─────────────────────────────────────────
    # Prompt Building
    # ─────────────────────────────────────────
    
    def _build_code_generation_prompt(
        self,
        ticket_id: str,
        functional_reqs: List[str],
        technical_reqs: List[str],
        implementation_steps: List[str],
        affected_files: List[str],
        code_context: str,
        qa_feedback: Optional[str],
        retry_count: int,
    ) -> str:
        """Builds the code generation prompt."""
        
        prompt = f"""# Code Generation Task

## Ticket: {ticket_id}

## Functional Requirements:
"""
        for i, req in enumerate(functional_reqs, 1):
            prompt += f"{i}. {req}\n"
        
        prompt += "\n## Technical Requirements:\n"
        for i, req in enumerate(technical_reqs, 1):
            prompt += f"{i}. {req}\n"
        
        prompt += "\n## Implementation Steps:\n"
        for i, step in enumerate(implementation_steps, 1):
            prompt += f"{i}. {step}\n"
        
        if affected_files:
            prompt += "\n## Affected Files:\n"
            for f in affected_files:
                prompt += f"- {f}\n"
        
        if code_context:
            prompt += f"\n{code_context}\n"
        
        if qa_feedback and retry_count > 0:
            prompt += f"""
## QA Feedback (Retry #{retry_count}):
{qa_feedback}

**IMPORTANT**: Address all QA feedback issues in this iteration.
"""
        
        prompt += """
## Your Task:

Generate production-ready code that implements ALL functional requirements.

**Output Format**:

```
### FILE: <filename>
```<language>
<complete code>
```

### FILE: <another_filename>
```<language>
<complete code>
```

### IMPLEMENTATION NOTES:
<brief notes about the implementation>
```

**Requirements**:
1. Generate COMPLETE, working code (no placeholders)
2. Include proper error handling
3. Add docstrings and comments
4. Follow best practices
5. Make code production-ready
6. Address ALL functional requirements
"""
        
        if retry_count > 0:
            prompt += "\n7. **FIX ALL ISSUES from QA feedback**\n"
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Returns system prompt for developer agent."""
        return """You are an expert software developer AI agent.

Your responsibilities:
1. Generate production-ready, working code
2. Follow best practices and design patterns
3. Write clean, maintainable code
4. Include proper error handling
5. Add comprehensive docstrings
6. Make code testable and modular

Rules:
- Generate COMPLETE code (no TODO or placeholder comments)
- Use proper typing and type hints
- Follow language-specific conventions
- Write defensive code with validation
- Keep functions focused and single-purpose
- Use meaningful variable names
"""
    
    # ─────────────────────────────────────────
    # Response Parsing
    # ─────────────────────────────────────────
    
    def _parse_code_response(
        self,
        response: str,
        ticket_id: str,
    ) -> CodeGenerationResult:
        """Parses LLM response into structured result."""
        
        try:
            generated_files = {}
            implementation_notes = ""
            
            # Split by FILE markers
            parts = response.split("### FILE:")
            
            for part in parts[1:]:  # Skip first empty part
                lines = part.strip().split("\n")
                if not lines:
                    continue
                
                # Extract filename
                filename = lines[0].strip()
                
                # Extract code block
                code_lines = []
                in_code_block = False
                
                for line in lines[1:]:
                    if line.strip().startswith("```") and not in_code_block:
                        in_code_block = True
                        continue
                    elif line.strip().startswith("```") and in_code_block:
                        in_code_block = False
                        break
                    elif in_code_block:
                        code_lines.append(line)
                
                if code_lines:
                    code = "\n".join(code_lines)
                    generated_files[filename] = code
            
            # Extract implementation notes
            if "### IMPLEMENTATION NOTES:" in response:
                notes_part = response.split("### IMPLEMENTATION NOTES:")[1]
                implementation_notes = notes_part.strip()
            
            # Generate diff
            code_diff = self._generate_diff(generated_files)
            
            if not generated_files:
                return CodeGenerationResult(
                    success=False,
                    error="No code files generated in response",
                )
            
            return CodeGenerationResult(
                success=True,
                generated_files=generated_files,
                code_diff=code_diff,
                implementation_notes=implementation_notes,
            )
        
        except Exception as e:
            return CodeGenerationResult(
                success=False,
                error=f"Failed to parse response: {str(e)}",
            )
    
    def _generate_diff(self, generated_files: Dict[str, str]) -> str:
        """Generates a unified diff string."""
        diff = "# Code Changes\n\n"
        
        for filename, code in generated_files.items():
            diff += f"## {filename}\n"
            diff += f"```\n{code[:500]}...\n```\n\n"
        
        return diff


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    
    print("\n" + "=" * 70)
    print("  DEVELOPER AGENT - TEST RUN")
    print("=" * 70)
    
    # Mock requirements
    requirements = {
        "functional_requirements": [
            "User can login with email and password",
            "System validates credentials against database",
            "Return JWT token on successful login",
        ],
        "technical_requirements": [
            "Use FastAPI for REST endpoint",
            "Use bcrypt for password hashing",
            "JWT token expires in 24 hours",
        ],
        "implementation_steps": [
            "Create login endpoint",
            "Validate user credentials",
            "Generate JWT token",
            "Return token in response",
        ],
        "affected_files": [
            "backend/auth/login.py",
            "backend/auth/jwt_utils.py",
        ],
    }
    
    # Create agent
    agent = DeveloperAgent(use_retriever=False)
    
    # Generate code
    print("\n[TEST] Generating code for login feature...")
    result = agent.generate_code(
        ticket_id="TEST-1",
        requirements=requirements,
    )
    
    # Display results
    print(f"\n[RESULT] Success: {result.success}")
    if result.success:
        print(f"[RESULT] Generated {len(result.generated_files)} file(s):")
        for filename in result.generated_files.keys():
            print(f"  - {filename}")
        print(f"\n[RESULT] Implementation Notes:")
        print(f"  {result.implementation_notes[:200]}...")
    else:
        print(f"[RESULT] Error: {result.error}")
    
    print("\n" + "=" * 70)
    print("  [DONE] Developer agent test complete")
    print("=" * 70 + "\n")
