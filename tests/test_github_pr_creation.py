"""
tests/test_github_pr_creation.py
---------------------------------------------
REAL GitHub PR Creation Test
[WARN]  WARNING: This will create an ACTUAL pull request in your GitHub repository!
"""

import sys
import io
from agents.github_agent.github_agent import GitHubAgent

# Ensure UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    """Main test execution"""
    print_header("GITHUB PR CREATION - REAL TEST")
    
    print("\n[WARN]  WARNING: This will create an ACTUAL pull request!")
    print("   Repository: Check your .env file")
    print("   Branch: feature/test-github-agent")
    print("   Files: 2 test files")
    
    # Initialize agent
    print("\n📋 Initializing GitHub Agent...")
    agent = GitHubAgent()
    
    if not agent.is_configured():
        print("\n[FAIL] GitHub is NOT configured!")
        print("   Set GITHUB_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME in .env")
        return False
    
    # Get repo info
    info = agent.get_repository_info()
    if not info["success"]:
        print(f"\n[FAIL] Failed to access repository: {info['error']}")
        return False
    
    print(f"\n[OK] GitHub configured")
    print(f"   Repository: {info['full_name']}")
    print(f"   Default Branch: {info['default_branch']}")
    print(f"   URL: {info['url']}")
    
    # Confirm with user
    print("\n" + "=" * 70)
    print("  CONFIRMATION REQUIRED")
    print("=" * 70)
    print(f"\n   This will create a REAL pull request in:")
    print(f"   📁 {info['full_name']}")
    print(f"   🌿 Branch: feature/test-github-agent")
    print(f"   [PR] Files: 2 test files")
    print(f"   🔗 PR will be visible at: {info['url']}/pulls")
    
    print("\n   The PR will include:")
    print("      - test_file_1.py (Hello World)")
    print("      - test_file_2.md (Test documentation)")
    
    print("\n   You can:")
    print("      - Review the PR in GitHub")
    print("      - Merge it if you want")
    print("      - Close it without merging")
    print("      - Delete the branch after closing")
    
    user_input = input("\n   Do you want to proceed? (yes/no): ").strip().lower()
    
    if user_input not in ['yes', 'y']:
        print("\n   ⏭️  Test cancelled by user.")
        return False
    
    # Prepare test data
    print("\n" + "=" * 70)
    print("  CREATING PULL REQUEST")
    print("=" * 70)
    
    ticket_id = "TEST-GITHUB-AGENT"
    pr_title = "[TEST] GitHub Agent - Automated PR Creation Test"
    pr_description = """## [TEST] Test Pull Request

This PR was created by the **GitHub Agent** test suite to verify automated PR creation functionality.

### What's in this PR:
- [OK] `test_file_1.py` - Simple Python test file
- [OK] `test_file_2.md` - Test documentation

### Purpose:
This is a **test PR** to verify that the GitHub Agent can:
1. Create branches automatically
2. Commit files to the branch
3. Create pull requests with descriptions
4. Add labels and metadata

### What to do:
- [OK] Review the PR
- [OK] Check the files
- [OK] Merge if you want (or close without merging)
- [OK] Delete the branch after closing

---

**Created by**: GitHub Agent Test Suite  
**Ticket**: TEST-GITHUB-AGENT  
**Status**: [OK] Automated PR Creation Working!
"""
    
    generated_code = {
        "test_file_1.py": """#!/usr/bin/env python3
\"\"\"
test_file_1.py
Test file created by GitHub Agent
\"\"\"

def hello_world():
    \"\"\"Simple hello world function\"\"\"
    print("Hello from GitHub Agent!")
    print("Automated PR creation is working! 🎉")

if __name__ == "__main__":
    hello_world()
""",
        "test_file_2.md": """# GitHub Agent Test

This file was created by the GitHub Agent test suite.

## Purpose

To verify that the GitHub Agent can:
- [OK] Create branches
- [OK] Commit files
- [OK] Create pull requests

## Status

[OK] **Working!** The GitHub Agent successfully created this PR.

## Next Steps

1. Review this PR
2. Merge or close it
3. Delete the branch if needed

---

**Created**: Automatically by GitHub Agent  
**Test**: Successful [OK]
""",
    }
    
    pr_labels = ["test", "automated", "github-agent"]
    
    print(f"\n   Ticket ID: {ticket_id}")
    print(f"   PR Title: {pr_title}")
    print(f"   Files: {len(generated_code)}")
    print(f"   Labels: {', '.join(pr_labels)}")
    
    # Create PR
    print("\n   [RUN] Creating pull request...")
    result = agent.create_pull_request(
        ticket_id=ticket_id,
        pr_title=pr_title,
        pr_description=pr_description,
        generated_code=generated_code,
        pr_labels=pr_labels,
        reviewers_suggested=None,  # No reviewers for test
        base_branch=info['default_branch'],
    )
    
    # Display results
    print("\n" + "=" * 70)
    print("  RESULTS")
    print("=" * 70)
    
    if result.success and result.pr_created:
        print("\n   🎉 SUCCESS! Pull request created!")
        print(f"\n   [STATS] PR Details:")
        print(f"      PR Number: #{result.pr_number}")
        print(f"      PR URL: {result.pr_url}")
        print(f"      Branch: {result.branch_name}")
        print(f"      Commit SHA: {result.commit_sha[:8]}...")
        print(f"      Files Committed: {result.files_committed}")
        print(f"      State: {result.pr_state}")
        
        print(f"\n   🔗 View your PR:")
        print(f"      {result.pr_url}")
        
        print(f"\n   [OK] GitHub Agent is working perfectly!")
        print(f"   [OK] Automated PR creation is functional!")
        
        print(f"\n   [PR] Next steps:")
        print(f"      1. Open the PR URL in your browser")
        print(f"      2. Review the files")
        print(f"      3. Merge or close the PR")
        print(f"      4. Delete the branch: {result.branch_name}")
        
        return True
    else:
        print(f"\n   [FAIL] Failed to create PR")
        print(f"      Error: {result.error}")
        
        if result.branch_name:
            print(f"\n   [INFO]  Branch was created: {result.branch_name}")
        if result.commit_sha:
            print(f"   [INFO]  Files were committed: {result.commit_sha[:8]}...")
        
        return False


if __name__ == "__main__":
    try:
        print("\n" + "=" * 70)
        print("  [WARN]  REAL GITHUB PR CREATION TEST")
        print("  This will create an ACTUAL pull request!")
        print("=" * 70)
        
        success = main()
        
        print("\n" + "=" * 70)
        if success:
            print("  [OK] TEST PASSED - PR CREATED SUCCESSFULLY!")
        else:
            print("  [FAIL] TEST FAILED OR CANCELLED")
        print("=" * 70 + "\n")
        
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARN]  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[FAIL] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
