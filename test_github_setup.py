"""
Test GitHub Setup and Diagnose Issues
Run this to check your GitHub configuration and identify problems.
"""

import os
from dotenv import load_dotenv
from github import Github, GithubException

load_dotenv()

print("\n" + "=" * 70)
print("  GITHUB SETUP DIAGNOSTIC")
print("=" * 70)

# Step 1: Check environment variables
print("\n[Step 1] Checking environment variables...")
token = os.getenv("GITHUB_TOKEN")
owner = os.getenv("GITHUB_REPO_OWNER")
repo_name = os.getenv("GITHUB_REPO_NAME")

if not token:
    print("[FAIL] GITHUB_TOKEN not set in .env")
    exit(1)
else:
    print(f"[OK] GITHUB_TOKEN: {token[:10]}...")

if not owner:
    print("[FAIL] GITHUB_REPO_OWNER not set in .env")
    exit(1)
else:
    print(f"[OK] GITHUB_REPO_OWNER: {owner}")

if not repo_name:
    print("[FAIL] GITHUB_REPO_NAME not set in .env")
    exit(1)
else:
    print(f"[OK] GITHUB_REPO_NAME: {repo_name}")

# Step 2: Test GitHub connection
print("\n[Step 2] Testing GitHub connection...")
try:
    client = Github(token)
    user = client.get_user()
    print(f"[OK] Connected as: {user.login}")
except Exception as e:
    print(f"[FAIL] Failed to connect: {e}")
    exit(1)

# Step 3: Check repository access
print("\n[Step 3] Checking repository access...")
try:
    repo = client.get_repo(f"{owner}/{repo_name}")
    print(f"[OK] Repository found: {repo.full_name}")
    print(f"   Description: {repo.description or 'No description'}")
    print(f"   Private: {repo.private}")
    print(f"   URL: {repo.html_url}")
except Exception as e:
    print(f"[FAIL] Cannot access repository: {e}")
    print(f"\n[IDEA] Possible issues:")
    print(f"   1. Repository doesn't exist: {owner}/{repo_name}")
    print(f"   2. Token doesn't have access to this repository")
    print(f"   3. Repository name is incorrect")
    exit(1)

# Step 4: Check default branch
print("\n[Step 4] Checking default branch...")
try:
    default_branch = repo.default_branch
    print(f"[OK] Default branch: {default_branch}")
    
    # Check if it's 'main' or 'master'
    if default_branch not in ['main', 'master']:
        print(f"[WARN]  WARNING: Default branch is '{default_branch}', not 'main' or 'master'")
        print(f"   You may need to update base_branch in your code")
except Exception as e:
    print(f"[FAIL] Cannot get default branch: {e}")

# Step 5: Check permissions
print("\n[Step 5] Checking repository permissions...")
try:
    permissions = repo.permissions
    print(f"   Admin: {permissions.admin}")
    print(f"   Push: {permissions.push}")
    print(f"   Pull: {permissions.pull}")
    
    if not permissions.push:
        print(f"[FAIL] ERROR: Token doesn't have PUSH permission!")
        print(f"   You need push access to create branches and PRs")
        print(f"\n[IDEA] To fix:")
        print(f"   1. Go to GitHub → Settings → Developer settings → Personal access tokens")
        print(f"   2. Create new token with 'repo' scope (full control)")
        print(f"   3. Update GITHUB_TOKEN in .env")
        exit(1)
    else:
        print(f"[OK] Token has push permission")
except Exception as e:
    print(f"[WARN]  Cannot check permissions: {e}")

# Step 6: List existing branches
print("\n[Step 6] Listing branches...")
try:
    branches = list(repo.get_branches())
    print(f"[OK] Found {len(branches)} branch(es):")
    for branch in branches[:5]:  # Show first 5
        print(f"   - {branch.name}")
    if len(branches) > 5:
        print(f"   ... and {len(branches) - 5} more")
except Exception as e:
    print(f"[WARN]  Cannot list branches: {e}")

# Step 7: Check for existing PRs
print("\n[Step 7] Checking existing pull requests...")
try:
    open_prs = list(repo.get_pulls(state='open'))
    print(f"[OK] Found {len(open_prs)} open PR(s)")
    if open_prs:
        print(f"   Recent PRs:")
        for pr in open_prs[:3]:
            print(f"   - #{pr.number}: {pr.title}")
            print(f"     Branch: {pr.head.ref} → {pr.base.ref}")
except Exception as e:
    print(f"[WARN]  Cannot list PRs: {e}")

# Step 8: Test branch creation (dry run)
print("\n[Step 8] Testing branch creation capability...")
test_branch_name = "test-diagnostic-branch"
try:
    # Check if test branch already exists
    try:
        existing_ref = repo.get_git_ref(f"heads/{test_branch_name}")
        print(f"[WARN]  Test branch '{test_branch_name}' already exists")
        print(f"   This is OK - it means branch creation works")
    except GithubException as e:
        if e.status == 404:
            print(f"[OK] Test branch doesn't exist (good)")
            print(f"   Branch creation should work")
        else:
            raise
except Exception as e:
    print(f"[WARN]  Cannot test branch creation: {e}")

# Summary
print("\n" + "=" * 70)
print("  DIAGNOSTIC SUMMARY")
print("=" * 70)

print(f"\n[OK] GitHub Configuration:")
print(f"   Repository: {owner}/{repo_name}")
print(f"   Default Branch: {default_branch}")
print(f"   Has Push Access: {permissions.push if 'permissions' in locals() else 'Unknown'}")

print(f"\n[IDEA] Common Issues and Solutions:")
print(f"\n1. 'Validation Failed' Error:")
print(f"   - Make sure base branch exists (use '{default_branch}' not 'main')")
print(f"   - Ensure branch has commits before creating PR")
print(f"   - Check if PR already exists for that branch")

print(f"\n2. 'No commits between branches' Error:")
print(f"   - Branch was created but no files were committed")
print(f"   - Check commit_files() is working correctly")

print(f"\n3. 'Resource not accessible' Error:")
print(f"   - Token doesn't have 'repo' scope")
print(f"   - Repository is private and token doesn't have access")

print(f"\n4. Branch already exists:")
print(f"   - Delete old branch or use a different ticket ID")
print(f"   - Or update code to handle existing branches")

print("\n" + "=" * 70)
print("  [DONE] Diagnostic complete")
print("=" * 70 + "\n")
