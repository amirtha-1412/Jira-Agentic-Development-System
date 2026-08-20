"""
backend/auth/auth_routes.py
---------------------------------------------
Authentication Routes - Login & Token Management
Provides secure login and token endpoints.

Endpoints:
  POST /auth/login - Login with username/password
  GET /auth/me - Get current user info
  POST /auth/refresh - Refresh access token
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta

from backend.auth.auth_utils import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    get_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_in: int


class User(BaseModel):
    """User model."""
    username: str
    email: str
    full_name: str
    role: str
    disabled: bool = False


class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str


# ─────────────────────────────────────────────
# OAuth2 Configuration
# ─────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ─────────────────────────────────────────────
# Dependency: Get Current User
# ─────────────────────────────────────────────

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
    
    Returns:
        Current user
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # Get username from token
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    # Get user from database
    user = get_user(username)
    if user is None:
        raise credentials_exception
    
    # Check if user is disabled
    if user.get("disabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    return User(**user)


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user.
    
    Args:
        current_user: Current user from get_current_user
    
    Returns:
        Current active user
    
    Raises:
        HTTPException: If user is disabled
    """
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return current_user


# ─────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint - authenticate user and return JWT token.
    
    Args:
        form_data: OAuth2 form with username and password
    
    Returns:
        JWT access token
    
    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate user
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
    }


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current user information
    """
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_active_user)):
    """
    Refresh access token.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        New JWT access token
    """
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username},
        expires_delta=access_token_expires,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint (no authentication required).
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "version": "1.0.0",
    }
