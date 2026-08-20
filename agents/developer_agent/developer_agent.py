"""
agents/developer_agent/developer_agent.py
---------------------------------------------
Developer Agent - Intelligent Code Modification
Generates production-ready code based on requirements.

Features:
  - LLM-powered code generation
  - Repository-aware file modification
  - Semantic code understanding
  - Context-aware synthesis
  - Multiple file support
  - Diff generation
  - Retry with QA feedback
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from agents.llm import call_llm, CODE_MAX_TOKENS
from agents.developer_agent.repository_analyzer import RepositoryAnalyzer
from agents.developer_agent.code_validator import CodeValidator
from agents.developer_agent.enhanced_prompts import EnhancedPromptBuilder


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
    
    def __init__(self, use_retriever: bool = True, repo_path: str = ".", use_memory: bool = True):
        self.use_retriever = use_retriever
        self.repo_path = repo_path
        self.use_memory = use_memory
        self._retriever = None
        self._repo_analyzer = None
        self._memory = None
        self._validator = CodeValidator()
        self._prompt_builder = EnhancedPromptBuilder(repo_path)
    
    def _get_retriever(self):
        """Lazy load retriever."""
        if self._retriever is None and self.use_retriever:
            try:
                from vectorstore.retriever import CodeRetriever
                self._retriever = CodeRetriever()
            except Exception:
                self._retriever = None
        return self._retriever
    
    def _get_repo_analyzer(self):
        """Lazy load repository analyzer."""
        if self._repo_analyzer is None:
            self._repo_analyzer = RepositoryAnalyzer(self.repo_path)
        return self._repo_analyzer
    
    def _get_memory(self):
        """Lazy load agent memory."""
        if self._memory is None and self.use_memory:
            try:
                from agents.memory.agent_memory import AgentMemory
                self._memory = AgentMemory()
            except Exception as e:
                print(f"  [DevAgent] [WARN] Memory system unavailable: {e}")
                self._memory = None
        return self._memory
    
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
        Intelligently modifies existing files instead of creating new ones.
        
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
            
            # Find existing files to modify
            repo_analyzer = self._get_repo_analyzer()
            files_to_modify = repo_analyzer.find_files_to_modify(
                requirements=functional_reqs,
                max_files=3,
            )
            
            # Get existing file contents
            existing_files = self._read_existing_files(files_to_modify)
            
            # Get code context from retriever
            code_context = self._get_code_context(functional_reqs, affected_files)
            
            # Get memory context (similar PRs, patterns, styles)
            memory_context = self._get_memory_context(ticket_id, files_to_modify)
            
            # Build prompt with repository awareness and memory
            prompt = self._prompt_builder.build_code_generation_prompt(
                ticket_id=ticket_id,
                functional_reqs=functional_reqs,
                technical_reqs=technical_reqs,
                implementation_steps=implementation_steps,
                files_to_modify=files_to_modify,
                existing_files=existing_files,
                code_context=code_context,
                memory_context=memory_context,
                qa_feedback=qa_feedback,
                retry_count=retry_count,
            )
            
            # Generate code with LLM
            print(f"  [DevAgent] Generating code for {ticket_id}...")
            if retry_count > 0:
                print(f"  [DevAgent] Retry attempt #{retry_count} with QA feedback")
            
            if files_to_modify:
                print(f"  [DevAgent] Modifying {len(files_to_modify)} existing file(s)")
            
            response = call_llm(
                user_prompt=prompt,
                system_prompt=self._get_intelligent_system_prompt(),
                temperature=0.3,
                max_tokens=CODE_MAX_TOKENS,
            )
            
            # Parse response
            result = self._parse_code_response(response, ticket_id)
            
            # Validate generated code
            if result.success:
                print(f"  [DevAgent] [OK] Generated {len(result.generated_files)} file(s)")
                print(f"  [DevAgent] [SEARCH] Validating code quality...")
                
                validation_passed = True
                for filename, code in result.generated_files.items():
                    validation_result = self._validator.validate(code, language="python", filename=filename)
                    
                    print(f"  [DevAgent] Validation for {filename}:")
                    print(f"    - Valid: {validation_result.is_valid}")
                    print(f"    - Quality Score: {validation_result.quality_score}/100")
                    print(f"    - Errors: {len(validation_result.get_errors())}")
                    print(f"    - Warnings: {len(validation_result.get_warnings())}")
                    
                    if not validation_result.is_valid:
                        validation_passed = False
                        print(f"  [DevAgent] [FAIL] Validation failed for {filename}")
                        for issue in validation_result.get_errors()[:3]:
                            print(f"    - {issue.message}")
                    elif validation_result.quality_score < 60:
                        print(f"  [DevAgent] [WARN]  Low quality score for {filename}")
                
                if not validation_passed:
                    print(f"  [DevAgent] [WARN]  Code validation failed, but returning for QA review")
            else:
                print(f"  [DevAgent] [FAIL] Generation failed: {result.error}")
            
            return result
        
        except Exception as e:
            print(f"  [DevAgent] [ERROR] Exception: {e}")
            return CodeGenerationResult(
                success=False,
                error=str(e),
            )
    
    # ─────────────────────────────────────────
    # Repository Intelligence
    # ─────────────────────────────────────────
    
    def _read_existing_files(self, files_to_modify: List) -> Dict[str, str]:
        """Reads content of existing files to modify."""
        existing_files = {}
        
        for file_analysis in files_to_modify:
            try:
                with open(file_analysis.filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    existing_files[file_analysis.filepath] = content
            except Exception as e:
                print(f"  [DevAgent] [WARN] Could not read {file_analysis.filepath}: {e}")
        
        return existing_files
    
    def _get_memory_context(self, ticket_id: str, files_to_modify: List) -> str:
        """Gets relevant context from agent memory."""
        memory = self._get_memory()
        if not memory:
            return ""
        
        try:
            context = "## 💡 Memory\n\n"
            
            # Get similar PRs (limit to 2)
            similar_prs = memory.get_similar_prs(ticket_id, max_results=2)
            if similar_prs:
                context += "**Similar PRs**: "
                context += ", ".join([f"{pr.ticket_id}({pr.quality_score})" for pr in similar_prs])
                context += "\n\n"
            
            # Get high-confidence patterns (limit to 2)
            patterns = memory.get_high_confidence_patterns(min_confidence=0.7)
            if patterns:
                context += "**Patterns**: "
                context += ", ".join([p.pattern_type for p in patterns[:2]])
                context += "\n\n"
            
            return context if len(context) > 20 else ""
        
        except Exception as e:
            return ""
    
    def _build_intelligent_prompt(
        self,
        ticket_id: str,
        functional_reqs: List[str],
        technical_reqs: List[str],
        implementation_steps: List[str],
        files_to_modify: List,
        existing_files: Dict[str, str],
        code_context: str,
        memory_context: str,
        qa_feedback: Optional[str],
        retry_count: int,
    ) -> str:
        """Builds intelligent prompt with repository awareness."""
        
        prompt = f"""# Intelligent Code Modification Task

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
        
        # Add existing files to modify
        if files_to_modify:
            prompt += "\n## Existing Files to Modify:\n\n"
            prompt += "**IMPORTANT**: Modify these existing files instead of creating new ones.\n\n"
            
            for file_analysis in files_to_modify:
                prompt += f"### File: {file_analysis.filepath}\n"
                prompt += f"**Type**: {file_analysis.file_type}\n"
                prompt += f"**Reason**: {file_analysis.modification_reason}\n"
                prompt += f"**Patterns**: {', '.join(file_analysis.patterns)}\n"
                
                # Show existing content — increased to 3000 chars for full context
                if file_analysis.filepath in existing_files:
                    content = existing_files[file_analysis.filepath]
                    prompt += f"\n**Current Content**:\n```python\n{content[:3000]}\n```\n\n"
        
        if code_context:
            prompt += f"\n{code_context}\n"
        
        if memory_context:
            prompt += f"\n{memory_context}\n"
        
        if qa_feedback and retry_count > 0:
            prompt += f"""
## QA Feedback (Retry #{retry_count}):
{qa_feedback}

**IMPORTANT**: Address all QA feedback issues in this iteration.
"""
        
        prompt += """
## Your Task:

Implement ALL functional requirements by generating or modifying code.

If existing files are provided above, MODIFY them. Otherwise, create a new
standalone Python module for this feature.

**Critical Instructions**:
1. **Preserve existing functionality** - only add/modify what's needed
2. **Maintain code style** - match the existing code patterns if modifying
3. **Add to existing routes/functions** - don't replace everything
4. **Keep imports and structure** - integrate smoothly
5. **If creating new files** - use clean module structure

**Output Format** (use EXACTLY this format, one block per file):

### FILE: <filepath>
```python
<complete file content here>
```

### FILE: <another_filepath>
```python
<complete file content here>
```

### IMPLEMENTATION NOTES:
<brief notes about what was done>

**Requirements**:
1. Output COMPLETE file content (not just changes)
2. Preserve existing code that's not related to requirements
3. Add new functionality seamlessly
4. Include proper error handling
5. Add docstrings for new functions
6. Follow existing code patterns
"""
        
        if retry_count > 0:
            prompt += "\n7. **FIX ALL ISSUES from QA feedback**\n"
        
        return prompt
    
    def _get_intelligent_system_prompt(self) -> str:
        """Returns enhanced system prompt for intelligent modification."""
        return """You are an expert software developer AI agent with repository intelligence.

Your responsibilities:
1. **Modify existing files intelligently** - don't create isolated new files
2. **Understand existing code patterns** - match the style and structure
3. **Preserve existing functionality** - only add/modify what's needed
4. **Integrate seamlessly** - make changes feel natural
5. **Follow best practices** - maintain code quality

Critical Rules:
- **NEVER create new files when existing files can be modified**
- **ALWAYS preserve unrelated existing code**
- **MATCH the existing code style and patterns**
- **ADD to existing routes/functions, don't replace**
- **KEEP existing imports and structure**
- **OUTPUT complete file content, not just diffs**

Code Quality:
- Generate COMPLETE, working code
- Use proper typing and type hints
- Follow language-specific conventions
- Write defensive code with validation
- Keep functions focused and single-purpose
- Use meaningful variable names
- Add comprehensive docstrings for new code
"""
    
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
            
            # Format context — MINIMAL: only 150 chars per chunk to stay under token limit
            context = "## 📚 Code Examples\n\n"
            for r in results:
                context += f"**{r.source_path}**: {r.content[:150]}...\n\n"
            
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
        """
        Robust parser for LLM code response.
        Handles multiple delimiter variations the LLM might use:
          ### FILE: path   (preferred)
          ## FILE: path
          **FILE:** path
        Collects ALL code blocks per file section (not just the first).
        Sanitizes filenames by stripping trailing LLM commentary.
        """
        import re

        try:
            generated_files: Dict[str, str] = {}
            implementation_notes = ""

            # ── Normalise delimiters ──────────────────────
            # Map all FILE: variants to the canonical ### FILE: form
            normalised = re.sub(
                r'(?m)^(?:#{1,4}\s*|\*{2})FILE:\*{0,2}\s*',
                '### FILE: ',
                response,
            )

            # ── Split on canonical delimiter ──────────────
            parts = normalised.split("### FILE:")

            for part in parts[1:]:  # skip text before first FILE marker
                lines = part.split("\n")
                if not lines:
                    continue

                # ── Extract & sanitize filename ───────────
                raw_filename = lines[0].strip()
                # Remove trailing commentary, leading asterisks/backticks
                # e.g. "backend/auth.py  # new file" -> "backend/auth.py"
                # e.g. "** backend/routes.py"         -> "backend/routes.py"
                filename = re.split(r'\s+[#(]', raw_filename)[0].strip().strip('`').lstrip('* ').strip()
                if not filename:
                    continue

                # ── Collect ALL code blocks for this section ──
                all_code_lines: List[str] = []
                in_block = False
                block_lines: List[str] = []

                for line in lines[1:]:
                    stripped = line.strip()
                    if stripped.startswith("```") and not in_block:
                        in_block = True
                        continue  # skip opening fence
                    elif stripped.startswith("```") and in_block:
                        in_block = False
                        all_code_lines.extend(block_lines)
                        all_code_lines.append("")  # blank line between blocks
                        block_lines = []
                        # Do NOT break — collect subsequent blocks too
                        continue
                    elif in_block:
                        block_lines.append(line)

                # Flush any unclosed block
                if block_lines:
                    all_code_lines.extend(block_lines)

                code = "\n".join(all_code_lines).strip()
                if code:
                    generated_files[filename] = code

            # ── Implementation notes ──────────────────────
            for marker in ("### IMPLEMENTATION NOTES:", "## IMPLEMENTATION NOTES:", "IMPLEMENTATION NOTES:"):
                if marker in response:
                    implementation_notes = response.split(marker)[1].strip()
                    break

            # ── Diagnostics on failure ────────────────────
            if not generated_files:
                snippet = response[:400].replace('\n', ' ')
                print(f"  [DevAgent] [WARN] Parser found 0 files. Response excerpt: {snippet}")
                return CodeGenerationResult(
                    success=False,
                    error="No code files extracted — LLM may not have followed the output format.",
                )

            code_diff = self._generate_diff(generated_files)

            print(f"  [DevAgent] [OK] Parser extracted {len(generated_files)} file(s): {list(generated_files.keys())}")
            return CodeGenerationResult(
                success=True,
                generated_files=generated_files,
                code_diff=code_diff,
                implementation_notes=implementation_notes,
            )

        except Exception as e:
            return CodeGenerationResult(
                success=False,
                error=f"Parser exception: {str(e)}",
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
