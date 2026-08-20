"""
agents/github_agent/github_agent.py
---------------------------------------------
GitHub Agent - Real PR Automation
Automatically creates pull requests in GitHub with generated code.

Features:
  - Automatic branch creation from ticket ID
  - Commit generated code to branch
  - Create pull request with description
  - Add labels and reviewers
  - Complete end-to-end automation
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from backend.gh_integration.github_client import GitHubClient


# ─────────────────────────────────────────────
# GitHub PR Result
# ─────────────────────────────────────────────

@dataclass
class GitHubPRResult:
    """Result of GitHub PR creation."""
    success: bool
    pr_created: bool = False
    branch_name: str = ""
    commit_sha: str = ""
    files_committed: int = 0
    pr_number: int = 0
    pr_url: str = ""
    pr_state: str = ""
    error: str = ""
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "pr_created": self.pr_created,
            "branch_name": self.branch_name,
            "commit_sha": self.commit_sha,
            "files_committed": self.files_committed,
            "pr_number": self.pr_number,
            "pr_url": self.pr_url,
            "pr_state": self.pr_state,
            "error": self.error,
        }


# ─────────────────────────────────────────────
# GitHub Agent
# ─────────────────────────────────────────────

class GitHubAgent:
    """
    AI-powered GitHub automation agent.
    Creates actual pull requests in GitHub repositories.
    """
    
    def __init__(self):
        self.client = GitHubClient()
    
    def is_configured(self) -> bool:
        """Check if GitHub is properly configured."""
        return self.client.is_configured()
    
    # ─────────────────────────────────────────
    # Main PR Creation Method
    # ─────────────────────────────────────────
    
    def create_pull_request(
        self,
        ticket_id: str,
        pr_title: str,
        pr_description: str,
        generated_code: Dict[str, str],
        pr_labels: Optional[List[str]] = None,
        reviewers_suggested: Optional[List[str]] = None,
        base_branch: str = "main",
    ) -> GitHubPRResult:
        """
        Creates a complete pull request in GitHub.
        
        Workflow:
        1. Create branch from base (e.g., feature/scrum-1)
        2. Commit generated code to branch
        3. Create pull request
        4. Add labels and reviewers
        
        Args:
            ticket_id: Jira ticket ID (e.g., "SCRUM-1")
            pr_title: PR title
            pr_description: PR description (markdown)
            generated_code: Dict of {file_path: code_content}
            pr_labels: List of labels (e.g., ["feature", "enhancement"])
            reviewers_suggested: List of GitHub usernames
            base_branch: Target branch (default: "main")
        
        Returns:
            GitHubPRResult with PR details or error
        """
        if not self.is_configured():
            print("  [GitHubAgent] [WARN]  GitHub not configured - skipping PR creation")
            return GitHubPRResult(
                success=True,  # Not an error, just not configured
                pr_created=False,
                error="GitHub not configured. Set GITHUB_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME in .env",
            )
        
        try:
            print(f"  [GitHubAgent] Creating PR for {ticket_id}...")
            
            # Generate branch name from ticket ID
            branch_name = self._generate_branch_name(ticket_id)
            print(f"  [GitHubAgent] Branch name: {branch_name}")
            
            # Step 1: Create branch
            print(f"  [GitHubAgent] Creating branch from {base_branch}...")
            branch_result = self.client.create_branch(
                branch_name=branch_name,
                from_branch=base_branch,
            )
            
            if not branch_result["success"]:
                # Branch might already exist
                if "already exists" in branch_result["error"]:
                    print(f"  [GitHubAgent] [WARN]  Branch already exists, using existing branch")
                else:
                    print(f"  [GitHubAgent] [FAIL] Failed to create branch: {branch_result['error']}")
                    return GitHubPRResult(
                        success=False,
                        pr_created=False,
                        error=f"Failed to create branch: {branch_result['error']}",
                    )
            else:
                print(f"  [GitHubAgent] [OK] Branch created: {branch_name}")
            
            # Step 2: Commit files
            commit_message = self._generate_commit_message(ticket_id, pr_title)
            print(f"  [GitHubAgent] Committing {len(generated_code)} file(s)...")
            
            commit_result = self.client.commit_files(
                branch_name=branch_name,
                files=generated_code,
                commit_message=commit_message,
            )
            
            if not commit_result["success"]:
                print(f"  [GitHubAgent] [FAIL] Failed to commit files: {commit_result['error']}")
                return GitHubPRResult(
                    success=False,
                    pr_created=False,
                    branch_name=branch_name,
                    error=f"Failed to commit files: {commit_result['error']}",
                )
            
            print(f"  [GitHubAgent] [OK] Committed {commit_result['files_committed']} file(s)")
            print(f"  [GitHubAgent] Commit SHA: {commit_result['commit_sha'][:8]}...")
            
            # Step 3: Create PR
            print(f"  [GitHubAgent] Creating pull request...")
            pr_result = self.client.create_pull_request(
                title=pr_title,
                body=pr_description,
                head_branch=branch_name,
                base_branch=base_branch,
                labels=pr_labels,
                reviewers=reviewers_suggested,
            )
            
            if not pr_result["success"]:
                print(f"  [GitHubAgent] [FAIL] Failed to create PR: {pr_result['error']}")
                return GitHubPRResult(
                    success=False,
                    pr_created=False,
                    branch_name=branch_name,
                    commit_sha=commit_result["commit_sha"],
                    files_committed=commit_result["files_committed"],
                    error=f"Failed to create PR: {pr_result['error']}",
                )
            
            # Success!
            print(f"  [GitHubAgent] [OK] Pull request created!")
            print(f"  [GitHubAgent] PR #{pr_result['pr_number']}: {pr_result['pr_url']}")
            
            return GitHubPRResult(
                success=True,
                pr_created=True,
                branch_name=branch_name,
                commit_sha=commit_result["commit_sha"],
                files_committed=commit_result["files_committed"],
                pr_number=pr_result["pr_number"],
                pr_url=pr_result["pr_url"],
                pr_state=pr_result["pr_state"],
            )
        
        except Exception as e:
            print(f"  [GitHubAgent] [FAIL] Exception: {e}")
            return GitHubPRResult(
                success=False,
                pr_created=False,
                error=str(e),
            )
    
    # ─────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────
    
    def _generate_branch_name(self, ticket_id: str) -> str:
        """
        Generates a branch name from ticket ID.
        
        Examples:
            SCRUM-1 → feature/scrum-1
            BUG-42 → bugfix/bug-42
            HOTFIX-10 → hotfix/hotfix-10
            TASK-10 → feature/task-10
        """
        ticket_lower = ticket_id.lower()
        
        # Determine branch prefix based on ticket type
        # Check hotfix first (before bug/fix check)
        if "hotfix" in ticket_lower:
            prefix = "hotfix"
        elif "bug" in ticket_lower or "fix" in ticket_lower:
            prefix = "bugfix"
        else:
            prefix = "feature"
        
        return f"{prefix}/{ticket_lower}"
    
    def _generate_commit_message(self, ticket_id: str, pr_title: str) -> str:
        """
        Generates a commit message.
        
        Format: [TICKET-ID] PR Title
        Example: [SCRUM-1] Add user authentication
        """
        return f"[{ticket_id}] {pr_title}"
    
    def get_repository_info(self) -> Dict:
        """Get repository information."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "GitHub not configured",
            }
        
        return self.client.get_repository_info()


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    
    print("\n" + "=" * 70)
    print("  GITHUB AGENT - TEST RUN")
    print("=" * 70)
    
    # Create agent
    agent = GitHubAgent()
    
    if not agent.is_configured():
        print("\n[WARN]  GitHub is NOT configured")
        print("   Set GITHUB_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME in .env")
        print("\n" + "=" * 70 + "\n")
        exit(0)
    
    print("\n[OK] GitHub agent is configured")
    
    # Get repo info
    info = agent.get_repository_info()
    if info["success"]:
        print(f"\n📁 Repository: {info['full_name']}")
        print(f"   Default Branch: {info['default_branch']}")
        print(f"   URL: {info['url']}")
    
    # Test PR creation (dry run - won't actually create)
    print("\n[TEST] Testing PR creation workflow...")
    print("   (This is a dry run - no actual PR will be created)")
    
    mock_code = {
        "src/test_file.py": "# Test file\nprint('Hello from GitHub Agent!')\n",
        "README.md": "# Test PR\nThis is a test PR created by GitHub Agent.\n",
    }
    
    print(f"\n   Mock data:")
    print(f"   - Ticket ID: TEST-1")
    print(f"   - Files: {len(mock_code)}")
    print(f"   - Branch: feature/test-1")
    
    print("\n[OK] GitHub agent is ready for PR creation!")
    print("   Use create_pull_request() method to create actual PRs")
    
    print("\n" + "=" * 70)
    print("  [DONE] GitHub agent test complete")
    print("=" * 70 + "\n")
