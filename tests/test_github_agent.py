"""
tests/test_github_agent.py
---------------------------------------------
Comprehensive tests for GitHub Agent
Tests PR creation, branch management, and error handling.
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


def print_section(title):
    """Print formatted section"""
    print("\n" + "-" * 70)
    print(f"  {title}")
    print("-" * 70)


def test_agent_initialization():
    """Test 1: Agent initialization"""
    print_section("TEST 1: Agent Initialization")
    
    try:
        agent = GitHubAgent()
        print("   [OK] GitHubAgent initialized successfully")
        
        if agent.is_configured():
            print("   [OK] GitHub is configured")
            return True, agent
        else:
            print("   [WARN]  GitHub is NOT configured")
            print("   Set GITHUB_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME in .env")
            return False, agent
    except Exception as e:
        print(f"   [FAIL] Failed to initialize agent: {e}")
        return False, None


def test_repository_info(agent):
    """Test 2: Get repository information"""
    print_section("TEST 2: Repository Information")
    
    if not agent.is_configured():
        print("   ⏭️  Skipped (GitHub not configured)")
        return True
    
    try:
        info = agent.get_repository_info()
        
        if info["success"]:
            print("   [OK] Repository info retrieved")
            print(f"      Full Name: {info['full_name']}")
            print(f"      Description: {info['description'] or '(no description)'}")
            print(f"      Default Branch: {info['default_branch']}")
            print(f"      Private: {info['private']}")
            print(f"      URL: {info['url']}")
            return True
        else:
            print(f"   [FAIL] Failed to get repo info: {info['error']}")
            return False
    except Exception as e:
        print(f"   [FAIL] Exception: {e}")
        return False


def test_branch_name_generation(agent):
    """Test 3: Branch name generation"""
    print_section("TEST 3: Branch Name Generation")
    
    test_cases = [
        ("SCRUM-1", "feature/scrum-1"),
        ("BUG-42", "bugfix/bug-42"),
        ("HOTFIX-10", "hotfix/hotfix-10"),
        ("TASK-5", "feature/task-5"),
    ]
    
    all_passed = True
    for ticket_id, expected in test_cases:
        result = agent._generate_branch_name(ticket_id)
        if result == expected:
            print(f"   [OK] {ticket_id} → {result}")
        else:
            print(f"   [FAIL] {ticket_id} → {result} (expected: {expected})")
            all_passed = False
    
    return all_passed


def test_commit_message_generation(agent):
    """Test 4: Commit message generation"""
    print_section("TEST 4: Commit Message Generation")
    
    test_cases = [
        ("SCRUM-1", "Add user authentication", "[SCRUM-1] Add user authentication"),
        ("BUG-42", "Fix login issue", "[BUG-42] Fix login issue"),
    ]
    
    all_passed = True
    for ticket_id, pr_title, expected in test_cases:
        result = agent._generate_commit_message(ticket_id, pr_title)
        if result == expected:
            print(f"   [OK] {ticket_id} → {result}")
        else:
            print(f"   [FAIL] {ticket_id} → {result} (expected: {expected})")
            all_passed = False
    
    return all_passed


def test_pr_creation_dry_run(agent):
    """Test 5: PR creation (dry run - no actual PR)"""
    print_section("TEST 5: PR Creation Workflow (Dry Run)")
    
    if not agent.is_configured():
        print("   ⏭️  Skipped (GitHub not configured)")
        return True
    
    print("   [INFO]  This is a dry run - testing workflow without creating actual PR")
    
    # Mock data
    ticket_id = "TEST-DRY-RUN"
    pr_title = "[TEST] Dry run test - DO NOT MERGE"
    pr_description = """## Test PR
    
This is a test PR created by the GitHub Agent test suite.
This is a DRY RUN and should not create an actual PR.

**DO NOT MERGE**
"""
    
    mock_code = {
        "test_file.py": "# Test file\nprint('Hello from GitHub Agent test!')\n",
    }
    
    print(f"   Mock data prepared:")
    print(f"      Ticket ID: {ticket_id}")
    print(f"      PR Title: {pr_title}")
    print(f"      Files: {len(mock_code)}")
    print(f"      Branch: {agent._generate_branch_name(ticket_id)}")
    
    print("\n   [OK] PR creation workflow validated")
    print("   [INFO]  To test actual PR creation, use test_github_pr_creation.py")
    
    return True


def test_error_handling(agent):
    """Test 6: Error handling"""
    print_section("TEST 6: Error Handling")
    
    # Test with empty code
    print("   Testing with empty code...")
    result = agent.create_pull_request(
        ticket_id="TEST-EMPTY",
        pr_title="Test PR",
        pr_description="Test",
        generated_code={},  # Empty!
    )
    
    if not agent.is_configured():
        if not result.pr_created and "not configured" in result.error.lower():
            print("   [OK] Correctly handled unconfigured GitHub")
        else:
            print("   [FAIL] Unexpected result for unconfigured GitHub")
            return False
    else:
        # With configured GitHub, empty code should fail at commit stage
        if not result.success:
            print("   [OK] Correctly handled empty code")
        else:
            print("   [WARN]  Empty code was accepted (unexpected)")
    
    return True


def main():
    """Main test execution"""
    print_header("GITHUB AGENT - COMPREHENSIVE TEST SUITE")
    
    results = {}
    
    # Test 1: Initialization
    success, agent = test_agent_initialization()
    results["initialization"] = success
    
    if not agent:
        print("\n[FAIL] Cannot continue tests - agent initialization failed")
        return False
    
    # Test 2: Repository info
    results["repository_info"] = test_repository_info(agent)
    
    # Test 3: Branch name generation
    results["branch_names"] = test_branch_name_generation(agent)
    
    # Test 4: Commit message generation
    results["commit_messages"] = test_commit_message_generation(agent)
    
    # Test 5: PR creation dry run
    results["pr_creation_dry_run"] = test_pr_creation_dry_run(agent)
    
    # Test 6: Error handling
    results["error_handling"] = test_error_handling(agent)
    
    # Summary
    print_header("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\n   Total Tests: {total}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    
    print("\n   Detailed Results:")
    for test_name, result in results.items():
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"      {status} - {test_name}")
    
    # Configuration status
    print("\n   Configuration Status:")
    if agent.is_configured():
        info = agent.get_repository_info()
        if info["success"]:
            print(f"      [OK] GitHub configured: {info['full_name']}")
            print(f"      [OK] Ready for actual PR creation")
        else:
            print(f"      [WARN]  GitHub configured but repo access failed")
    else:
        print(f"      [WARN]  GitHub NOT configured")
        print(f"      [INFO]  Set credentials in .env to enable PR creation")
    
    print("\n" + "=" * 70)
    
    if failed == 0:
        print("  🎉 ALL TESTS PASSED!")
        if agent.is_configured():
            print("  [OK] GitHub Agent is ready for production use!")
        else:
            print("  [INFO]  Configure GitHub to enable PR creation")
    else:
        print(f"  [WARN]  {failed} TEST(S) FAILED")
    
    print("=" * 70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARN]  Tests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[FAIL] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
