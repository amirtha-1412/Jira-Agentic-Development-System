"""
agents/developer_agent/enhanced_prompts.py
---------------------------------------------
Enhanced Prompt Engineering for Developer Agent
Provides context-rich, example-driven prompts for better code generation.

Features:
  - Repository pattern extraction
  - Code example inclusion
  - Style guide integration
  - Detailed instructions
  - Quality requirements
"""

from typing import List, Dict, Optional


class EnhancedPromptBuilder:
    """
    Builds enhanced prompts with rich context for accurate code generation.
    """
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
    
    # ─────────────────────────────────────────
    # Main Prompt Building
    # ─────────────────────────────────────────
    
    def build_code_generation_prompt(
        self,
        ticket_id: str,
        functional_reqs: List[str],
        technical_reqs: List[str],
        implementation_steps: List[str],
        files_to_modify: List,
        existing_files: Dict[str, str],
        code_context: str,
        memory_context: str,
        qa_feedback: Optional[str] = None,
        retry_count: int = 0,
    ) -> str:
        """
        Builds comprehensive prompt with all context.
        """
        
        prompt = f"""# 🎯 Intelligent Code Modification Task

## 📋 Ticket Information
**Ticket ID:** {ticket_id}
**Type:** Feature Implementation
**Retry Attempt:** {retry_count}

---

## 🎯 Functional Requirements

"""
        for i, req in enumerate(functional_reqs, 1):
            prompt += f"{i}. **{req}**\n"
        
        prompt += "\n## 🔧 Technical Requirements\n\n"
        for i, req in enumerate(technical_reqs, 1):
            prompt += f"{i}. {req}\n"
        
        prompt += "\n## [PR] Implementation Steps\n\n"
        for i, step in enumerate(implementation_steps, 1):
            prompt += f"{i}. {step}\n"
        
        # Add repository patterns
        prompt += "\n" + self._build_repository_patterns_section()
        
        # Add code quality standards
        prompt += "\n" + self._build_quality_standards_section()
        
        # Add existing files to modify
        if files_to_modify:
            prompt += "\n## 📁 Existing Files to Modify\n\n"
            prompt += "**[WARN] CRITICAL:** Modify these existing files instead of creating new ones.\n\n"
            
            for file_analysis in files_to_modify:
                prompt += f"### 📄 File: `{file_analysis.filepath}`\n\n"
                prompt += f"- **Type:** {file_analysis.file_type}\n"
                prompt += f"- **Reason:** {file_analysis.modification_reason}\n"
                prompt += f"- **Patterns:** {', '.join(file_analysis.patterns)}\n"
                
                # Show existing content with analysis
                if file_analysis.filepath in existing_files:
                    content = existing_files[file_analysis.filepath]
                    # MINIMAL: Only show first 200 chars to stay under token limit
                    prompt += f"\n**Snippet** ({len(content)} chars total):\n"
                    prompt += f"```python\n{content[:200]}\n...\n```\n\n"
        
        # Add code context from vector store (limit to 300 chars)
        if code_context:
            prompt += f"\n## 📚 Code Context\n{code_context[:300]}\n...\n"
        
        # Add memory context (limit to 200 chars)
        if memory_context:
            prompt += f"\n## 💡 Patterns\n{memory_context[:200]}\n...\n"
        
        # Add QA feedback if retry (limit to 200 chars)
        if qa_feedback and retry_count > 0:
            prompt += f"""
---

## ⚠️ QA Feedback (Retry #{retry_count})

{qa_feedback[:200]}...

**Fix ALL issues mentioned above.**

---
"""
        
        # Add output format instructions
        prompt += self._build_output_format_section()
        
        # Add critical instructions
        prompt += self._build_critical_instructions_section(retry_count)
        
        # Add validation checklist
        prompt += self._build_validation_checklist_section()
        
        return prompt
    
    # ─────────────────────────────────────────
    # Section Builders
    # ─────────────────────────────────────────
    
    def _build_repository_patterns_section(self) -> str:
        """Builds section about repository patterns."""
        return """## 🏗️ Repository Patterns

**Error Handling:** Try-except for operations, specific exceptions, log errors
**Logging:** Use print(f"  [Agent] Message") with [OK]/[FAIL]/[WARN]
**Validation:** Check inputs at entry, use type hints
**Imports:** stdlib → 3rd-party → local, grouped by relation
**Docstrings:** Description, Args, Returns, Raises sections
"""
    
    def _build_quality_standards_section(self) -> str:
        """Builds section about code quality standards."""
        return """## ⭐ Quality Standards

**MUST:**
Valid syntax • Complete impl • Type hints • Docstrings • Error handling • Input validation • Clear names • No hardcoded secrets

**MUST NOT:**
Syntax errors • TODO/FIXME • Bare except • Hardcoded keys • SQL injection • eval/exec • Wildcard imports
"""
    
    def _build_output_format_section(self) -> str:
        """Builds section about output format."""
        return """
---

## 📤 Output

```
### FILE: <filepath>
```python
<complete file content>
```

### IMPLEMENTATION NOTES:
<brief changes>
```

Output COMPLETE file content, not just diffs.
"""
    
    def _build_critical_instructions_section(self, retry_count: int) -> str:
        """Builds section with critical instructions."""
        section = """
---

## ⚠️ CRITICAL

**Modify Files:** Don't create new • Preserve existing • Match style • Integrate seamlessly
**Code Quality:** No TODO • No placeholders • No syntax errors • Include error handling • Type hints • Docstrings
**Implementation:** Address ALL reqs • Handle edge cases • Validate inputs • Use existing patterns • Production quality
"""
        
        if retry_count > 0:
            section += """
**RETRY:** Fix ALL QA issues • Don't repeat mistakes • Higher quality
"""
        
        return section
    
    def _build_validation_checklist_section(self) -> str:
        """Builds validation checklist section."""
        return """
---

## ✅ Checklist

Syntax • Complete (no TODO) • Type hints • Docstrings • Error handling • Input validation • Security • Imports • Style • All requirements

---
"""
    
    def _analyze_file_structure(self, content: str) -> str:
        """Analyzes and describes file structure."""
        lines = content.split('\n')
        
        # Count key elements
        imports = len([l for l in lines if l.strip().startswith('import ') or l.strip().startswith('from ')])
        classes = len([l for l in lines if l.strip().startswith('class ')])
        functions = len([l for l in lines if l.strip().startswith('def ')])
        
        analysis = f"**Structure Analysis:**\n"
        analysis += f"- Lines: {len(lines)}\n"
        analysis += f"- Imports: {imports}\n"
        analysis += f"- Classes: {classes}\n"
        analysis += f"- Functions: {functions}\n\n"
        
        return analysis
    
    # ─────────────────────────────────────────
    # System Prompt
    # ─────────────────────────────────────────
    
    def get_enhanced_system_prompt(self) -> str:
        """Returns enhanced system prompt."""
        return """You are an EXPERT SOFTWARE DEVELOPER AI with repository intelligence.

## Core Capabilities
1. Repository Understanding: Analyze patterns, architecture, conventions
2. Intelligent Modification: Modify existing files, preserve functionality, integrate seamlessly
3. Production Quality: Complete implementations, error handling, type hints, docstrings
4. Quality Assurance: Validate syntax, no TODOs, check security, verify requirements

## DO
✅ Complete working code (no placeholders) • Modify existing files • Preserve unrelated code • Match style • Error handling • Docstrings • Type hints • Validate inputs • Security best practices • Address ALL requirements

## DON'T
❌ New files when existing can be modified • TODO/FIXME/PLACEHOLDER • Bare except • Hardcoded secrets • SQL injection • eval/exec • Skip error handling • Forget type hints/docstrings • Syntax errors

## Quality Standards
Every function: Type hints • Docstring • Input validation • Error handling • Clear names
Every file: Valid syntax • All imports • Follow patterns • Production-ready

## Response Format
```
### FILE: <filepath>
```python
<complete file content>
```

### IMPLEMENTATION NOTES:
<what changed and why>
```

Generate production-ready code. Quality, completeness, correctness are paramount.
"""


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  ENHANCED PROMPT BUILDER - TEST RUN")
    print("=" * 70)
    
    builder = EnhancedPromptBuilder()
    
    # Test system prompt
    system_prompt = builder.get_enhanced_system_prompt()
    print(f"\n[SYSTEM PROMPT] Length: {len(system_prompt)} chars")
    print(f"[SYSTEM PROMPT] Preview:\n{system_prompt[:300]}...\n")
    
    # Test quality standards section
    quality_section = builder._build_quality_standards_section()
    print(f"[QUALITY STANDARDS] Length: {len(quality_section)} chars")
    print(f"[QUALITY STANDARDS] Preview:\n{quality_section[:200]}...\n")
    
    print("=" * 70)
    print("  [DONE] Enhanced prompt builder test complete")
    print("=" * 70 + "\n")
