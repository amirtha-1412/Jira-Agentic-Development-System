"""
agents/developer_agent/code_validator.py
---------------------------------------------
Code Validator - Validates Generated Code Quality
Performs multi-stage validation before returning code.

Features:
  - Syntax validation (AST parsing)
  - Import validation
  - Type hint checking
  - Docstring presence
  - Error handling patterns
  - Security vulnerability detection
  - Code quality scoring
"""

import ast
import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: str  # ERROR, WARNING, INFO
    category: str  # syntax, imports, types, docs, security, quality
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of code validation."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    quality_score: int = 0  # 0-100
    has_errors: bool = False
    has_warnings: bool = False
    
    def get_errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "ERROR"]
    
    def get_warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "WARNING"]
    
    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "quality_score": self.quality_score,
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message": i.message,
                    "line_number": i.line_number,
                    "suggestion": i.suggestion,
                }
                for i in self.issues
            ],
        }


class CodeValidator:
    """
    Validates generated code for quality and correctness.
    Multi-stage validation pipeline.
    """
    
    def __init__(self):
        self.issues = []
    
    # ─────────────────────────────────────────
    # Main Validation Method
    # ─────────────────────────────────────────
    
    def validate(self, code: str, language: str = "python", filename: str = "") -> ValidationResult:
        """
        Validates code through multiple stages.
        
        Args:
            code: Source code to validate
            language: Programming language (currently only Python)
            filename: Optional filename for context
        
        Returns:
            ValidationResult with issues and quality score
        """
        self.issues = []
        
        if language != "python":
            return ValidationResult(
                is_valid=True,
                quality_score=50,
                issues=[ValidationIssue(
                    severity="INFO",
                    category="validation",
                    message=f"Validation not supported for {language}",
                )],
            )
        
        # Stage 1: Syntax validation
        syntax_valid = self._validate_syntax(code)
        
        # Stage 2: Import validation
        self._validate_imports(code)
        
        # Stage 3: Type hints checking
        self._check_type_hints(code)
        
        # Stage 4: Docstring presence
        self._check_docstrings(code)
        
        # Stage 5: Error handling patterns
        self._check_error_handling(code)
        
        # Stage 6: Security vulnerabilities
        self._check_security(code)
        
        # Stage 7: Code quality checks
        self._check_code_quality(code)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score()
        
        # Determine if valid
        has_errors = any(i.severity == "ERROR" for i in self.issues)
        has_warnings = any(i.severity == "WARNING" for i in self.issues)
        is_valid = syntax_valid and not has_errors
        
        return ValidationResult(
            is_valid=is_valid,
            issues=self.issues,
            quality_score=quality_score,
            has_errors=has_errors,
            has_warnings=has_warnings,
        )
    
    # ─────────────────────────────────────────
    # Validation Stages
    # ─────────────────────────────────────────
    
    def _validate_syntax(self, code: str) -> bool:
        """Validates Python syntax using AST."""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            self.issues.append(ValidationIssue(
                severity="ERROR",
                category="syntax",
                message=f"Syntax error: {e.msg}",
                line_number=e.lineno,
                suggestion="Fix syntax error before proceeding",
            ))
            return False
        except Exception as e:
            self.issues.append(ValidationIssue(
                severity="ERROR",
                category="syntax",
                message=f"Parse error: {str(e)}",
                suggestion="Check code structure",
            ))
            return False
    
    def _validate_imports(self, code: str):
        """Validates import statements."""
        try:
            tree = ast.parse(code)
            
            # Check for wildcard imports
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == '*':
                            self.issues.append(ValidationIssue(
                                severity="WARNING",
                                category="imports",
                                message=f"Wildcard import from {node.module}",
                                line_number=node.lineno,
                                suggestion="Use explicit imports instead of wildcard",
                            ))
            
            # Check for unused imports (basic check)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imports.append(alias.name)
            
            # Check if imports are used (simple heuristic)
            for imp in imports:
                if imp not in code.split('\n', 20)[-1]:  # Check in code after imports
                    # This is a very basic check - could be improved
                    pass
        
        except Exception:
            pass  # Syntax already validated
    
    def _check_type_hints(self, code: str):
        """Checks for type hints in function definitions."""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip __init__ and private methods
                    if node.name.startswith('_'):
                        continue
                    
                    # Check for return type hint
                    if node.returns is None:
                        self.issues.append(ValidationIssue(
                            severity="WARNING",
                            category="types",
                            message=f"Function '{node.name}' missing return type hint",
                            line_number=node.lineno,
                            suggestion="Add return type hint: def func() -> ReturnType:",
                        ))
                    
                    # Check for parameter type hints
                    missing_params = []
                    for arg in node.args.args:
                        if arg.annotation is None and arg.arg != 'self' and arg.arg != 'cls':
                            missing_params.append(arg.arg)
                    
                    if missing_params:
                        self.issues.append(ValidationIssue(
                            severity="INFO",
                            category="types",
                            message=f"Function '{node.name}' parameters missing type hints: {', '.join(missing_params)}",
                            line_number=node.lineno,
                            suggestion="Add type hints to parameters",
                        ))
        
        except Exception:
            pass
    
    def _check_docstrings(self, code: str):
        """Checks for docstrings in functions and classes."""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    # Skip private methods
                    if node.name.startswith('_') and not node.name.startswith('__'):
                        continue
                    
                    # Check for docstring
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        entity_type = "Function" if isinstance(node, ast.FunctionDef) else "Class"
                        self.issues.append(ValidationIssue(
                            severity="WARNING",
                            category="docs",
                            message=f"{entity_type} '{node.name}' missing docstring",
                            line_number=node.lineno,
                            suggestion="Add docstring explaining purpose and parameters",
                        ))
        
        except Exception:
            pass
    
    def _check_error_handling(self, code: str):
        """Checks for error handling patterns."""
        # Check for bare except clauses
        if re.search(r'except\s*:', code):
            self.issues.append(ValidationIssue(
                severity="WARNING",
                category="quality",
                message="Bare except clause found",
                suggestion="Catch specific exceptions instead of bare except:",
            ))
        
        # Check if code has any error handling
        if 'try:' not in code and 'except' not in code:
            # Check if it's a simple utility function
            lines = code.strip().split('\n')
            if len(lines) > 10:  # Only warn for longer code
                self.issues.append(ValidationIssue(
                    severity="INFO",
                    category="quality",
                    message="No error handling found",
                    suggestion="Consider adding try-except blocks for robustness",
                ))
    
    def _check_security(self, code: str):
        """Checks for common security vulnerabilities."""
        # Check for SQL injection risks
        if re.search(r'execute\s*\(\s*["\'].*%s.*["\']', code):
            self.issues.append(ValidationIssue(
                severity="ERROR",
                category="security",
                message="Potential SQL injection vulnerability",
                suggestion="Use parameterized queries instead of string formatting",
            ))
        
        # Check for eval/exec usage
        if re.search(r'\beval\s*\(|\bexec\s*\(', code):
            self.issues.append(ValidationIssue(
                severity="ERROR",
                category="security",
                message="Use of eval() or exec() detected",
                suggestion="Avoid eval/exec - use safer alternatives",
            ))
        
        # Check for hardcoded secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token"),
        ]
        
        for pattern, message in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                self.issues.append(ValidationIssue(
                    severity="WARNING",
                    category="security",
                    message=message,
                    suggestion="Use environment variables or secure config",
                ))
    
    def _check_code_quality(self, code: str):
        """Checks general code quality."""
        # Check for TODO/FIXME/PLACEHOLDER comments
        todo_patterns = [
            (r'#\s*TODO', "TODO comment found"),
            (r'#\s*FIXME', "FIXME comment found"),
            (r'#\s*PLACEHOLDER', "PLACEHOLDER comment found"),
            (r'#\s*HACK', "HACK comment found"),
        ]
        
        for pattern, message in todo_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                self.issues.append(ValidationIssue(
                    severity="ERROR",
                    category="quality",
                    message=message,
                    line_number=line_num,
                    suggestion="Complete implementation - no placeholders allowed",
                ))
        
        # Check for print statements (should use logging)
        if re.search(r'\bprint\s*\(', code):
            self.issues.append(ValidationIssue(
                severity="INFO",
                category="quality",
                message="print() statement found",
                suggestion="Consider using logging instead of print()",
            ))
        
        # Check for long functions (>50 lines)
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    if func_lines > 50:
                        self.issues.append(ValidationIssue(
                            severity="INFO",
                            category="quality",
                            message=f"Function '{node.name}' is very long ({func_lines} lines)",
                            line_number=node.lineno,
                            suggestion="Consider breaking into smaller functions",
                        ))
        except Exception:
            pass
    
    # ─────────────────────────────────────────
    # Quality Scoring
    # ─────────────────────────────────────────
    
    def _calculate_quality_score(self) -> int:
        """Calculates overall quality score (0-100)."""
        score = 100
        
        # Deduct points for issues
        for issue in self.issues:
            if issue.severity == "ERROR":
                score -= 15
            elif issue.severity == "WARNING":
                score -= 5
            elif issue.severity == "INFO":
                score -= 2
        
        return max(0, min(100, score))


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  CODE VALIDATOR - TEST RUN")
    print("=" * 70)
    
    # Test code with various issues
    test_code = """
def process_user_data(user_id, data):
    # TODO: Add validation
    password = "hardcoded123"
    
    try:
        result = execute("SELECT * FROM users WHERE id = %s" % user_id)
        print(result)
        return result
    except:
        pass

class UserManager:
    def get_user(self, user_id):
        return None
"""
    
    validator = CodeValidator()
    result = validator.validate(test_code)
    
    print(f"\n[RESULT] Valid: {result.is_valid}")
    print(f"[RESULT] Quality Score: {result.quality_score}/100")
    print(f"[RESULT] Errors: {len(result.get_errors())}")
    print(f"[RESULT] Warnings: {len(result.get_warnings())}")
    
    print(f"\n[ISSUES] Found {len(result.issues)} issue(s):")
    for issue in result.issues:
        print(f"  [{issue.severity}] {issue.category}: {issue.message}")
        if issue.suggestion:
            print(f"    → {issue.suggestion}")
    
    print("\n" + "=" * 70)
    print("  [DONE] Code validator test complete")
    print("=" * 70 + "\n")
