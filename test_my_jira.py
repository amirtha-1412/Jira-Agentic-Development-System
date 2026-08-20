"""
test_my_jira.py
---------------------------------------------
Comprehensive Test Script for Your Jira Instance
Tests:
1. Jira Connection & Authentication
2. Fetch Real Tickets from Your Jira
3. Complete Workflow with Real Ticket
"""

import sys
import io
import os
from dotenv import load_dotenv

# Ensure UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Load environment variables
load_dotenv()


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """Print formatted section"""
    print("\n" + "-" * 70)
    print(f"  {title}")
    print("-" * 70)


def test_environment_config():
    """Test 1: Verify environment configuration"""
    print_header("TEST 1: ENVIRONMENT CONFIGURATION")
    
    required_vars = {
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "JIRA_BASE_URL": os.getenv("JIRA_BASE_URL"),
        "JIRA_EMAIL": os.getenv("JIRA_EMAIL"),
        "JIRA_API_KEY": os.getenv("JIRA_API_KEY"),
        "JIRA_PROJECT_KEY": os.getenv("JIRA_PROJECT_KEY"),
    }
    
    all_present = True
    for var_name, var_value in required_vars.items():
        if var_value:
            # Mask sensitive values
            if "KEY" in var_name or "TOKEN" in var_name:
                display_value = var_value[:10] + "..." if len(var_value) > 10 else "***"
            else:
                display_value = var_value
            print(f"   [OK] {var_name}: {display_value}")
        else:
            print(f"   [FAIL] {var_name}: NOT SET")
            all_present = False
    
    if all_present:
        print("\n   [OK] All environment variables configured!")
        return True
    else:
        print("\n   [FAIL] Missing required environment variables!")
        return False


def test_jira_connection():
    """Test 2: Test Jira connection and authentication"""
    print_header("TEST 2: JIRA CONNECTION & AUTHENTICATION")
    
    try:
        from backend.jira.connector import JiraConnector
        
        connector = JiraConnector()
        print(f"   [OK] JiraConnector initialized")
        print(f"   📍 Base URL: {connector.base_url}")
        print(f"   📁 Project: {connector.project}")
        
        # Test connection by fetching open tickets
        print("\n   [SEARCH] Fetching open tickets from your Jira...")
        result = connector.get_open_tickets(max_results=10)
        
        if result.get("success"):
            print(f"   [OK] Connection successful!")
            print(f"   [STATS] Total open tickets: {result.get('total', 0)}")
            
            tickets = result.get("tickets", [])
            if tickets:
                print(f"\n   📋 Your Open Tickets:")
                for i, ticket in enumerate(tickets[:5], 1):
                    print(f"      {i}. [{ticket['ticket_id']}] {ticket['summary']}")
                    print(f"         Status: {ticket['status']} | Priority: {ticket['priority']}")
                
                return True, tickets
            else:
                print(f"   [WARN]  No open tickets found in project {connector.project}")
                print(f"   [IDEA] Create a ticket in Jira to test the workflow")
                return True, []
        else:
            print(f"   [FAIL] Connection failed: {result.get('error')}")
            return False, []
            
    except Exception as e:
        print(f"   [FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, []


def test_fetch_specific_ticket(ticket_id):
    """Test 3: Fetch a specific ticket"""
    print_header(f"TEST 3: FETCH SPECIFIC TICKET - {ticket_id}")
    
    try:
        from backend.jira.connector import JiraConnector
        
        connector = JiraConnector()
        print(f"   [SEARCH] Fetching ticket {ticket_id}...")
        
        result = connector.get_ticket(ticket_id)
        
        if result.get("success"):
            print(f"   [OK] Ticket fetched successfully!")
            print(f"\n   📋 Ticket Details:")
            print(f"      ID: {result.get('ticket_id')}")
            print(f"      Summary: {result.get('summary')}")
            print(f"      Status: {result.get('status')}")
            print(f"      Priority: {result.get('priority')}")
            print(f"      Type: {result.get('issue_type')}")
            print(f"      Assignee: {result.get('assignee')}")
            print(f"      Reporter: {result.get('reporter')}")
            
            description = result.get('description', '')
            if description:
                print(f"\n   [PR] Description:")
                desc_preview = description[:300] + "..." if len(description) > 300 else description
                for line in desc_preview.split('\n'):
                    print(f"      {line}")
            
            return True, result
        else:
            print(f"   [FAIL] Failed to fetch ticket: {result.get('error')}")
            return False, None
            
    except Exception as e:
        print(f"   [FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None


def test_requirement_analyst(ticket_data):
    """Test 4: Test Requirement Analyst Agent"""
    print_header("TEST 4: REQUIREMENT ANALYST AGENT")
    
    try:
        from agents.requirement_analyst.analyzer import RequirementAnalyst
        
        print(f"   [BOT] Initializing Requirement Analyst...")
        analyst = RequirementAnalyst()
        
        print(f"   [STATS] Analyzing ticket: {ticket_data.get('ticket_id')}")
        print(f"   [WAIT] This may take 30-60 seconds...")
        
        analysis = analyst.analyze(ticket_data)
        
        if analysis:
            print(f"   [OK] Analysis completed!")
            print(f"\n   📋 Analysis Results:")
            print(f"      Functional Requirements: {len(analysis.get('functional_requirements', []))}")
            print(f"      Technical Requirements: {len(analysis.get('technical_requirements', []))}")
            print(f"      Implementation Steps: {len(analysis.get('implementation_steps', []))}")
            print(f"      Risk Level: {analysis.get('risk_level', 'N/A')}")
            print(f"      Estimated Complexity: {analysis.get('estimated_complexity', 'N/A')}")
            
            # Show first few requirements
            func_reqs = analysis.get('functional_requirements', [])
            if func_reqs:
                print(f"\n   📌 Sample Functional Requirements:")
                for i, req in enumerate(func_reqs[:3], 1):
                    print(f"      {i}. {req}")
            
            return True, analysis
        else:
            print(f"   [FAIL] Analysis failed or returned empty")
            return False, None
            
    except Exception as e:
        print(f"   [FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None


def test_complete_workflow(ticket_id):
    """Test 5: Run complete workflow with real ticket"""
    print_header(f"TEST 5: COMPLETE WORKFLOW - {ticket_id}")
    
    try:
        from workflows.orchestrator.graph import execute_workflow, get_workflow_status
        
        print(f"   [RUN] Starting complete workflow for {ticket_id}")
        print(f"   [WAIT] This will take several minutes...")
        print(f"\n   Expected Flow:")
        print(f"      1. Requirement Analyst → Analyzes ticket")
        print(f"      2. Developer Agent → Generates code")
        print(f"      3. QA Agent → Validates code")
        print(f"      4. PR Agent → Creates PR description")
        print(f"\n   " + "-" * 66)
        
        # Execute workflow
        final_state = execute_workflow(
            ticket_id=ticket_id,
            max_retries=2,
            verbose=True,
        )
        
        # Get status
        status = get_workflow_status(final_state)
        
        print(f"\n   " + "-" * 66)
        print(f"   [OK] Workflow completed!")
        
        print(f"\n   [STATS] Workflow Results:")
        print(f"      Pipeline Status: {status.get('pipeline_status')}")
        print(f"      Current Stage: {status.get('current_stage')}")
        print(f"      Test Status: {status.get('test_status')}")
        print(f"      Retry Count: {status.get('retry_count')}")
        print(f"      PR Ready: {status.get('pr_ready')}")
        
        print(f"\n   📋 Completed Stages:")
        for stage in final_state.get('completed_stages', []):
            print(f"      [OK] {stage}")
        
        print(f"\n   [CODE] Generated Code:")
        code_files = final_state.get('generated_code', {})
        print(f"      Files: {len(code_files)}")
        if code_files:
            for filename in list(code_files.keys())[:5]:
                print(f"         - {filename}")
        
        print(f"\n   [TEST] Test Results:")
        test_cases = final_state.get('test_cases', [])
        print(f"      Test Cases: {len(test_cases)}")
        print(f"      Status: {final_state.get('test_status', 'N/A')}")
        
        print(f"\n   [PR] PR Information:")
        print(f"      Title: {final_state.get('pr_title', 'N/A')}")
        print(f"      Labels: {', '.join(final_state.get('pr_labels', []))}")
        print(f"      Reviewers: {', '.join(final_state.get('reviewers_suggested', []))}")
        
        # Check if workflow was successful
        success = (
            status.get('pipeline_status') == 'completed' and
            len(code_files) > 0 and
            final_state.get('pr_ready', False)
        )
        
        return success, final_state
        
    except Exception as e:
        print(f"   [FAIL] Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None


def main():
    """Main test execution"""
    print("\n" + "=" * 70)
    print("  JIRA AGENTIC DEVELOPMENT SYSTEM")
    print("  Comprehensive Test Suite - Your Jira Instance")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Environment Configuration
    results['env_config'] = test_environment_config()
    if not results['env_config']:
        print("\n[FAIL] Environment configuration failed. Please check your .env file.")
        return False
    
    # Test 2: Jira Connection
    results['jira_connection'], tickets = test_jira_connection()
    if not results['jira_connection']:
        print("\n[FAIL] Jira connection failed. Please check your credentials.")
        return False
    
    # If no tickets, suggest creating one
    if not tickets:
        print("\n" + "=" * 70)
        print("  [WARN]  NO OPEN TICKETS FOUND")
        print("=" * 70)
        print("  Please create a ticket in your Jira project to test the workflow.")
        print(f"  Project: {os.getenv('JIRA_PROJECT_KEY')}")
        print(f"  URL: {os.getenv('JIRA_BASE_URL')}")
        return False
    
    # Select first ticket for testing
    test_ticket_id = tickets[0]['ticket_id']
    
    # Test 3: Fetch Specific Ticket
    results['fetch_ticket'], ticket_data = test_fetch_specific_ticket(test_ticket_id)
    if not results['fetch_ticket']:
        print(f"\n[FAIL] Failed to fetch ticket {test_ticket_id}")
        return False
    
    # Test 4: Requirement Analyst
    results['requirement_analyst'], analysis = test_requirement_analyst(ticket_data)
    
    # Ask user if they want to run complete workflow
    print("\n" + "=" * 70)
    print("  READY FOR COMPLETE WORKFLOW TEST")
    print("=" * 70)
    print(f"  Ticket: {test_ticket_id}")
    print(f"  Summary: {ticket_data.get('summary')}")
    print(f"\n  [WARN]  This will take several minutes and use LLM API credits.")
    print(f"  The workflow will:")
    print(f"     1. Analyze requirements")
    print(f"     2. Generate code")
    print(f"     3. Create tests")
    print(f"     4. Generate PR description")
    
    user_input = input("\n  Do you want to proceed? (yes/no): ").strip().lower()
    
    if user_input in ['yes', 'y']:
        # Test 5: Complete Workflow
        results['complete_workflow'], workflow_state = test_complete_workflow(test_ticket_id)
    else:
        print("\n  ⏭️  Skipping complete workflow test.")
        results['complete_workflow'] = None
    
    # Final Summary
    print("\n" + "=" * 70)
    print("  FINAL TEST SUMMARY")
    print("=" * 70)
    
    test_results = [
        ("Environment Configuration", results.get('env_config')),
        ("Jira Connection", results.get('jira_connection')),
        ("Fetch Ticket", results.get('fetch_ticket')),
        ("Requirement Analyst", results.get('requirement_analyst')),
        ("Complete Workflow", results.get('complete_workflow')),
    ]
    
    for test_name, result in test_results:
        if result is True:
            print(f"   [OK] {test_name}")
        elif result is False:
            print(f"   [FAIL] {test_name}")
        else:
            print(f"   ⏭️  {test_name} (skipped)")
    
    all_passed = all(r in [True, None] for r in results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  🎉 ALL TESTS PASSED!")
        print("  Your Jira integration is working correctly!")
    else:
        print("  [WARN]  SOME TESTS FAILED")
        print("  Please review the errors above.")
    print("=" * 70 + "\n")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARN]  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[FAIL] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
