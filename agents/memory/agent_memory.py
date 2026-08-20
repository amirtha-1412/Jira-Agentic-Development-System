"""
agents/memory/agent_memory.py
---------------------------------------------
Agent Memory System - Learning from Experience
Stores and retrieves agent experiences for continuous improvement.

Features:
  - Previous PR tracking
  - Failure pattern recognition
  - Repository pattern learning
  - Coding style memory
  - Success/failure analysis
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


@dataclass
class PRMemory:
    """Memory of a previous PR."""
    ticket_id: str
    pr_number: int
    pr_url: str
    branch_name: str
    files_modified: List[str]
    test_status: str  # PASSED, FAILED, PARTIAL
    quality_score: int
    issues_found: List[str]
    created_at: str
    merged: bool = False
    merge_time: Optional[str] = None
    reviewer_feedback: List[str] = field(default_factory=list)


@dataclass
class FailureMemory:
    """Memory of a past failure."""
    ticket_id: str
    failure_type: str  # test_failure, build_failure, qa_failure, merge_conflict
    error_message: str
    files_involved: List[str]
    resolution: str
    occurred_at: str
    resolved: bool = False


@dataclass
class PatternMemory:
    """Memory of repository patterns."""
    pattern_type: str  # file_structure, naming_convention, import_pattern, etc.
    pattern_description: str
    examples: List[str]
    frequency: int  # How often this pattern appears
    confidence: float  # 0-1 confidence score
    last_seen: str


@dataclass
class StyleMemory:
    """Memory of coding style preferences."""
    language: str  # python, javascript, etc.
    style_rule: str  # max_line_length, indent_style, etc.
    value: str
    source: str  # config_file, observed_pattern, explicit_rule
    confidence: float  # 0-1 confidence score


class AgentMemory:
    """
    Persistent memory system for AI agents.
    Learns from experience and improves over time.
    """
    
    def __init__(self, memory_dir: str = ".agent_memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        # Memory files
        self.pr_memory_file = self.memory_dir / "pr_memory.json"
        self.failure_memory_file = self.memory_dir / "failure_memory.json"
        self.pattern_memory_file = self.memory_dir / "pattern_memory.json"
        self.style_memory_file = self.memory_dir / "style_memory.json"
        
        # Load existing memories
        self.pr_memories: List[PRMemory] = self._load_pr_memories()
        self.failure_memories: List[FailureMemory] = self._load_failure_memories()
        self.pattern_memories: List[PatternMemory] = self._load_pattern_memories()
        self.style_memories: List[StyleMemory] = self._load_style_memories()
    
    # ─────────────────────────────────────────
    # PR Memory Management
    # ─────────────────────────────────────────
    
    def remember_pr(self, pr_memory: PRMemory):
        """Store memory of a PR."""
        self.pr_memories.append(pr_memory)
        self._save_pr_memories()
        print(f"  [Memory] Remembered PR: {pr_memory.pr_url}")
    
    def get_similar_prs(self, ticket_id: str, max_results: int = 5) -> List[PRMemory]:
        """Get similar PRs based on ticket patterns."""
        # Extract ticket prefix (e.g., SCRUM from SCRUM-1)
        prefix = ticket_id.split('-')[0] if '-' in ticket_id else ticket_id
        
        similar = [
            pr for pr in self.pr_memories
            if pr.ticket_id.startswith(prefix)
        ]
        
        # Sort by quality score and recency
        similar.sort(key=lambda x: (x.quality_score, x.created_at), reverse=True)
        
        return similar[:max_results]
    
    def get_successful_prs(self, min_quality: int = 70) -> List[PRMemory]:
        """Get PRs that were successful."""
        return [
            pr for pr in self.pr_memories
            if pr.test_status == "PASSED" and pr.quality_score >= min_quality
        ]
    
    # ─────────────────────────────────────────
    # Failure Memory Management
    # ─────────────────────────────────────────
    
    def remember_failure(self, failure: FailureMemory):
        """Store memory of a failure."""
        self.failure_memories.append(failure)
        self._save_failure_memories()
        print(f"  [Memory] Remembered failure: {failure.failure_type}")
    
    def get_similar_failures(self, error_message: str, max_results: int = 3) -> List[FailureMemory]:
        """Get similar past failures."""
        # Simple keyword matching
        keywords = set(error_message.lower().split())
        
        scored_failures = []
        for failure in self.failure_memories:
            failure_keywords = set(failure.error_message.lower().split())
            overlap = len(keywords & failure_keywords)
            if overlap > 0:
                scored_failures.append((overlap, failure))
        
        # Sort by relevance
        scored_failures.sort(key=lambda x: x[0], reverse=True)
        
        return [f[1] for f in scored_failures[:max_results]]
    
    def get_failure_patterns(self) -> Dict[str, int]:
        """Get common failure patterns."""
        patterns = {}
        for failure in self.failure_memories:
            patterns[failure.failure_type] = patterns.get(failure.failure_type, 0) + 1
        return patterns
    
    # ─────────────────────────────────────────
    # Pattern Memory Management
    # ─────────────────────────────────────────
    
    def remember_pattern(self, pattern: PatternMemory):
        """Store or update a repository pattern."""
        # Check if pattern already exists
        existing = next(
            (p for p in self.pattern_memories 
             if p.pattern_type == pattern.pattern_type and 
             p.pattern_description == pattern.pattern_description),
            None
        )
        
        if existing:
            # Update existing pattern
            existing.frequency += 1
            existing.confidence = min(existing.confidence + 0.1, 1.0)
            existing.last_seen = pattern.last_seen
            if pattern.examples[0] not in existing.examples:
                existing.examples.extend(pattern.examples)
        else:
            # Add new pattern
            self.pattern_memories.append(pattern)
        
        self._save_pattern_memories()
    
    def get_patterns_by_type(self, pattern_type: str) -> List[PatternMemory]:
        """Get patterns of a specific type."""
        return [
            p for p in self.pattern_memories
            if p.pattern_type == pattern_type
        ]
    
    def get_high_confidence_patterns(self, min_confidence: float = 0.7) -> List[PatternMemory]:
        """Get patterns with high confidence."""
        return [
            p for p in self.pattern_memories
            if p.confidence >= min_confidence
        ]
    
    # ─────────────────────────────────────────
    # Style Memory Management
    # ─────────────────────────────────────────
    
    def remember_style(self, style: StyleMemory):
        """Store or update a coding style preference."""
        # Check if style rule already exists
        existing = next(
            (s for s in self.style_memories
             if s.language == style.language and s.style_rule == style.style_rule),
            None
        )
        
        if existing:
            # Update if new confidence is higher
            if style.confidence > existing.confidence:
                existing.value = style.value
                existing.source = style.source
                existing.confidence = style.confidence
        else:
            # Add new style
            self.style_memories.append(style)
        
        self._save_style_memories()
    
    def get_style_guide(self, language: str) -> Dict[str, str]:
        """Get style guide for a language."""
        styles = [s for s in self.style_memories if s.language == language]
        return {s.style_rule: s.value for s in styles}
    
    # ─────────────────────────────────────────
    # Learning & Analysis
    # ─────────────────────────────────────────
    
    def learn_from_pr(self, pr_memory: PRMemory):
        """Learn patterns and styles from a successful PR."""
        if pr_memory.test_status == "PASSED" and pr_memory.quality_score >= 70:
            # This was a good PR, learn from it
            for filepath in pr_memory.files_modified:
                # Learn file structure patterns
                if '/' in filepath:
                    directory = '/'.join(filepath.split('/')[:-1])
                    pattern = PatternMemory(
                        pattern_type="file_structure",
                        pattern_description=f"Files in {directory}",
                        examples=[filepath],
                        frequency=1,
                        confidence=0.6,
                        last_seen=pr_memory.created_at,
                    )
                    self.remember_pattern(pattern)
    
    def get_learning_summary(self) -> Dict:
        """Get summary of what the agent has learned."""
        return {
            "total_prs": len(self.pr_memories),
            "successful_prs": len([p for p in self.pr_memories if p.test_status == "PASSED"]),
            "total_failures": len(self.failure_memories),
            "resolved_failures": len([f for f in self.failure_memories if f.resolved]),
            "patterns_learned": len(self.pattern_memories),
            "high_confidence_patterns": len(self.get_high_confidence_patterns()),
            "style_rules": len(self.style_memories),
            "failure_patterns": self.get_failure_patterns(),
        }
    
    # ─────────────────────────────────────────
    # Persistence
    # ─────────────────────────────────────────
    
    def _load_pr_memories(self) -> List[PRMemory]:
        """Load PR memories from disk."""
        if not self.pr_memory_file.exists():
            return []
        
        try:
            with open(self.pr_memory_file, 'r') as f:
                data = json.load(f)
                return [PRMemory(**item) for item in data]
        except Exception as e:
            print(f"  [Memory] Warning: Could not load PR memories: {e}")
            return []
    
    def _save_pr_memories(self):
        """Save PR memories to disk."""
        try:
            with open(self.pr_memory_file, 'w') as f:
                data = [asdict(pr) for pr in self.pr_memories]
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"  [Memory] Warning: Could not save PR memories: {e}")
    
    def _load_failure_memories(self) -> List[FailureMemory]:
        """Load failure memories from disk."""
        if not self.failure_memory_file.exists():
            return []
        
        try:
            with open(self.failure_memory_file, 'r') as f:
                data = json.load(f)
                return [FailureMemory(**item) for item in data]
        except Exception as e:
            print(f"  [Memory] Warning: Could not load failure memories: {e}")
            return []
    
    def _save_failure_memories(self):
        """Save failure memories to disk."""
        try:
            with open(self.failure_memory_file, 'w') as f:
                data = [asdict(failure) for failure in self.failure_memories]
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"  [Memory] Warning: Could not save failure memories: {e}")
    
    def _load_pattern_memories(self) -> List[PatternMemory]:
        """Load pattern memories from disk."""
        if not self.pattern_memory_file.exists():
            return []
        
        try:
            with open(self.pattern_memory_file, 'r') as f:
                data = json.load(f)
                return [PatternMemory(**item) for item in data]
        except Exception as e:
            print(f"  [Memory] Warning: Could not load pattern memories: {e}")
            return []
    
    def _save_pattern_memories(self):
        """Save pattern memories to disk."""
        try:
            with open(self.pattern_memory_file, 'w') as f:
                data = [asdict(pattern) for pattern in self.pattern_memories]
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"  [Memory] Warning: Could not save pattern memories: {e}")
    
    def _load_style_memories(self) -> List[StyleMemory]:
        """Load style memories from disk."""
        if not self.style_memory_file.exists():
            return []
        
        try:
            with open(self.style_memory_file, 'r') as f:
                data = json.load(f)
                return [StyleMemory(**item) for item in data]
        except Exception as e:
            print(f"  [Memory] Warning: Could not load style memories: {e}")
            return []
    
    def _save_style_memories(self):
        """Save style memories to disk."""
        try:
            with open(self.style_memory_file, 'w') as f:
                data = [asdict(style) for style in self.style_memories]
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"  [Memory] Warning: Could not save style memories: {e}")


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  AGENT MEMORY - TEST RUN")
    print("=" * 70)
    
    # Create memory system
    memory = AgentMemory(memory_dir=".test_memory")
    
    # Test PR memory
    print("\n[TEST] Storing PR memory...")
    pr = PRMemory(
        ticket_id="SCRUM-1",
        pr_number=1,
        pr_url="https://github.com/user/repo/pull/1",
        branch_name="feature/scrum-1",
        files_modified=["backend/routes/auth.py", "backend/models/user.py"],
        test_status="PASSED",
        quality_score=85,
        issues_found=[],
        created_at=datetime.now().isoformat(),
        merged=True,
    )
    memory.remember_pr(pr)
    
    # Test failure memory
    print("\n[TEST] Storing failure memory...")
    failure = FailureMemory(
        ticket_id="SCRUM-2",
        failure_type="test_failure",
        error_message="AssertionError: Expected 200, got 404",
        files_involved=["backend/routes/api.py"],
        resolution="Fixed route path",
        occurred_at=datetime.now().isoformat(),
        resolved=True,
    )
    memory.remember_failure(failure)
    
    # Test pattern memory
    print("\n[TEST] Storing pattern memory...")
    pattern = PatternMemory(
        pattern_type="file_structure",
        pattern_description="API routes in backend/routes/",
        examples=["backend/routes/auth.py", "backend/routes/api.py"],
        frequency=2,
        confidence=0.8,
        last_seen=datetime.now().isoformat(),
    )
    memory.remember_pattern(pattern)
    
    # Test style memory
    print("\n[TEST] Storing style memory...")
    style = StyleMemory(
        language="python",
        style_rule="max_line_length",
        value="127",
        source="config_file",
        confidence=1.0,
    )
    memory.remember_style(style)
    
    # Get learning summary
    print("\n[RESULT] Learning Summary:")
    summary = memory.get_learning_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("  [DONE] Agent memory test complete")
    print("=" * 70 + "\n")
