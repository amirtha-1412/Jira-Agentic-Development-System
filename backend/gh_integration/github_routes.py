"""
backend/github/github_routes.py
---------------------------------------------
GitHub API Routes
REST endpoints for GitHub integration.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from backend.gh_integration.github_client import GitHubClient

router = APIRouter(prefix="/github", tags=["GitHub"])


# ─────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────

class CreatePRRequest(BaseModel):
    title: str
    body: str
    head_branch: str
    base_branch: str = "main"
    labels: Optional[List[str]] = None
    reviewers: Optional[List[str]] = None


class CreateBranchRequest(BaseModel):
    branch_name: str
    from_branch: str = "main"


class CommitFilesRequest(BaseModel):
    branch_name: str
    files: Dict[str, str]  # {file_path: content}
    commit_message: str


class CreatePRWithCodeRequest(BaseModel):
    """
    Complete PR creation: branch + commit + PR
    """
    ticket_id: str
    pr_title: str
    pr_body: str
    generated_code: Dict[str, str]  # {file_path: content}
    base_branch: str = "main"
    labels: Optional[List[str]] = None
    reviewers: Optional[List[str]] = None


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@router.get("/status")
async def github_status():
    """Check GitHub integration status."""
    client = GitHubClient()
    
    if client.is_configured():
        info = client.get_repository_info()
        return {
            "configured": True,
            "repository": info.get("full_name"),
            "default_branch": info.get("default_branch"),
        }
    else:
        return {
            "configured": False,
            "message": "GitHub not configured. Set GITHUB_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME in .env",
        }


@router.get("/repo-info")
async def get_repo_info():
    """Get repository information."""
    client = GitHubClient()
    
    if not client.is_configured():
        raise HTTPException(
            status_code=400,
            detail="GitHub not configured",
        )
    
    info = client.get_repository_info()
    
    if info["success"]:
        return info
    else:
        raise HTTPException(
            status_code=500,
            detail=info["error"],
        )


@router.post("/create-pr")
async def create_pull_request(request: CreatePRRequest):
    """
    Create a pull request.
    
    Note: The branch must already exist with committed changes.
    """
    client = GitHubClient()
    
    if not client.is_configured():
        raise HTTPException(
            status_code=400,
            detail="GitHub not configured",
        )
    
    result = client.create_pull_request(
        title=request.title,
        body=request.body,
        head_branch=request.head_branch,
        base_branch=request.base_branch,
        labels=request.labels,
        reviewers=request.reviewers,
    )
    
    if result["success"]:
        return result
    else:
        raise HTTPException(
            status_code=500,
            detail=result["error"],
        )


@router.post("/create-branch")
async def create_branch(request: CreateBranchRequest):
    """Create a new branch."""
    client = GitHubClient()
    
    if not client.is_configured():
        raise HTTPException(
            status_code=400,
            detail="GitHub not configured",
        )
    
    result = client.create_branch(
        branch_name=request.branch_name,
        from_branch=request.from_branch,
    )
    
    if result["success"]:
        return result
    else:
        raise HTTPException(
            status_code=500,
            detail=result["error"],
        )


@router.post("/commit-files")
async def commit_files(request: CommitFilesRequest):
    """Commit files to a branch."""
    client = GitHubClient()
    
    if not client.is_configured():
        raise HTTPException(
            status_code=400,
            detail="GitHub not configured",
        )
    
    result = client.commit_files(
        branch_name=request.branch_name,
        files=request.files,
        commit_message=request.commit_message,
    )
    
    if result["success"]:
        return result
    else:
        raise HTTPException(
            status_code=500,
            detail=result["error"],
        )


@router.post("/create-pr-with-code")
async def create_pr_with_code(request: CreatePRWithCodeRequest):
    """
    Complete PR creation workflow:
    1. Create branch from base
    2. Commit generated code
    3. Create pull request
    
    This is the main endpoint for automated PR creation.
    """
    client = GitHubClient()
    
    if not client.is_configured():
        return {
            "success": False,
            "error": "GitHub not configured. Set GITHUB_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME in .env",
            "pr_created": False,
        }
    
    # Generate branch name from ticket ID
    branch_name = f"feature/{request.ticket_id.lower()}"
    
    try:
        # Step 1: Create branch
        branch_result = client.create_branch(
            branch_name=branch_name,
            from_branch=request.base_branch,
        )
        
        if not branch_result["success"]:
            # Branch might already exist, try to use it
            if "already exists" not in branch_result["error"]:
                return {
                    "success": False,
                    "error": f"Failed to create branch: {branch_result['error']}",
                    "step": "create_branch",
                }
        
        # Step 2: Commit files
        commit_message = f"[{request.ticket_id}] {request.pr_title}"
        commit_result = client.commit_files(
            branch_name=branch_name,
            files=request.generated_code,
            commit_message=commit_message,
        )
        
        if not commit_result["success"]:
            return {
                "success": False,
                "error": f"Failed to commit files: {commit_result['error']}",
                "step": "commit_files",
            }
        
        # Step 3: Create PR
        pr_result = client.create_pull_request(
            title=request.pr_title,
            body=request.pr_body,
            head_branch=branch_name,
            base_branch=request.base_branch,
            labels=request.labels,
            reviewers=request.reviewers,
        )
        
        if not pr_result["success"]:
            return {
                "success": False,
                "error": f"Failed to create PR: {pr_result['error']}",
                "step": "create_pr",
                "branch_created": True,
                "files_committed": True,
            }
        
        # Success!
        return {
            "success": True,
            "pr_created": True,
            "branch_name": branch_name,
            "commit_sha": commit_result["commit_sha"],
            "files_committed": commit_result["files_committed"],
            "pr_number": pr_result["pr_number"],
            "pr_url": pr_result["pr_url"],
            "pr_state": pr_result["pr_state"],
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }
