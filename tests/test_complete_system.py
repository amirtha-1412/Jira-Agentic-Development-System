"""
tests/test_complete_system.py
---------------------------------------------
Complete System Test - All Real Agents
Tests the entire workflow with all real LLM-powered agents:
  - Requirement Analyst
  - Developer Agent
  - QA Agent
  - PR Agent
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from workflows.orchestrator.graph import execute_workflow, get_workflow_status


def test_complete_system():
    """Tests complete system with all real agents."""
    print("\n" + "=" * 70)
    print("  COMPLETE SYSTEM TEST - ALL REAL AGENTS")
    print("=" * 70)
    
    ticket_data = {
        "ticket_id": "COMPLETE-1",
        "title": "Add password reset functionality",
        "summary": "Add password reset functionality",
        "description": (
            "Implement password reset feature for users.\n\n"
            "Requirements:\n"
            "- User can request password reset via email\n"
            "- System sends reset token to user's email\n"
            "- Token expires after 24 hours\n"
            "- User can set new password with valid token\n"
            "- Old password is invalidated after reset\n\n"
            "Technical Requirements:\n"
            "- Use secure random token generation\n"
            "- Hash tokens before storing\n"
            "- Implement rate limiting\n"
            "- Add email validation\n"
            "- Log all reset attempts"
        ),
        "status": "TODO",
        "priority": "HIGH",
        "issue_type": "Story",
        "assignee": "AI Agent",
    }
    
    print(f"\n📋 Ticket: {ticket_data['ticket_id']}")
    print(f"   Title: {ticket_data['title']}")
    print(f"   Priority: {ticket_data['priority']}")
    print(f"\n   Expected Flow:")
    print(f"   1. Requirement Analyst → Analyzes ticket")
    print(f"   2. Developer Agent → Generates code")
    print(f"   3. QA Agent → Validates code")
    print(f"   4. PR Agent → Creates PR description")
    print("\n" + "-" * 70)
    
    # Execute complete workflow
    final_state = execute_workflow(
        ticket_id=ticket_data["ticket_id"],
        ticket_data=ticket_data,
        max_retries=1,
        verbose=True,
    )
    
    # Validate results
    print("\n" + "=" * 70)
    print("  VALIDATION - ALL AGENTS")
    print("=" * 70)
    
    status = get_workflow_status(final_state)
    
    checks = [
        ("✅ Requirement Analyst ran", "requirement" in final_state.get("completed_stages", [])),
        ("✅ Developer Agent ran", "developer" in final_state.get("completed_stages", [])),
        ("✅ QA Agent ran", "qa" in final_state.get("completed_stages", [])),
        ("✅ PR Agent ran", "pr" in final_state.get("completed_stages", [])),
        ("✅ Requirements extracted", len(final_state.get("functional_reqs", [])) > 0),
        ("✅ Code generated", len(final_state.get("generated_code", {})) > 0),
        ("✅ Tests created", len(final_state.get("test_cases", [])) > 0),
        ("✅ PR generated", bool(final_state.get("pr_title"))),
        ("✅ PR labels added", len(final_state.get("pr_labels", [])) > 0),
        ("✅ Reviewers suggested", len(final_state.get("reviewers_suggested", [])) > 0),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        emoji = "✅" if passed else "❌"
        print(f"   {emoji} {check_name}")
        if not passed:
            all_passed = False
    
    # Display comprehensive results
    print(f"\n📊 Complete Results:")
    print(f"   Pipeline Status: {status['pipeline_status']}")
    print(f"   Current Stage: {status['current_stage']}")
    print(f"   Test Status: {status['test_status']}")
    print(f"   Retry Count: {status['retry_count']}")
    print(f"   PR Ready: {status['pr_ready']}")
    
    print(f"\n📋 Requirement Analysis:")
    print(f"   Functional Requirements: {len(final_state.get('functional_reqs', []))}")
    print(f"   Technical Requirements: {len(final_state.get('technical_reqs', []))}")
    print(f"   Implementation Steps: {len(final_state.get('implementation_steps', []))}")
    print(f"   Risk Level: {final_state.get('risk_level', 'N/A')}")
    
    print(f"\n💻 Developer Output:")
    print(f"   Files Generated: {len(final_state.get('generated_code', {}))}")
    if final_state.get("generated_code"):
        print(f"   Generated Files:")
        for filename in list(final_state.get("generated_code", {}).keys())[:5]:
            print(f"     - {filename}")
    
    print(f"\n🧪 QA Results:")
    print(f"   Test Cases: {len(final_state.get('test_cases', []))}")
    print(f"   Test Status: {final_state.get('test_status', 'N/A')}")
    if final_state.get("qa_notes"):
        print(f"   QA Notes (preview):")
        for line in final_state.get("qa_notes", "").split("\n")[:5]:
            if line.strip():
                print(f"     {line}")
    
    print(f"\n📝 PR Details:")
    print(f"   Title: {final_state.get('pr_title', 'N/A')}")
    print(f"   Labels: {', '.join(final_state.get('pr_labels', []))}")
    print(f"   Reviewers: {', '.join(final_state.get('reviewers_suggested', []))}")
    print(f"   PR Ready: {final_state.get('pr_ready', False)}")
    if final_state.get("pr_description"):
        print(f"   Description (preview):")
        desc_lines = final_state.get("pr_description", "").split("\n")[:8]
        for line in desc_lines:
            if line.strip():
                print(f"     {line}")
    
    # Progress visualization
    print(f"\n📈 Progress:")
    for stage, emoji in status.get('progress', {}).items():
        print(f"   {emoji} {stage.capitalize()}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  🎉 ALL AGENTS WORKING - COMPLETE SYSTEM TEST PASSED!")
    else:
        print("  ⚠️  SOME CHECKS FAILED - REVIEW ABOVE")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = test_complete_system()
    
    print("\n" + "=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)
    print(f"  Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"  All Agents: {'✅ Working' if success else '⚠️  Issues detected'}")
    print("=" * 70 + "\n")
    
    sys.exit(0 if success else 1)
