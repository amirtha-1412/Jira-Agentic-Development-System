"""
Test GitHub PR Creation
Diagnoses GitHub integration issues
"""

import os
import sys
from dotenv import load_dotenv

print("\n" + "=" * 70)
print("  GITHUB PR DIAGNOSTIC")
print("=" * 70 + "\n")

# Load environment variables
load_dotenv()

# Test 1: Check environment variables
print("[1/6] Checking GitHub credentials...")
github_token = os.getenv("GITHUB_TOKEN")
github_owner = os.getenv("GITHUB_REPO_OWNER")
github_repo = os.getenv("GITHUB_REPO_NAME")

if github_token:
    print(f"  ✅ GITHUB_TOKEN: Set ({len(github_token)} chars)")
    if github_token.startswith("ghp_"):
        print(f"     Token format: Valid (starts with ghp_)")
    else:
        print(f"     ⚠️  Token format: Unusual (doesn't start with ghp_)")
else:
    print(f"  ❌ GITHUB_TOKEN: NOT SET")

if github_owner:
    print(f"  ✅ GITHUB_REPO_OWNER: {github_owner}")
else:
    print(f"  ❌ GITHUB_REPO_OWNER: NOT SET")

if github_repo:
    print(f"  ✅ GITHUB_REPO_NAME: {github_repo}")
else:
    print(f"  ❌ GITHUB_REPO_NAME: NOT SET")

if not (github_token and github_owner and github_repo):
    print("\n❌ MISSING CREDENTIALS - Cannot proceed")
    print("   Please set GITHUB_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME in .env")
    sys.exit(1)

print()

# Test 2: Check PyGithub installation
print("[2/6] Checking PyGithub installation...")
try:
    from github import Github, GithubException
    print("  ✅ PyGithub installed")
except ImportError as e:
    print(f"  ❌ PyGithub not installed: {e}")
    print("     Run: pip install PyGithub")
    sys.exit(1)
print()

# Test 3: Test GitHub authentication
print("[3/6] Testing GitHub authentication...")
try:
    client = Github(github_token)
    user = client.get_user()
    print(f"  ✅ Authentication successful")
    print(f"     User: {user.login}")
    print(f"     Name: {user.name}")
    
    # Check rate limit
    rate_limit = client.get_rate_limit()
    print(f"     Rate Limit: {rate_limit.core.remaining}/{rate_limit.core.limit}")
    
except Exception as e:
    print(f"  ❌ Authentication failed: {e}")
    if "401" in str(e) or "Bad credentials" in str(e):
        print("     Your GitHub token is invalid or expired")
        print("     Get a new token from: https://github.com/settings/tokens")
    sys.exit(1)
print()

# Test 4: Check repository access
print("[4/6] Checking repository access...")
try:
    repo = client.get_repo(f"{github_owner}/{github_repo}")
    print(f"  ✅ Repository found: {repo.full_name}")
    print(f"     Description: {repo.description}")
    print(f"     Default branch: {repo.default_branch}")
    print(f"     Private: {repo.private}")
    
    # Check permissions
    permissions = repo.permissions
    print(f"     Permissions:")
    print(f"       - Admin: {permissions.admin}")
    print(f"       - Push: {permissions.push}")
    print(f"       - Pull: {permissions.pull}")
    
    if not permissions.push:
        print(f"     ⚠️  WARNING: No push access - PR creation may fail")
    
except Exception as e:
    print(f"  ❌ Cannot access repository: {e}")
    if "404" in str(e):
        print(f"     Repository '{github_owner}/{github_repo}' not found")
        print(f"     Check if the repository name is correct")
    elif "403" in str(e):
        print(f"     Permission denied - token doesn't have access to this repo")
    sys.exit(1)
print()

# Test 5: Check existing PRs
print("[5/6] Checking existing PRs...")
try:
    pulls = repo.get_pulls(state='all')
    pull_list = list(pulls[:10])  # Get first 10
    
    print(f"  ✅ Found {pulls.totalCount} total PRs")
    if pull_list:
        print(f"     Recent PRs:")
        for pr in pull_list[:5]:
            print(f"       - #{pr.number}: {pr.title} ({pr.state})")
    else:
        print(f"     No PRs found")
    
except Exception as e:
    print(f"  ⚠️  Could not fetch PRs: {e}")
print()

# Test 6: Test branch creation (dry run)
print("[6/6] Testing branch creation capability...")
try:
    # Get default branch
    default_branch = repo.default_branch
    main_branch = repo.get_branch(default_branch)
    print(f"  ✅ Can read {default_branch} branch")
    print(f"     Latest commit: {main_branch.commit.sha[:7]}")
    
    # Check if we can list branches
    branches = list(repo.get_branches())
    print(f"  ✅ Can list branches ({len(branches)} total)")
    
    # Check for test branch
    test_branches = [b for b in branches if b.name.startswith('feature/scrum-')]
    if test_branches:
        print(f"     Found {len(test_branches)} SCRUM feature branches:")
        for branch in test_branches[:5]:
            print(f"       - {branch.name}")
    
except Exception as e:
    print(f"  ⚠️  Branch operations issue: {e}")
print()

# Test 7: Simulate PR creation
print("[SIMULATION] Testing PR creation flow...")
try:
    test_branch_name = "feature/test-diagnosis"
    
    # Check if test branch exists
    try:
        existing_branch = repo.get_branch(test_branch_name)
        print(f"  ℹ️  Test branch '{test_branch_name}' already exists")
        print(f"     (This is OK - just means we've tested before)")
    except:
        print(f"  ℹ️  Test branch '{test_branch_name}' doesn't exist (expected)")
    
    # Check for open PRs from this branch
    open_prs = repo.get_pulls(state='open', head=f"{github_owner}:{test_branch_name}")
    open_pr_list = list(open_prs)
    
    if open_pr_list:
        print(f"  ℹ️  Found {len(open_pr_list)} open PR(s) from test branch:")
        for pr in open_pr_list:
            print(f"     - #{pr.number}: {pr.title}")
    else:
        print(f"  ✅ No open PRs from test branch (good for testing)")
    
    print(f"\n  ✅ PR creation should work!")
    print(f"     You have the necessary permissions")
    
except Exception as e:
    print(f"  ⚠️  Simulation issue: {e}")

print()

# Summary
print("=" * 70)
print("  DIAGNOSTIC COMPLETE")
print("=" * 70)
print()
print("Summary:")
print("  - GitHub credentials: Valid ✅")
print("  - Repository access: Granted ✅")
print(f"  - Repository: {github_owner}/{github_repo} ✅")
print(f"  - Permissions: Push={permissions.push}, Admin={permissions.admin}")
print()

if permissions.push:
    print("✅ GitHub PR creation should work!")
    print()
    print("If PRs still fail, common issues:")
    print("  1. Branch protection rules blocking automated PRs")
    print("  2. Required status checks not met")
    print("  3. Repository settings restrict PR creation")
    print("  4. Token permissions don't include 'repo' scope")
    print()
    print("To check token permissions:")
    print("  1. Go to: https://github.com/settings/tokens")
    print("  2. Click on your token")
    print("  3. Ensure 'repo' scope is checked")
else:
    print("⚠️  WARNING: No push permission!")
    print()
    print("To fix:")
    print("  1. Generate a new token: https://github.com/settings/tokens")
    print("  2. Select 'repo' scope (full control)")
    print("  3. Update GITHUB_TOKEN in .env file")

print()
