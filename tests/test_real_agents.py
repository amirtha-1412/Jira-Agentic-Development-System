"""
tests/test_real_agents.py
---------------------------------------------
Test Real Developer and QA Agents
Tests the complete workflow with actual LLM-powered agents.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from workflows.orchestrator.graph import execute_workflow, get_workflow_status


def test_real_agents_workflow():
    """Tests workflow with real Developer and QA agents."""
    print("\n" + "=" * 70)
    print("  TEST: REAL AGENTS WORKFLOW")
    print("=" * 70)
    
    ticket_data = {
        "ticket_id": "REAL-1",
        "title": "Add user registration endpoint",
        "summary": "Add user registration endpoint",
        "description": (
            "Create a REST API endpoint for user registration.\n"
            "Requirements:\n"
            "- Accept email and password\n"
            "- Validate email format\n"
            "- Hash password with bcrypt\n"
            "- Store user in database\n"
            "- Return user ID and success message"
        ),
        "status": "TODO",
        "priority": "HIGH",
        "issue_type": "Story",
        "assignee": "AI Agent",
    }
    
    print(f"\n📋 Ticket: {ticket_data['ticket_id']}")
    print(f"   Title: {ticket_data['title']}")
    print(f"   Expected: Real code generation + QA validation")
    print("\n" + "-" * 70)
    
    # Execute workflow with real agents
    final_state = execute_workflow(
        ticket_id=ticket_data["ticket_id"],
        ticket_data=ticket_data,
        max_retries=1,  # Allow 1 retry
        verbose=True,
    )
    
    # Validate results
    print("\n" + "=" * 70)
    print("  VALIDATION")
    print("=" * 70)
    
    status = get_workflow_status(final_state)
    
    checks = [
        ("Workflow completed", final_state.get("pipeline_status") == "completed"),
        ("Code generated", len(final_state.get("generated_code", {})) > 0),
        ("Test cases created", len(final_state.get("test_cases", [])) > 0),
        ("QA validation ran", final_state.get("test_status") in ["PASSED", "FAILED", "PARTIAL"]),
        ("PR generated", bool(final_state.get("pr_title"))),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        emoji = "✅" if passed else "❌"
        print(f"   {emoji} {check_name}")
        if not passed:
            all_passed = False
    
    # Display details
    print(f"\n📊 Results:")
    print(f"   Pipeline Status: {status['pipeline_status']}")
    print(f"   Test Status: {status['test_status']}")
    print(f"   Retry Count: {status['retry_count']}")
    print(f"   Generated Files: {len(final_state.get('generated_code', {}))}")
    print(f"   Test Cases: {len(final_state.get('test_cases', []))}")
    
    # Show generated files
    if final_state.get("generated_code"):
        print(f"\n📁 Generated Files:")
        for filename in final_state.get("generated_code", {}).keys():
            print(f"   - {filename}")
    
    # Show QA notes
    if final_state.get("qa_notes"):
        print(f"\n🧪 QA Notes:")
        qa_notes = final_state.get("qa_notes", "")
        for line in qa_notes.split("\n")[:10]:
            print(f"   {line}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  ✅ TEST PASSED - Real agents working!")
    else:
        print("  ⚠️  TEST PARTIAL - Some checks failed")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = test_real_agents_workflow()
    sys.exit(0 if success else 1)
