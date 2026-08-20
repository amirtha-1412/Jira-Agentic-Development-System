"""
agents/developer_agent/repository_analyzer.py
---------------------------------------------
Repository Analyzer - Intelligent Code Understanding
Analyzes existing repository structure to find files to modify.

Features:
  - Repository structure analysis
  - Semantic file matching
  - Code pattern recognition
  - Intelligent file selection
"""

import os
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class FileAnalysis:
    """Analysis result for a single file."""
    filepath: str
    file_type: str  # route, model, service, util, test
    patterns: List[str]  # Detected patterns (auth, user, api, etc.)
    functions: List[str]  # Function names found
    classes: List[str]  # Class names found
    imports: List[str]  # Import statements
    relevance_score: float  # 0-1 score for requirement match
    should_modify: bool  # Whether this file should be modified
    modification_reason: str  # Why this file was selected


class RepositoryAnalyzer:
    """
    Analyzes repository structure to intelligently select files for modification.
    """
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.file_cache = {}
    
    # ─────────────────────────────────────────
    # Main Analysis Method
    # ─────────────────────────────────────────
    
    def find_files_to_modify(
        self,
        requirements: List[str],
        ticket_type: str = "feature",
        max_files: int = 5,
    ) -> List[FileAnalysis]:
        """
        Finds existing files that should be modified for the requirements.
        
        Args:
            requirements: List of functional requirements
            ticket_type: Type of ticket (feature, bug, enhancement)
            max_files: Maximum number of files to return
        
        Returns:
            List of FileAnalysis objects for files to modify
        """
        print(f"  [RepoAnalyzer] Analyzing repository for relevant files...")
        
        # Extract keywords from requirements
        keywords = self._extract_keywords(requirements)
        print(f"  [RepoAnalyzer] Keywords: {', '.join(keywords[:5])}")
        
        # Scan repository
        all_files = self._scan_repository()
        print(f"  [RepoAnalyzer] Found {len(all_files)} Python files")
        
        # Analyze each file
        analyzed_files = []
        for filepath in all_files:
            analysis = self._analyze_file(filepath, keywords, requirements)
            if analysis.relevance_score > 0.3:  # Threshold for relevance
                analyzed_files.append(analysis)
        
        # Sort by relevance
        analyzed_files.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Select top files
        selected = analyzed_files[:max_files]
        
        print(f"  [RepoAnalyzer] Selected {len(selected)} file(s) for modification:")
        for f in selected:
            print(f"    - {f.filepath} (score: {f.relevance_score:.2f})")
        
        return selected
    
    # ─────────────────────────────────────────
    # Repository Scanning
    # ─────────────────────────────────────────
    
    def _scan_repository(self) -> List[str]:
        """Scans repository for Python files."""
        python_files = []
        
        # Directories to scan (ONLY backend - exclude agent files to prevent self-modification)
        scan_dirs = ["backend"]
        
        # Files to NEVER modify (core system files)
        excluded_files = [
            "developer_agent.py",
            "qa_agent.py",
            "pr_generator.py",
            "github_agent.py",
            "notification_agent.py",
            "analyzer.py",
            "prompt.py",
            "code_validator.py",
            "enhanced_prompts.py",
            "repository_analyzer.py",
            "llm.py",
            "agent_memory.py",
        ]
        
        for dir_name in scan_dirs:
            dir_path = self.repo_path / dir_name
            if not dir_path.exists():
                continue
            
            for root, dirs, files in os.walk(dir_path):
                # Skip __pycache__ and hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                
                for file in files:
                    # Skip excluded files
                    if file in excluded_files:
                        continue
                    
                    if file.endswith('.py') and not file.startswith('__'):
                        filepath = os.path.join(root, file)
                        python_files.append(filepath)
        
        return python_files
    
    # ─────────────────────────────────────────
    # File Analysis
    # ─────────────────────────────────────────
    
    def _analyze_file(
        self,
        filepath: str,
        keywords: List[str],
        requirements: List[str],
    ) -> FileAnalysis:
        """Analyzes a single file for relevance."""
        
        # Read file content
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return FileAnalysis(
                filepath=filepath,
                file_type="unknown",
                patterns=[],
                functions=[],
                classes=[],
                imports=[],
                relevance_score=0.0,
                should_modify=False,
                modification_reason="",
            )
        
        # Detect file type
        file_type = self._detect_file_type(filepath, content)
        
        # Extract code elements
        functions = self._extract_functions(content)
        classes = self._extract_classes(content)
        imports = self._extract_imports(content)
        patterns = self._detect_patterns(filepath, content)
        
        # Calculate relevance score
        relevance_score = self._calculate_relevance(
            filepath, content, keywords, requirements, patterns
        )
        
        # Determine if should modify
        should_modify = relevance_score > 0.5
        modification_reason = self._get_modification_reason(
            filepath, file_type, patterns, keywords, relevance_score
        )
        
        return FileAnalysis(
            filepath=filepath,
            file_type=file_type,
            patterns=patterns,
            functions=functions,
            classes=classes,
            imports=imports,
            relevance_score=relevance_score,
            should_modify=should_modify,
            modification_reason=modification_reason,
        )
    
    # ─────────────────────────────────────────
    # Pattern Detection
    # ─────────────────────────────────────────
    
    def _detect_file_type(self, filepath: str, content: str) -> str:
        """Detects the type of file."""
        filepath_lower = filepath.lower()
        
        if 'routes' in filepath_lower or 'router' in filepath_lower:
            return "route"
        elif 'model' in filepath_lower or 'schema' in filepath_lower:
            return "model"
        elif 'service' in filepath_lower or 'agent' in filepath_lower:
            return "service"
        elif 'test' in filepath_lower:
            return "test"
        elif 'util' in filepath_lower or 'helper' in filepath_lower:
            return "util"
        elif 'main.py' in filepath_lower:
            return "main"
        else:
            return "module"
    
    def _detect_patterns(self, filepath: str, content: str) -> List[str]:
        """Detects code patterns in the file."""
        patterns = []
        
        content_lower = content.lower()
        filepath_lower = filepath.lower()
        
        # Common patterns
        pattern_keywords = {
            'auth': ['auth', 'login', 'password', 'token', 'jwt'],
            'user': ['user', 'account', 'profile'],
            'api': ['api', 'endpoint', 'route', 'fastapi'],
            'database': ['database', 'db', 'sql', 'query'],
            'email': ['email', 'mail', 'smtp'],
            'file': ['file', 'upload', 'download', 'storage'],
            'payment': ['payment', 'stripe', 'paypal', 'transaction'],
        }
        
        for pattern, keywords in pattern_keywords.items():
            if any(kw in content_lower or kw in filepath_lower for kw in keywords):
                patterns.append(pattern)
        
        return patterns
    
    def _extract_functions(self, content: str) -> List[str]:
        """Extracts function names from code."""
        pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        return re.findall(pattern, content)
    
    def _extract_classes(self, content: str) -> List[str]:
        """Extracts class names from code."""
        pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]'
        return re.findall(pattern, content)
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extracts import statements."""
        pattern = r'(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_.]*)'
        return re.findall(pattern, content)[:10]  # Limit to first 10
    
    # ─────────────────────────────────────────
    # Relevance Scoring
    # ─────────────────────────────────────────
    
    def _calculate_relevance(
        self,
        filepath: str,
        content: str,
        keywords: List[str],
        requirements: List[str],
        patterns: List[str],
    ) -> float:
        """Calculates relevance score (0-1) for a file."""
        score = 0.0
        
        content_lower = content.lower()
        filepath_lower = filepath.lower()
        
        # Keyword matching (40% weight)
        keyword_matches = sum(1 for kw in keywords if kw in content_lower or kw in filepath_lower)
        keyword_score = min(keyword_matches / max(len(keywords), 1), 1.0) * 0.4
        score += keyword_score
        
        # Pattern matching (30% weight)
        pattern_score = len(patterns) / 5.0  # Normalize to 0-1
        score += min(pattern_score, 1.0) * 0.3
        
        # File type relevance (20% weight)
        file_type = self._detect_file_type(filepath, content)
        type_scores = {
            'route': 0.9,
            'service': 0.8,
            'model': 0.7,
            'util': 0.5,
            'main': 0.6,
            'module': 0.4,
            'test': 0.3,
        }
        score += type_scores.get(file_type, 0.3) * 0.2
        
        # Requirement matching (10% weight)
        req_text = " ".join(requirements).lower()
        req_matches = sum(1 for kw in keywords if kw in req_text)
        req_score = min(req_matches / max(len(keywords), 1), 1.0) * 0.1
        score += req_score
        
        return min(score, 1.0)
    
    def _get_modification_reason(
        self,
        filepath: str,
        file_type: str,
        patterns: List[str],
        keywords: List[str],
        score: float,
    ) -> str:
        """Generates explanation for why file should be modified."""
        if score < 0.3:
            return "Low relevance to requirements"
        
        reasons = []
        
        if file_type == "route":
            reasons.append("Contains API routes")
        elif file_type == "service":
            reasons.append("Contains business logic")
        elif file_type == "model":
            reasons.append("Contains data models")
        
        if patterns:
            reasons.append(f"Handles {', '.join(patterns[:2])}")
        
        if not reasons:
            reasons.append("Matches requirement keywords")
        
        return "; ".join(reasons)
    
    # ─────────────────────────────────────────
    # Keyword Extraction
    # ─────────────────────────────────────────
    
    def _extract_keywords(self, requirements: List[str]) -> List[str]:
        """Extracts keywords from requirements."""
        # Common stop words to ignore
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'shall',
        }
        
        keywords = []
        
        for req in requirements:
            # Split into words
            words = re.findall(r'\b[a-zA-Z]{3,}\b', req.lower())
            
            # Filter stop words
            words = [w for w in words if w not in stop_words]
            
            keywords.extend(words)
        
        # Remove duplicates and return
        return list(set(keywords))


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  REPOSITORY ANALYZER - TEST RUN")
    print("=" * 70)
    
    # Create analyzer
    analyzer = RepositoryAnalyzer()
    
    # Test requirements
    requirements = [
        "User can reset password using email verification",
        "System sends password reset token to user email",
        "Token expires after 1 hour",
    ]
    
    # Find files to modify
    print("\n[TEST] Finding files to modify...")
    files = analyzer.find_files_to_modify(requirements, max_files=5)
    
    # Display results
    print(f"\n[RESULT] Found {len(files)} relevant file(s):")
    for f in files:
        print(f"\n  File: {f.filepath}")
        print(f"  Type: {f.file_type}")
        print(f"  Score: {f.relevance_score:.2f}")
        print(f"  Patterns: {', '.join(f.patterns)}")
        print(f"  Reason: {f.modification_reason}")
    
    print("\n" + "=" * 70)
    print("  [DONE] Repository analyzer test complete")
    print("=" * 70 + "\n")
