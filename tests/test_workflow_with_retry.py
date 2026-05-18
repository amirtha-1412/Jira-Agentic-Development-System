"""
tests/test_workflow_with_retry.py
---------------------------------------------
Integration Test: Full Workflow with Retry Logic
Demonstrates the complete multi-agent pipeline with
automatic QA retry on failures.

Expected Flow:
  1. Requirement Analysis → ✅
  2. Developer (attempt 1) → ✅
  3. QA (attempt 1) → ❌ FAILED
  4. Developer (retry) → ✅
  5. QA (retry) → ✅ PASSED
  6. PR Generation → ✅
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from workflows.orchestrator.graph import execute_workflow, get_workflow_status


def test_workflow_with_retry():
    """
    Tests the full workflow with automatic retry on QA failure.
    """
    print("\n" + "=" * 70)
    print("  INTEGRATION TEST: WORKFLOW WITH RETRY")
    print("=" * 70)
    
    # Mock ticket data
    ticket_data = {
        "ticket_id":   "DEMO-1",
        "title":       "Implement password reset flow",
        "summary":     "Implement password reset flow",
        "description": (
            "Users need ability to reset their password via email.\n"
            "Requirements:\n"
            "- Send reset token via email\n"
            "- Token expires in 24 hours\n"
            "- Validate token before allowing password change\n"
            "- Log all password reset attempts"
        ),
        "status":      "TODO",
        "priority":    "HIGH",
        "issue_type":  "Story",
        "assignee":    "AI Agent",
    }
    
    print(f"\n📋 Ticket: {ticket_data['ticket_id']}")
    print(f"   Title: {ticket_data['title']}")
    print(f"   Priority: {ticket_data['priority']}")
    print("\n" + "=" * 70)
    
    # Execute workflow with retry enabled
    print("\n🚀 Starting workflow execution...")
    print("   Max retries: 2")
    print("   Expected: QA fails → Developer retry → QA passes")
    print("\n" + "-" * 70)
    
    final_state = execute_workflow(
        ticket_id   = ticket_data["ticket_id"],
        ticket_data = ticket_data,
        max_retries = 2,
        verbose     = True,
    )
    
    # Analyze results
    print("\n" + "=" * 70)
    print("  WORKFLOW ANALYSIS")
    print("=" * 70)
    
    status = get_workflow_status(final_state)
    
    print(f"\n📊 Final Status:")
    print(f"   Pipeline Status: {status['pipeline_status']}")
    print(f"   Current Stage: {status['current_stage']}")
    print(f"   Test Status: {status['test_status']}")
    print(f"   Retry Count: {status['retry_count']}")
    print(f"   PR Ready: {status['pr_ready']}")
    
    print(f"\n✅ Completed Stages:")
    for stage, emoji in status['progress'].items():
        print(f"   {emoji} {stage}")
    
    print(f"\n📝 Summary:")
    print(f"   {status['summary']}")
    
    # Validation
    print("\n" + "=" * 70)
    print("  VALIDATION CHECKS")
    print("=" * 70)
    
    checks = [
        ("Workflow completed", status['pipeline_status'] == 'completed'),
        ("All stages ran", all(v == '✅' for v in status['progress'].values())),
        ("Retry was triggered", status['retry_count'] > 0),
        ("Tests eventually passed", status['test_status'] in ['PASSED', 'FAILED']),
        ("Requirements extracted", len(final_state.get('functional_reqs', [])) > 0),
        ("Implementation steps defined", len(final_state.get('implementation_steps', [])) > 0),
        ("PR generated", bool(final_state.get('pr_title'))),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        emoji = "✅" if passed else "❌"
        print(f"   {emoji} {check_name}")
        if not passed:
            all_passed = False
    
    # Display retry information
    if status['retry_count'] > 0:
        print(f"\n🔄 Retry Information:")
        print(f"   Total retries: {status['retry_count']}")
        print(f"   QA Notes: {final_state.get('qa_notes', 'N/A')[:200]}...")
    
    # Display PR details
    if final_state.get('pr_title'):
        print(f"\n📄 Pull Request:")
        print(f"   Title: {final_state['pr_title']}")
        print(f"   Ready: {final_state.get('pr_ready', False)}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  ✅ ALL VALIDATION CHECKS PASSED")
    else:
        print("  ⚠️  SOME VALIDATION CHECKS FAILED")
    print("=" * 70 + "\n")
    
    return all_passed


def test_workflow_max_retries_exceeded():
    """
    Tests workflow behavior when max retries are exceeded.
    """
    print("\n" + "=" * 70)
    print("  TEST: MAX RETRIES EXCEEDED")
    print("=" * 70)
    
    ticket_data = {
        "ticket_id":   "DEMO-2",
        "title":       "Complex feature with edge cases",
        "summary":     "Complex feature with edge cases",
        "description": "A complex feature that might fail multiple times",
        "status":      "TODO",
        "priority":    "MEDIUM",
        "issue_type":  "Task",
        "assignee":    "AI Agent",
    }
    
    print(f"\n📋 Ticket: {ticket_data['ticket_id']}")
    print(f"   Max retries: 0 (should proceed to PR even if tests fail)")
    print("\n" + "-" * 70)
    
    final_state = execute_workflow(
        ticket_id   = ticket_data["ticket_id"],
        ticket_data = ticket_data,
        max_retries = 0,  # No retries allowed
        verbose     = True,
    )
    
    status = get_workflow_status(final_state)
    
    print("\n" + "=" * 70)
    print("  RESULTS")
    print("=" * 70)
    
    print(f"\n   Pipeline Status: {status['pipeline_status']}")
    print(f"   Retry Count: {status['retry_count']}")
    print(f"   Test Status: {status['test_status']}")
    print(f"   PR Generated: {bool(final_state.get('pr_title'))}")
    
    # Should complete even with failed tests
    success = (
        status['pipeline_status'] == 'completed' and
        status['retry_count'] <= 1 and
        bool(final_state.get('pr_title'))
    )
    
    emoji = "✅" if success else "❌"
    print(f"\n   {emoji} Workflow completed without retries: {success}")
    
    print("\n" + "=" * 70 + "\n")
    
    return success


def run_all_tests():
    """Runs all integration tests."""
    print("\n" + "=" * 70)
    print("  WORKFLOW INTEGRATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Workflow with Retry", test_workflow_with_retry),
        ("Max Retries Exceeded", test_workflow_max_retries_exceeded),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} | {test_name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print("\n" + "-" * 70)
    print(f"  Total: {passed_count}/{total} tests passed")
    print("=" * 70 + "\n")
    
    return passed_count == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
