"""
backend/auth/auth_utils.py
---------------------------------------------
Authentication Utilities - JWT & Password Hashing
Provides secure authentication with JWT tokens.

Features:
  - Password hashing with bcrypt
  - JWT token generation and validation
  - Token expiration handling
  - Secure password verification
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
import os

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ─────────────────────────────────────────────
# Password Hashing
# ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    # Convert password to bytes and hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
    
    Returns:
        True if password matches, False otherwise
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ─────────────────────────────────────────────
# JWT Token Management
# ─────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in token (e.g., {"sub": "username"})
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token data if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ─────────────────────────────────────────────
# User Database (In-Memory for Demo)
# ─────────────────────────────────────────────

# In production, replace with actual database
USERS_DB = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "hashed_password": hash_password("admin123"),  # Default password
        "disabled": False,
        "role": "admin",
    },
    "developer": {
        "username": "developer",
        "email": "dev@example.com",
        "full_name": "Developer User",
        "hashed_password": hash_password("developer123"),  # Default password
        "disabled": False,
        "role": "developer",
    },
    "viewer": {
        "username": "viewer",
        "email": "viewer@example.com",
        "full_name": "Viewer User",
        "hashed_password": hash_password("viewer123"),  # Default password
        "disabled": False,
        "role": "viewer",
    },
}


def get_user(username: str) -> Optional[dict]:
    """
    Get user from database.
    
    Args:
        username: Username to lookup
    
    Returns:
        User dict if found, None otherwise
    """
    return USERS_DB.get(username)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: Username
        password: Plain text password
    
    Returns:
        User dict if authenticated, None otherwise
    """
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    if user.get("disabled"):
        return None
    return user


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  AUTHENTICATION UTILITIES - TEST")
    print("=" * 70)
    
    # Test password hashing
    print("\n[TEST] Password Hashing:")
    password = "test123"
    hashed = hash_password(password)
    print(f"  Original: {password}")
    print(f"  Hashed: {hashed[:50]}...")
    print(f"  Verify correct: {verify_password(password, hashed)}")
    print(f"  Verify wrong: {verify_password('wrong', hashed)}")
    
    # Test JWT token
    print("\n[TEST] JWT Token:")
    token = create_access_token({"sub": "testuser"})
    print(f"  Token: {token[:50]}...")
    decoded = decode_access_token(token)
    print(f"  Decoded: {decoded}")
    
    # Test user authentication
    print("\n[TEST] User Authentication:")
    user = authenticate_user("admin", "admin123")
    print(f"  Admin login: {'[OK] Success' if user else '[FAIL] Failed'}")
    user = authenticate_user("admin", "wrong")
    print(f"  Wrong password: {'[FAIL] Should fail' if not user else '[OK] Unexpected success'}")
    
    print("\n[INFO] Default Users:")
    for username, user_data in USERS_DB.items():
        print(f"  - {username}: password = {username}123, role = {user_data['role']}")
    
    print("\n" + "=" * 70 + "\n")
