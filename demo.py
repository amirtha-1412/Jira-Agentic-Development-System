"""
demo.py
---------------------------------------------
Hackathon Demo Script
Runs a complete demo of the Jira Agentic Development System
"""

import sys
import io
import time
from datetime import datetime

# Ensure UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def print_banner(text, char="="):
    """Print a formatted banner"""
    width = 70
    print("\n" + char * width)
    print(f"  {text}")
    print(char * width)


def print_stage(stage_num, stage_name, emoji="[RETRY]"):
    """Print stage header"""
    print(f"\n{emoji} Stage {stage_num}: {stage_name}")
    print("-" * 70)


def animate_dots(duration=2):
    """Animate dots for visual effect"""
    for _ in range(duration):
        print(".", end="", flush=True)
        time.sleep(0.5)
    print()


def main():
    """Main demo execution"""
    
    print_banner("🎯 JIRA AGENTIC DEVELOPMENT SYSTEM", "=")
    print("  Hackathon Demo - Live Execution")
    print("  " + "=" * 66)
    
    # Get ticket ID
    print("\n📋 Enter Jira Ticket ID (e.g., SCRUM-1):")
    ticket_id = input("   Ticket ID: ").strip().upper()
    
    if not ticket_id:
        ticket_id = "SCRUM-1"
        print(f"   Using default: {ticket_id}")
    
    print(f"\n[OK] Ticket Selected: {ticket_id}")
    print(f"⏰ Start Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Confirm execution
    print("\n" + "=" * 70)
    print("  Ready to execute workflow?")
    print("  This will:")
    print("    1. Fetch ticket from Jira")
    print("    2. Analyze requirements")
    print("    3. Generate code")
    print("    4. Create tests")
    print("    5. Draft PR")
    print("=" * 70)
    
    input("\n  Press ENTER to start the demo...")
    
    # Execute workflow
    print_banner("[RUN] EXECUTING MULTI-AGENT WORKFLOW")
    
    try:
        from workflows.orchestrator.graph import execute_workflow, get_workflow_status
        
        print(f"\n📍 Initializing workflow for {ticket_id}...")
        animate_dots(1)
        
        print("\n🔗 Connecting to Jira...")
        animate_dots(1)
        
        print("\n[OK] Connection established!")
        print("\n" + "=" * 70)
        print("  AGENT PIPELINE EXECUTION")
        print("=" * 70)
        
        # Execute with verbose output
        start_time = time.time()
        
        result = execute_workflow(
            ticket_id=ticket_id,
            max_retries=2,
            verbose=True
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Get status
        status = get_workflow_status(result)
        
        # Display results
        print("\n" + "=" * 70)
        print("  [OK] WORKFLOW COMPLETED!")
        print("=" * 70)
        
        print(f"\n⏱️  Execution Time: {duration:.1f} seconds")
        print(f"[STATS] Pipeline Status: {status.get('pipeline_status')}")
        print(f"🎯 Current Stage: {status.get('current_stage')}")
        print(f"[RETRY] Retry Count: {status.get('retry_count')}")
        print(f"[OK] Test Status: {status.get('test_status')}")
        print(f"[PR] PR Ready: {status.get('pr_ready')}")
        
        print("\n" + "-" * 70)
        print("  COMPLETED STAGES")
        print("-" * 70)
        for stage in result.get('completed_stages', []):
            print(f"  [OK] {stage.capitalize()}")
        
        print("\n" + "-" * 70)
        print("  GENERATED OUTPUTS")
        print("-" * 70)
        
        # Code files
        code_files = result.get('generated_code', {})
        print(f"\n[CODE] Code Files Generated: {len(code_files)}")
        if code_files:
            for i, filename in enumerate(list(code_files.keys())[:5], 1):
                print(f"   {i}. {filename}")
            if len(code_files) > 5:
                print(f"   ... and {len(code_files) - 5} more")
        
        # Test cases
        test_cases = result.get('test_cases', [])
        print(f"\n[TEST] Test Cases Created: {len(test_cases)}")
        if test_cases:
            for i, test in enumerate(test_cases[:3], 1):
                print(f"   {i}. {test.get('name', 'Test case')}")
            if len(test_cases) > 3:
                print(f"   ... and {len(test_cases) - 3} more")
        
        # Requirements
        func_reqs = result.get('functional_reqs', [])
        tech_reqs = result.get('technical_reqs', [])
        print(f"\n📋 Requirements Extracted:")
        print(f"   Functional: {len(func_reqs)}")
        print(f"   Technical: {len(tech_reqs)}")
        
        # PR Info
        pr_title = result.get('pr_title', 'N/A')
        pr_labels = result.get('pr_labels', [])
        reviewers = result.get('reviewers_suggested', [])
        
        print(f"\n[PR] Pull Request:")
        print(f"   Title: {pr_title[:60]}...")
        print(f"   Labels: {', '.join(pr_labels) if pr_labels else 'None'}")
        print(f"   Reviewers: {', '.join(reviewers) if reviewers else 'None'}")
        
        # Risk assessment
        risk_level = result.get('risk_level', 'N/A')
        print(f"\n[WARN]  Risk Level: {risk_level}")
        
        # Show sample code
        if code_files:
            print("\n" + "=" * 70)
            print("  SAMPLE GENERATED CODE")
            print("=" * 70)
            
            first_file = list(code_files.keys())[0]
            code_content = code_files[first_file]
            
            print(f"\n📄 File: {first_file}")
            print("-" * 70)
            
            # Show first 20 lines
            lines = code_content.split('\n')[:20]
            for line in lines:
                print(line)
            
            if len(code_content.split('\n')) > 20:
                print("\n... (truncated)")
        
        # Show PR description preview
        pr_desc = result.get('pr_description', '')
        if pr_desc:
            print("\n" + "=" * 70)
            print("  PR DESCRIPTION PREVIEW")
            print("=" * 70)
            
            lines = pr_desc.split('\n')[:15]
            for line in lines:
                print(line)
            
            if len(pr_desc.split('\n')) > 15:
                print("\n... (truncated)")
        
        # Success summary
        print("\n" + "=" * 70)
        print("  🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
        print(f"\n[NEW] Summary:")
        print(f"   • Analyzed ticket in {duration:.1f}s")
        print(f"   • Generated {len(code_files)} code files")
        print(f"   • Created {len(test_cases)} test cases")
        print(f"   • Drafted complete PR")
        print(f"   • All stages completed: {', '.join(result.get('completed_stages', []))}")
        
        print(f"\n[IDEA] What would take a developer 2-4 hours was done in {duration/60:.1f} minutes!")
        
        print("\n" + "=" * 70)
        print("  Thank you for watching the demo!")
        print("  Questions? Let's discuss!")
        print("=" * 70 + "\n")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n[WARN]  Demo interrupted by user.")
        return False
        
    except Exception as e:
        print(f"\n\n[FAIL] Demo failed: {str(e)}")
        print("\n[IDEA] Troubleshooting:")
        print("   1. Check Jira connection: python test_jira_only.py")
        print("   2. Verify API limits: python fix_issues.py")
        print("   3. Check ticket exists in Jira")
        
        import traceback
        print("\n📋 Error Details:")
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n\n[FAIL] Unexpected error: {str(e)}")
        sys.exit(1)
