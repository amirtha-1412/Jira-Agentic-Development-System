"""
backend/github/github_client.py
---------------------------------------------
GitHub API Integration
Creates actual pull requests in GitHub repositories.
"""

import os
from typing import Optional, Dict, List
from github import Github, GithubException, InputGitTreeElement
from dotenv import load_dotenv

load_dotenv()


class GitHubClient:
    """
    GitHub API client for creating pull requests.
    """
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo_owner = os.getenv("GITHUB_REPO_OWNER")
        self.repo_name = os.getenv("GITHUB_REPO_NAME")
        
        if not self.token:
            print("[WARN] GITHUB_TOKEN not set. PR creation will be disabled.")
            self.client = None
            self.repo = None
        else:
            try:
                self.client = Github(self.token)
                self.repo = self.client.get_repo(f"{self.repo_owner}/{self.repo_name}")
                print(f"[OK] GitHub client initialized for {self.repo_owner}/{self.repo_name}")
            except Exception as e:
                print(f"[ERROR] Failed to initialize GitHub client: {e}")
                self.client = None
                self.repo = None
    
    def is_configured(self) -> bool:
        """Check if GitHub is properly configured."""
        return self.client is not None and self.repo is not None
    
    def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        labels: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None,
    ) -> Dict:
        """
        Creates a pull request in GitHub.
        
        Args:
            title: PR title
            body: PR description (markdown)
            head_branch: Source branch (e.g., "feature/add-login")
            base_branch: Target branch (default: "main")
            labels: List of label names
            reviewers: List of GitHub usernames to request review
        
        Returns:
            dict with PR details or error
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "GitHub not configured. Set GITHUB_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME in .env",
            }
        
        try:
            # Check if PR already exists for this branch
            existing_prs = self.repo.get_pulls(state='open', head=f"{self.repo_owner}:{head_branch}", base=base_branch)
            existing_pr_list = list(existing_prs)
            
            if existing_pr_list:
                # PR already exists
                existing_pr = existing_pr_list[0]
                print(f"[WARN]  PR already exists for branch {head_branch}: #{existing_pr.number}")
                return {
                    "success": True,
                    "pr_number": existing_pr.number,
                    "pr_url": existing_pr.html_url,
                    "pr_state": existing_pr.state,
                    "created_at": existing_pr.created_at.isoformat(),
                    "note": "PR already exists - returning existing PR",
                }
            
            # Create pull request
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch,
            )
            
            # Add labels if provided
            if labels:
                try:
                    pr.add_to_labels(*labels)
                except GithubException as e:
                    print(f"[WARN]  Failed to add labels: {e}")
            
            # Request reviewers if provided
            if reviewers:
                try:
                    pr.create_review_request(reviewers=reviewers)
                except GithubException as e:
                    print(f"[WARN]  Failed to request reviewers: {e}")
            
            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "pr_state": pr.state,
                "created_at": pr.created_at.isoformat(),
            }
        
        except GithubException as e:
            return {
                "success": False,
                "error": f"GitHub API error: {e.data.get('message', str(e))}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }
    
    def create_branch(
        self,
        branch_name: str,
        from_branch: str = "main",
    ) -> Dict:
        """
        Creates a new branch in the repository.
        
        Args:
            branch_name: Name of the new branch
            from_branch: Source branch to branch from
        
        Returns:
            dict with branch details or error
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "GitHub not configured",
            }
        
        try:
            # Get the source branch reference
            source_ref = self.repo.get_git_ref(f"heads/{from_branch}")
            source_sha = source_ref.object.sha
            
            # Create new branch
            new_ref = self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=source_sha,
            )
            
            return {
                "success": True,
                "branch_name": branch_name,
                "sha": new_ref.object.sha,
            }
        
        except GithubException as e:
            if e.status == 422:
                return {
                    "success": False,
                    "error": f"Branch '{branch_name}' already exists",
                }
            return {
                "success": False,
                "error": f"GitHub API error: {e.data.get('message', str(e))}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }
    
    def commit_files(
        self,
        branch_name: str,
        files: Dict[str, str],
        commit_message: str,
    ) -> Dict:
        """
        Commits multiple files to a branch.
        
        Args:
            branch_name: Target branch
            files: Dict of {file_path: file_content}
            commit_message: Commit message
        
        Returns:
            dict with commit details or error
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "GitHub not configured",
            }
        
        try:
            # Get branch reference
            ref = self.repo.get_git_ref(f"heads/{branch_name}")
            base_tree = self.repo.get_git_tree(ref.object.sha)
            
            # Create blobs for each file
            tree_elements = []
            for file_path, content in files.items():
                blob = self.repo.create_git_blob(content, "utf-8")
                element = InputGitTreeElement(
                    path=file_path,
                    mode="100644",  # Regular file
                    type="blob",
                    sha=blob.sha
                )
                tree_elements.append(element)
            
            # Create tree
            tree = self.repo.create_git_tree(tree_elements, base_tree)
            
            # Create commit
            parent = self.repo.get_git_commit(ref.object.sha)
            commit = self.repo.create_git_commit(
                message=commit_message,
                tree=tree,
                parents=[parent],
            )
            
            # Update branch reference
            ref.edit(commit.sha)
            
            return {
                "success": True,
                "commit_sha": commit.sha,
                "files_committed": len(files),
            }
        
        except GithubException as e:
            return {
                "success": False,
                "error": f"GitHub API error: {e.data.get('message', str(e))}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }
    
    def get_repository_info(self) -> Dict:
        """Get repository information."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "GitHub not configured",
            }
        
        try:
            return {
                "success": True,
                "name": self.repo.name,
                "full_name": self.repo.full_name,
                "description": self.repo.description,
                "default_branch": self.repo.default_branch,
                "private": self.repo.private,
                "url": self.repo.html_url,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  GITHUB CLIENT - TEST")
    print("=" * 70)
    
    client = GitHubClient()
    
    if client.is_configured():
        print("[OK] GitHub client is configured")
        
        # Get repo info
        info = client.get_repository_info()
        if info["success"]:
            print(f"[OK] Repository  : {info['full_name']}")
            print(f"     Description : {info['description']}")
            print(f"     Branch      : {info['default_branch']}")
            print(f"     Private     : {info['private']}")
            print(f"     URL         : {info['url']}")
        else:
            print(f"[FAIL] Repo info: {info['error']}")
    else:
        print("[WARN] GitHub client is NOT configured")
        print("   Set GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME in .env")
    
    print("\n" + "=" * 70 + "\n")
