"""
backend/auth/protected_example.py
---------------------------------------------
Example of Protected Endpoints
Shows how to protect routes with authentication.

Usage:
  from backend.auth.auth_routes import get_current_active_user
  from backend.auth.protected_example import require_role
  
  @router.get("/protected")
  async def protected_route(current_user: User = Depends(get_current_active_user)):
      return {"message": f"Hello {current_user.username}"}
"""

from fastapi import Depends, HTTPException, status
from backend.auth.auth_routes import User, get_current_active_user


# ─────────────────────────────────────────────
# Role-Based Access Control
# ─────────────────────────────────────────────

def require_role(*allowed_roles: str):
    """
    Dependency factory to require specific roles.
    
    Usage:
        @router.get("/admin-only")
        async def admin_route(user: User = Depends(require_role("admin"))):
            return {"message": "Admin access granted"}
    
    Args:
        *allowed_roles: Roles that are allowed to access the endpoint
    
    Returns:
        Dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}",
            )
        return current_user
    
    return role_checker


# ─────────────────────────────────────────────
# Example Usage
# ─────────────────────────────────────────────

"""
# In your routes file:

from fastapi import APIRouter, Depends
from backend.auth.auth_routes import User, get_current_active_user
from backend.auth.protected_example import require_role

router = APIRouter()

# Protected endpoint - any authenticated user
@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    return {
        "message": f"Hello {current_user.username}",
        "role": current_user.role,
    }

# Admin-only endpoint
@router.get("/admin-only")
async def admin_route(current_user: User = Depends(require_role("admin"))):
    return {
        "message": "Admin access granted",
        "user": current_user.username,
    }

# Developer or Admin endpoint
@router.get("/dev-access")
async def dev_route(current_user: User = Depends(require_role("admin", "developer"))):
    return {
        "message": "Developer access granted",
        "user": current_user.username,
    }
"""
