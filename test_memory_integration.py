"""
test_memory_integration.py
---------------------------------------------
Test script to verify Agent Memory System integration.

Tests:
1. Memory system initialization
2. Developer Agent memory integration
3. QA Agent memory integration
4. PR memory storage
5. Learning from experience
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agents.memory.agent_memory import AgentMemory, PRMemory, FailureMemory, PatternMemory, StyleMemory
from agents.developer_agent import DeveloperAgent
from agents.qa_agent import QAAgent
from datetime import datetime
import shutil
import os


def test_memory_initialization():
    """Test 1: Memory system initialization."""
    print("\n" + "=" * 70)
    print("  TEST 1: Memory System Initialization")
    print("=" * 70)
    
    # Create test memory directory
    test_dir = ".test_memory_integration"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    # Initialize memory
    memory = AgentMemory(memory_dir=test_dir)
    
    # Verify memory files created
    assert os.path.exists(test_dir), "Memory directory not created"
    
    print("  [OK] Memory system initialized successfully")
    print(f"  [OK] Memory directory: {test_dir}")
    
    return memory, test_dir


def test_developer_agent_memory():
    """Test 2: Developer Agent memory integration."""
    print("\n" + "=" * 70)
    print("  TEST 2: Developer Agent Memory Integration")
    print("=" * 70)
    
    # Create agent with memory
    agent = DeveloperAgent(use_retriever=False, use_memory=True)
    
    # Verify memory is accessible
    memory = agent._get_memory()
    assert memory is not None, "Memory not initialized in Developer Agent"
    
    print("  [OK] Developer Agent memory integration working")
    print("  [OK] Memory context retrieval available")
    
    # Test memory context generation
    context = agent._get_memory_context("TEST-1", [])
    print(f"  [OK] Memory context generated (length: {len(context)})")
    
    return agent


def test_qa_agent_memory():
    """Test 3: QA Agent memory integration."""
    print("\n" + "=" * 70)
    print("  TEST 3: QA Agent Memory Integration")
    print("=" * 70)
    
    # Create agent with memory
    agent = QAAgent(use_memory=True)
    
    # Verify memory is accessible
    memory = agent._get_memory()
    assert memory is not None, "Memory not initialized in QA Agent"
    
    print("  [OK] QA Agent memory integration working")
    print("  [OK] Failure memory storage available")
    
    # Test failure context generation
    context = agent._get_similar_failures_context("TEST-1")
    print(f"  [OK] Failure context generated (length: {len(context)})")
    
    return agent


def test_pr_memory_storage(memory):
    """Test 4: PR memory storage."""
    print("\n" + "=" * 70)
    print("  TEST 4: PR Memory Storage")
    print("=" * 70)
    
    # Create test PR memory
    pr = PRMemory(
        ticket_id="TEST-1",
        pr_number=1,
        pr_url="https://github.com/test/repo/pull/1",
        branch_name="feature/test-1",
        files_modified=["backend/routes/test.py", "backend/models/test.py"],
        test_status="PASSED",
        quality_score=85,
        issues_found=[],
        created_at=datetime.now().isoformat(),
        merged=False,
    )
    
    # Store PR memory
    memory.remember_pr(pr)
    
    # Verify storage
    similar_prs = memory.get_similar_prs("TEST-1")
    assert len(similar_prs) > 0, "PR memory not stored"
    assert similar_prs[0].ticket_id == "TEST-1", "PR memory incorrect"
    
    print("  [OK] PR memory stored successfully")
    print(f"  [OK] Retrieved {len(similar_prs)} similar PR(s)")
    print(f"  [OK] PR Quality Score: {similar_prs[0].quality_score}/100")
    
    # Learn from PR
    memory.learn_from_pr(pr)
    print("  [OK] Learning from PR completed")


def test_failure_memory_storage(memory):
    """Test 5: Failure memory storage."""
    print("\n" + "=" * 70)
    print("  TEST 5: Failure Memory Storage")
    print("=" * 70)
    
    # Create test failure memory
    failure = FailureMemory(
        ticket_id="TEST-2",
        failure_type="test_failure",
        error_message="AssertionError: Expected 200, got 404",
        files_involved=["backend/routes/api.py"],
        resolution="Fixed route path",
        occurred_at=datetime.now().isoformat(),
        resolved=True,
    )
    
    # Store failure memory
    memory.remember_failure(failure)
    
    # Verify storage
    similar_failures = memory.get_similar_failures("Expected 200 got 404")
    assert len(similar_failures) > 0, "Failure memory not stored"
    
    print("  [OK] Failure memory stored successfully")
    print(f"  [OK] Retrieved {len(similar_failures)} similar failure(s)")
    
    # Get failure patterns
    patterns = memory.get_failure_patterns()
    print(f"  [OK] Failure patterns: {patterns}")


def test_pattern_memory_storage(memory):
    """Test 6: Pattern memory storage."""
    print("\n" + "=" * 70)
    print("  TEST 6: Pattern Memory Storage")
    print("=" * 70)
    
    # Create test pattern memory
    pattern = PatternMemory(
        pattern_type="file_structure",
        pattern_description="API routes in backend/routes/",
        examples=["backend/routes/auth.py", "backend/routes/api.py"],
        frequency=2,
        confidence=0.8,
        last_seen=datetime.now().isoformat(),
    )
    
    # Store pattern memory
    memory.remember_pattern(pattern)
    
    # Verify storage
    patterns = memory.get_patterns_by_type("file_structure")
    assert len(patterns) > 0, "Pattern memory not stored"
    
    print("  [OK] Pattern memory stored successfully")
    print(f"  [OK] Retrieved {len(patterns)} pattern(s)")
    
    # Get high confidence patterns
    high_conf = memory.get_high_confidence_patterns(min_confidence=0.7)
    print(f"  [OK] High confidence patterns: {len(high_conf)}")


def test_style_memory_storage(memory):
    """Test 7: Style memory storage."""
    print("\n" + "=" * 70)
    print("  TEST 7: Style Memory Storage")
    print("=" * 70)
    
    # Create test style memory
    style = StyleMemory(
        language="python",
        style_rule="max_line_length",
        value="127",
        source="config_file",
        confidence=1.0,
    )
    
    # Store style memory
    memory.remember_style(style)
    
    # Verify storage
    style_guide = memory.get_style_guide("python")
    assert len(style_guide) > 0, "Style memory not stored"
    assert "max_line_length" in style_guide, "Style rule not found"
    
    print("  [OK] Style memory stored successfully")
    print(f"  [OK] Style guide: {style_guide}")


def test_learning_summary(memory):
    """Test 8: Learning summary."""
    print("\n" + "=" * 70)
    print("  TEST 8: Learning Summary")
    print("=" * 70)
    
    # Get learning summary
    summary = memory.get_learning_summary()
    
    print("  [OK] Learning Summary:")
    print(f"     - Total PRs: {summary['total_prs']}")
    print(f"     - Successful PRs: {summary['successful_prs']}")
    print(f"     - Total Failures: {summary['total_failures']}")
    print(f"     - Resolved Failures: {summary['resolved_failures']}")
    print(f"     - Patterns Learned: {summary['patterns_learned']}")
    print(f"     - High Confidence Patterns: {summary['high_confidence_patterns']}")
    print(f"     - Style Rules: {summary['style_rules']}")
    print(f"     - Failure Patterns: {summary['failure_patterns']}")
    
    # Verify data
    assert summary['total_prs'] > 0, "No PRs in memory"
    assert summary['total_failures'] > 0, "No failures in memory"
    assert summary['patterns_learned'] > 0, "No patterns in memory"
    assert summary['style_rules'] > 0, "No styles in memory"
    
    print("  [OK] All memory types populated")


def cleanup(test_dir):
    """Cleanup test directory."""
    print("\n" + "=" * 70)
    print("  CLEANUP")
    print("=" * 70)
    
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"  [OK] Cleaned up test directory: {test_dir}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  AGENT MEMORY INTEGRATION - TEST SUITE")
    print("=" * 70)
    
    test_dir = None
    
    try:
        # Test 1: Memory initialization
        memory, test_dir = test_memory_initialization()
        
        # Test 2: Developer Agent memory
        dev_agent = test_developer_agent_memory()
        
        # Test 3: QA Agent memory
        qa_agent = test_qa_agent_memory()
        
        # Test 4: PR memory storage
        test_pr_memory_storage(memory)
        
        # Test 5: Failure memory storage
        test_failure_memory_storage(memory)
        
        # Test 6: Pattern memory storage
        test_pattern_memory_storage(memory)
        
        # Test 7: Style memory storage
        test_style_memory_storage(memory)
        
        # Test 8: Learning summary
        test_learning_summary(memory)
        
        # Final summary
        print("\n" + "=" * 70)
        print("  [OK] ALL TESTS PASSED")
        print("=" * 70)
        print("\n  Agent Memory System Integration: VERIFIED [OK]")
        print("  - Developer Agent: Memory-enabled [OK]")
        print("  - QA Agent: Memory-enabled [OK]")
        print("  - PR Storage: Working [OK]")
        print("  - Failure Learning: Working [OK]")
        print("  - Pattern Recognition: Working [OK]")
        print("  - Style Learning: Working [OK]")
        print("\n" + "=" * 70 + "\n")
    
    except Exception as e:
        print(f"\n  [FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if test_dir:
            cleanup(test_dir)


if __name__ == "__main__":
    main()
