"""
workflows/retry/retry_manager.py
---------------------------------------------
Retry Manager for QA Failures
Handles automatic retry logic when QA tests fail.

Features:
  - Configurable max retry attempts
  - Exponential backoff (optional)
  - Retry reason tracking
  - Failure pattern detection
  - Autonomous debugging loops

Design:
  QA Fail → Developer Retry → QA Retest → [Pass/Fail]
  
  If still failing after max retries:
    → Proceed to PR with warnings
    → Log failure reasons for human review
"""

from typing import Optional
from workflows.state import WorkflowState


# ─────────────────────────────────────────────
# Retry Decision Logic
# ─────────────────────────────────────────────

def should_retry(state: WorkflowState) -> bool:
    """
    Determines if the workflow should retry development
    based on QA test results and retry count.
    
    Args:
        state: Current workflow state
    
    Returns:
        bool: True if retry should be triggered
    """
    test_status = state.get("test_status", "NOT_RUN")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)
    errors      = state.get("errors", [])
    
    # Don't retry if critical errors
    if any("CRITICAL" in str(e).upper() for e in errors):
        return False
    
    # Don't retry if max attempts reached
    if retry_count >= max_retries:
        return False
    
    # Retry if tests failed or partially passed
    if test_status in ["FAILED", "PARTIAL"]:
        return True
    
    return False


def get_retry_reason(state: WorkflowState) -> str:
    """
    Generates a human-readable reason for the retry.
    
    Args:
        state: Current workflow state
    
    Returns:
        str: Explanation of why retry is needed
    """
    test_status = state.get("test_status", "UNKNOWN")
    qa_notes    = state.get("qa_notes", "")
    retry_count = state.get("retry_count", 0)
    
    reasons = []
    
    if test_status == "FAILED":
        reasons.append("QA tests failed")
    elif test_status == "PARTIAL":
        reasons.append("QA tests partially passed")
    
    # Extract specific failure from QA notes
    if "Missing implementation" in qa_notes:
        reasons.append("missing core implementation")
    elif "FAILED" in qa_notes:
        reasons.append("test execution failures detected")
    
    if not reasons:
        reasons.append("quality issues detected")
    
    return f"Retry #{retry_count + 1}: {', '.join(reasons)}"


# ─────────────────────────────────────────────
# Retry State Updater
# ─────────────────────────────────────────────

def prepare_retry_state(state: WorkflowState) -> dict:
    """
    Prepares state updates for a retry attempt.
    Increments retry count and adds retry metadata.
    
    Args:
        state: Current workflow state
    
    Returns:
        dict: State updates to merge
    """
    retry_count = state.get("retry_count", 0)
    retry_reason = get_retry_reason(state)
    
    return {
        "retry_count":   retry_count + 1,
        "retry_reason":  retry_reason,
        "current_stage": "developer_retry",
    }


# ─────────────────────────────────────────────
# Retry History Tracker
# ─────────────────────────────────────────────

class RetryHistory:
    """
    Tracks retry attempts and failure patterns
    for debugging and analysis.
    """
    
    def __init__(self):
        self.attempts = []
    
    def record_attempt(
        self,
        retry_count: int,
        test_status: str,
        qa_notes: str,
        reason: str,
    ):
        """Records a retry attempt."""
        self.attempts.append({
            "retry_count": retry_count,
            "test_status": test_status,
            "qa_notes":    qa_notes,
            "reason":      reason,
        })
    
    def get_failure_pattern(self) -> Optional[str]:
        """
        Analyzes retry history to detect failure patterns.
        
        Returns:
            str: Description of failure pattern, or None
        """
        if len(self.attempts) < 2:
            return None
        
        # Check if same failure repeats
        last_two = self.attempts[-2:]
        if all("Missing implementation" in a["qa_notes"] for a in last_two):
            return "Persistent implementation gap"
        
        if all(a["test_status"] == "FAILED" for a in last_two):
            return "Consistent test failures"
        
        return None
    
    def to_dict(self) -> dict:
        """Returns retry history as a dict."""
        return {
            "total_attempts": len(self.attempts),
            "attempts":       self.attempts,
            "pattern":        self.get_failure_pattern(),
        }


# ─────────────────────────────────────────────
# Retry Strategy Selector
# ─────────────────────────────────────────────

def select_retry_strategy(state: WorkflowState) -> str:
    """
    Selects the appropriate retry strategy based on
    failure type and retry history.
    
    Args:
        state: Current workflow state
    
    Returns:
        str: Strategy name (e.g., "full_regeneration", "targeted_fix")
    """
    retry_count = state.get("retry_count", 0)
    qa_notes    = state.get("qa_notes", "")
    
    # First retry: targeted fix
    if retry_count == 0:
        return "targeted_fix"
    
    # Second retry: full regeneration
    if retry_count == 1:
        return "full_regeneration"
    
    # Final retry: conservative approach
    return "conservative_fix"


# ─────────────────────────────────────────────
# Retry Feedback Generator
# ─────────────────────────────────────────────

def generate_retry_feedback(state: WorkflowState) -> str:
    """
    Generates detailed feedback for the developer agent
    to use during retry attempts.
    
    Args:
        state: Current workflow state
    
    Returns:
        str: Structured feedback for developer agent
    """
    qa_notes    = state.get("qa_notes", "")
    test_results = state.get("test_results", {})
    retry_count = state.get("retry_count", 0)
    strategy    = select_retry_strategy(state)
    
    feedback = f"## Retry Feedback (Attempt #{retry_count + 1})\n\n"
    feedback += f"**Strategy**: {strategy}\n\n"
    feedback += f"**QA Notes**:\n{qa_notes}\n\n"
    
    # Failed tests
    failed_tests = [k for k, v in test_results.items() if v == "FAILED"]
    if failed_tests:
        feedback += f"**Failed Tests**:\n"
        for test in failed_tests:
            feedback += f"  - {test}\n"
        feedback += "\n"
    
    # Recommendations
    feedback += f"**Recommendations**:\n"
    if "Missing implementation" in qa_notes:
        feedback += "  - Implement missing core functionality\n"
        feedback += "  - Ensure all functional requirements are addressed\n"
    else:
        feedback += "  - Review test failure details\n"
        feedback += "  - Fix identified issues\n"
        feedback += "  - Validate edge cases\n"
    
    return feedback


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    
    print("\n" + "=" * 70)
    print("  RETRY MANAGER - TEST RUN")
    print("=" * 70)
    
    # Test 1: Should retry logic
    print("\n[TEST 1] Should Retry Logic")
    print("-" * 70)
    
    test_states = [
        {
            "name": "Failed, no retries yet",
            "state": {"test_status": "FAILED", "retry_count": 0, "max_retries": 2, "errors": []},
            "expected": True,
        },
        {
            "name": "Failed, max retries reached",
            "state": {"test_status": "FAILED", "retry_count": 2, "max_retries": 2, "errors": []},
            "expected": False,
        },
        {
            "name": "Passed",
            "state": {"test_status": "PASSED", "retry_count": 0, "max_retries": 2, "errors": []},
            "expected": False,
        },
        {
            "name": "Critical error",
            "state": {"test_status": "FAILED", "retry_count": 0, "max_retries": 2, "errors": ["CRITICAL: crash"]},
            "expected": False,
        },
    ]
    
    for tc in test_states:
        result = should_retry(tc["state"])
        status = "✅" if result == tc["expected"] else "❌"
        print(f"  {status} {tc['name']}: {result} (expected {tc['expected']})")
    
    # Test 2: Retry reason generation
    print("\n[TEST 2] Retry Reason Generation")
    print("-" * 70)
    
    state = {
        "test_status": "FAILED",
        "retry_count": 0,
        "qa_notes": "Tests FAILED - Missing implementation",
    }
    reason = get_retry_reason(state)
    print(f"  Reason: {reason}")
    
    # Test 3: Retry feedback
    print("\n[TEST 3] Retry Feedback Generation")
    print("-" * 70)
    
    state = {
        "test_status": "FAILED",
        "retry_count": 0,
        "qa_notes": "Tests FAILED - Missing implementation",
        "test_results": {
            "Test: User login": "FAILED",
            "Test: Password reset": "SKIPPED",
        },
    }
    feedback = generate_retry_feedback(state)
    print(feedback)
    
    # Test 4: Retry history
    print("\n[TEST 4] Retry History Tracking")
    print("-" * 70)
    
    history = RetryHistory()
    history.record_attempt(0, "FAILED", "Missing implementation", "Retry #1")
    history.record_attempt(1, "FAILED", "Missing implementation", "Retry #2")
    
    pattern = history.get_failure_pattern()
    print(f"  Pattern detected: {pattern}")
    print(f"  Total attempts: {len(history.attempts)}")
    
    print("\n" + "=" * 70)
    print("  [DONE] Retry manager test complete")
    print("=" * 70 + "\n")
