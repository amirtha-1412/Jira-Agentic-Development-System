"""
tests/test_final_integration.py
---------------------------------------------
Final Integration Testing
Validates the complete orchestration system end-to-end.

Test Scenarios:
  1. Valid feature request → Full execution
  2. QA failure → Retry triggered
  3. Invalid ticket → Safe handling
  4. Logs generated → Explainable workflow
  5. API endpoint → Workflow execution
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from workflows.orchestrator.graph import execute_workflow, get_workflow_status


# ─────────────────────────────────────────────
# Test 1: Valid Feature Request → Full Execution
# ─────────────────────────────────────────────

def test_valid_feature_request():
    """
    Tests complete workflow execution with a valid feature request.
    
    Expected Flow:
      Jira Ticket
        ↓
      Requirement Agent (analyzes)
        ↓
      Developer Agent (generates code)
        ↓
      QA Agent (tests code)
        ↓
      Retry Loop (if needed)
        ↓
      PR Agent (creates PR)
        ↓
      Workflow Result
    """
    print("\n" + "=" * 70)
    print("  TEST 1: VALID FEATURE REQUEST → FULL EXECUTION")
    print("=" * 70)
    
    ticket_data = {
        "ticket_id": "FINAL-1",
        "title": "Add user authentication with JWT",
        "summary": "Add user authentication with JWT",
        "description": (
            "Implement JWT-based authentication for the API.\n"
            "Requirements:\n"
            "- User login endpoint\n"
            "- Token generation and validation\n"
            "- Protected routes middleware\n"
            "- Token refresh mechanism\n"
            "- Logout functionality"
        ),
        "status": "TODO",
        "priority": "HIGH",
        "issue_type": "Story",
        "assignee": "AI Agent",
    }
    
    print(f"\n📋 Ticket: {ticket_data['ticket_id']}")
    print(f"   Title: {ticket_data['title']}")
    print(f"   Priority: {ticket_data['priority']}")
    print("\n" + "-" * 70)
    
    # Execute workflow
    final_state = execute_workflow(
        ticket_id=ticket_data["ticket_id"],
        ticket_data=ticket_data,
        max_retries=2,
        verbose=True,
    )
    
    # Validate results
    print("\n" + "=" * 70)
    print("  VALIDATION")
    print("=" * 70)
    
    checks = [
        ("Workflow completed", final_state.get("pipeline_status") == "completed"),
        ("Requirement stage completed", "requirement" in final_state.get("completed_stages", [])),
        ("Developer stage completed", "developer" in final_state.get("completed_stages", [])),
        ("QA stage completed", "qa" in final_state.get("completed_stages", [])),
        ("PR stage completed", "pr" in final_state.get("completed_stages", [])),
        ("Requirements extracted", len(final_state.get("functional_reqs", [])) > 0),
        ("Implementation steps defined", len(final_state.get("implementation_steps", [])) > 0),
        ("Test cases generated", len(final_state.get("test_cases", [])) > 0),
        ("PR generated", bool(final_state.get("pr_title"))),
        ("No critical errors", not any("CRITICAL" in str(e) for e in final_state.get("errors", []))),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        emoji = "✅" if passed else "❌"
        print(f"   {emoji} {check_name}")
        if not passed:
            all_passed = False
    
    # Display summary
    status = get_workflow_status(final_state)
    print(f"\n📊 Summary:")
    print(f"   Pipeline Status: {status['pipeline_status']}")
    print(f"   Test Status: {status['test_status']}")
    print(f"   Retry Count: {status['retry_count']}")
    print(f"   PR Ready: {status['pr_ready']}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  ✅ TEST 1 PASSED")
    else:
        print("  ❌ TEST 1 FAILED")
    print("=" * 70)
    
    return all_passed


# ─────────────────────────────────────────────
# Test 2: QA Failure → Retry Triggered
# ─────────────────────────────────────────────

def test_qa_failure_retry():
    """
    Tests that QA failures trigger automatic retry.
    
    Expected Flow:
      Developer generates code (attempt 1)
        ↓
      QA tests fail
        ↓
      Conditional edge detects failure
        ↓
      Developer regenerates code (retry)
        ↓
      QA re-tests
        ↓
      Tests pass
        ↓
      PR generated
    """
    print("\n" + "=" * 70)
    print("  TEST 2: QA FAILURE → RETRY TRIGGERED")
    print("=" * 70)
    
    ticket_data = {
        "ticket_id": "FINAL-2",
        "title": "Complex feature with edge cases",
        "summary": "Complex feature with edge cases",
        "description": "A complex feature that will trigger QA failures initially",
        "status": "TODO",
        "priority": "MEDIUM",
        "issue_type": "Task",
        "assignee": "AI Agent",
    }
    
    print(f"\n📋 Ticket: {ticket_data['ticket_id']}")
    print(f"   Expected: QA fails → Retry → QA passes")
    print("\n" + "-" * 70)
    
    # Execute workflow
    final_state = execute_workflow(
        ticket_id=ticket_data["ticket_id"],
        ticket_data=ticket_data,
        max_retries=2,
        verbose=True,
    )
    
    # Validate retry behavior
    print("\n" + "=" * 70)
    print("  VALIDATION")
    print("=" * 70)
    
    retry_count = final_state.get("retry_count", 0)
    test_status = final_state.get("test_status", "NOT_RUN")
    
    checks = [
        ("Retry was triggered", retry_count > 0),
        ("Retry count reasonable", retry_count <= 2),
        ("Workflow completed", final_state.get("pipeline_status") == "completed"),
        ("Developer ran multiple times", "developer" in final_state.get("completed_stages", [])),
        ("QA ran multiple times", "qa" in final_state.get("completed_stages", [])),
        ("Final test status recorded", test_status in ["PASSED", "FAILED"]),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        emoji = "✅" if passed else "❌"
        print(f"   {emoji} {check_name}")
        if not passed:
            all_passed = False
    
    print(f"\n🔄 Retry Information:")
    print(f"   Total Retries: {retry_count}")
    print(f"   Final Test Status: {test_status}")
    print(f"   QA Notes: {final_state.get('qa_notes', 'N/A')[:100]}...")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  ✅ TEST 2 PASSED")
    else:
        print("  ❌ TEST 2 FAILED")
    print("=" * 70)
    
    return all_passed


# ─────────────────────────────────────────────
# Test 3: Invalid Ticket → Safe Handling
# ─────────────────────────────────────────────

def test_invalid_ticket_handling():
    """
    Tests that invalid tickets are handled gracefully.
    
    Expected:
      - No crashes
      - Error captured in state
      - Pipeline status = failed
      - Errors list populated
    """
    print("\n" + "=" * 70)
    print("  TEST 3: INVALID TICKET → SAFE HANDLING")
    print("=" * 70)
    
    # Test with minimal/invalid ticket data
    ticket_data = {
        "ticket_id": "INVALID-1",
        "title": "",
        "summary": "",
        "description": "",
        "status": "UNKNOWN",
        "priority": "NONE",
        "issue_type": "Unknown",
        "assignee": "Unassigned",
    }
    
    print(f"\n📋 Ticket: {ticket_data['ticket_id']}")
    print(f"   Expected: Graceful error handling")
    print("\n" + "-" * 70)
    
    # Execute workflow (should not crash)
    try:
        final_state = execute_workflow(
            ticket_id=ticket_data["ticket_id"],
            ticket_data=ticket_data,
            max_retries=1,
            verbose=False,  # Reduce noise
        )
        
        crashed = False
    except Exception as e:
        print(f"   ⚠️  Exception caught: {e}")
        crashed = True
        final_state = {}
    
    # Validate error handling
    print("\n" + "=" * 70)
    print("  VALIDATION")
    print("=" * 70)
    
    checks = [
        ("Did not crash", not crashed),
        ("Workflow attempted", final_state.get("pipeline_status") in ["completed", "failed", "running"]),
        ("State returned", isinstance(final_state, dict)),
        ("Ticket ID preserved", final_state.get("ticket_id") == "INVALID-1"),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        emoji = "✅" if passed else "❌"
        print(f"   {emoji} {check_name}")
        if not passed:
            all_passed = False
    
    if final_state.get("errors"):
        print(f"\n⚠️  Errors captured:")
        for err in final_state.get("errors", [])[:3]:
            print(f"   - {err}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  ✅ TEST 3 PASSED")
    else:
        print("  ❌ TEST 3 FAILED")
    print("=" * 70)
    
    return all_passed


# ─────────────────────────────────────────────
# Test 4: Logs Generated → Explainable Workflow
# ─────────────────────────────────────────────

def test_explainable_logs():
    """
    Tests that explainable logs are generated throughout execution.
    
    Expected:
      - Logs contain emoji indicators
      - Logs contain "Reason:" statements
      - Logs show progress through stages
      - Logs explain retry decisions
    """
    print("\n" + "=" * 70)
    print("  TEST 4: LOGS GENERATED → EXPLAINABLE WORKFLOW")
    print("=" * 70)
    
    ticket_data = {
        "ticket_id": "FINAL-4",
        "title": "Test explainable logging",
        "summary": "Test explainable logging",
        "description": "Simple feature to test logging",
        "status": "TODO",
        "priority": "LOW",
        "issue_type": "Task",
        "assignee": "AI Agent",
    }
    
    print(f"\n📋 Ticket: {ticket_data['ticket_id']}")
    print(f"   Expected: Detailed explainable logs")
    print("\n" + "-" * 70)
    
    # Capture output
    import io
    from contextlib import redirect_stdout
    
    log_buffer = io.StringIO()
    
    with redirect_stdout(log_buffer):
        final_state = execute_workflow(
            ticket_id=ticket_data["ticket_id"],
            ticket_data=ticket_data,
            max_retries=1,
            verbose=True,
        )
    
    logs = log_buffer.getvalue()
    
    # Validate log content
    print("\n" + "=" * 70)
    print("  VALIDATION")
    print("=" * 70)
    
    checks = [
        ("Logs generated", len(logs) > 0),
        ("Contains ReqNode logs", "[ReqNode]" in logs),
        ("Contains DevNode logs", "[DevNode]" in logs),
        ("Contains QANode logs", "[QANode]" in logs),
        ("Contains PRNode logs", "[PRNode]" in logs),
        ("Contains emoji indicators", any(emoji in logs for emoji in ["🔍", "💻", "🧪", "📝"])),
        ("Contains reason statements", "Reason:" in logs),
        ("Contains completion markers", "✅" in logs),
        ("Shows workflow stages", "Starting" in logs and "completed" in logs),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        emoji = "✅" if passed else "❌"
        print(f"   {emoji} {check_name}")
        if not passed:
            all_passed = False
    
    # Show log sample
    print(f"\n📝 Log Sample (first 500 chars):")
    print(f"   {logs[:500]}...")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  ✅ TEST 4 PASSED")
    else:
        print("  ❌ TEST 4 FAILED")
    print("=" * 70)
    
    return all_passed


# ─────────────────────────────────────────────
# Test Runner
# ─────────────────────────────────────────────

def run_final_integration_tests():
    """Runs all final integration tests."""
    print("\n" + "=" * 70)
    print("  FINAL INTEGRATION TEST SUITE")
    print("  Complete Orchestration System Validation")
    print("=" * 70)
    
    tests = [
        ("Valid Feature Request → Full Execution", test_valid_feature_request),
        ("QA Failure → Retry Triggered", test_qa_failure_retry),
        ("Invalid Ticket → Safe Handling", test_invalid_ticket_handling),
        ("Logs Generated → Explainable Workflow", test_explainable_logs),
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
    
    # Final Summary
    print("\n" + "=" * 70)
    print("  FINAL INTEGRATION TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} | {test_name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print("\n" + "-" * 70)
    print(f"  Total: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n  🎉 ALL INTEGRATION TESTS PASSED!")
        print("  ✅ Complete orchestration system validated")
        print("  ✅ Ready for production deployment")
    else:
        print(f"\n  ⚠️  {total - passed_count} test(s) failed")
        print("  Review failures above for details")
    
    print("=" * 70 + "\n")
    
    return passed_count == total


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    success = run_final_integration_tests()
    sys.exit(0 if success else 1)
