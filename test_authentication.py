"""
test_authentication.py
---------------------------------------------
Test Authentication System
Tests login, token validation, and protected endpoints.
"""

import requests
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Base URL
BASE_URL = "http://localhost:8000"

# Test users
USERS = {
    "admin": {"username": "admin", "password": "admin123"},
    "developer": {"username": "developer", "password": "dev123"},
    "viewer": {"username": "viewer", "password": "view123"},
}


def test_health_check():
    """Test health check endpoint (no auth required)."""
    print("\n" + "=" * 70)
    print("  TEST 1: Health Check (No Auth)")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/health")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        if response.status_code == 200:
            print("  [OK] Health check passed")
            return True
        else:
            print("  [FAIL] Health check failed")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_login(username: str, password: str):
    """Test login endpoint."""
    print("\n" + "=" * 70)
    print(f"  TEST 2: Login as {username}")
    print("=" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": username, "password": password},
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] Login successful")
            print(f"  Token Type: {data['token_type']}")
            print(f"  Expires In: {data['expires_in']} seconds")
            print(f"  Access Token: {data['access_token'][:50]}...")
            return data["access_token"]
        else:
            print(f"  [FAIL] Login failed: {response.json()}")
            return None
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return None


def test_wrong_password(username: str):
    """Test login with wrong password."""
    print("\n" + "=" * 70)
    print(f"  TEST 3: Login with Wrong Password ({username})")
    print("=" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": username, "password": "wrongpassword"},
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print(f"  [OK] Correctly rejected wrong password")
            print(f"  Error: {response.json()['detail']}")
            return True
        else:
            print(f"  [FAIL] Should have rejected wrong password")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_get_current_user(token: str):
    """Test getting current user info."""
    print("\n" + "=" * 70)
    print("  TEST 4: Get Current User Info")
    print("=" * 70)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] Got user info")
            print(f"  Username: {data['username']}")
            print(f"  Email: {data['email']}")
            print(f"  Full Name: {data['full_name']}")
            print(f"  Role: {data['role']}")
            return True
        else:
            print(f"  [FAIL] Failed to get user info: {response.json()}")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_unauthorized_access():
    """Test accessing protected endpoint without token."""
    print("\n" + "=" * 70)
    print("  TEST 5: Unauthorized Access (No Token)")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/me")
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print(f"  [OK] Correctly blocked unauthorized access")
            print(f"  Error: {response.json()['detail']}")
            return True
        else:
            print(f"  [FAIL] Should have blocked unauthorized access")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_invalid_token():
    """Test accessing protected endpoint with invalid token."""
    print("\n" + "=" * 70)
    print("  TEST 6: Invalid Token")
    print("=" * 70)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_12345"},
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print(f"  [OK] Correctly rejected invalid token")
            print(f"  Error: {response.json()['detail']}")
            return True
        else:
            print(f"  [FAIL] Should have rejected invalid token")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_token_refresh(token: str):
    """Test token refresh endpoint."""
    print("\n" + "=" * 70)
    print("  TEST 7: Token Refresh")
    print("=" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] Token refreshed successfully")
            print(f"  New Token: {data['access_token'][:50]}...")
            return True
        else:
            print(f"  [FAIL] Token refresh failed: {response.json()}")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def main():
    """Run all authentication tests."""
    print("\n" + "=" * 70)
    print("  AUTHENTICATION SYSTEM - TEST SUITE")
    print("=" * 70)
    print("\n  Make sure the backend is running on http://localhost:8000")
    print("  Start with: python backend/main.py")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Login with correct credentials
    token = test_login("admin", "admin123")
    results.append(("Login (Correct)", token is not None))
    
    if token:
        # Test 3: Wrong password
        results.append(("Wrong Password", test_wrong_password("admin")))
        
        # Test 4: Get current user
        results.append(("Get Current User", test_get_current_user(token)))
        
        # Test 5: Unauthorized access
        results.append(("Unauthorized Access", test_unauthorized_access()))
        
        # Test 6: Invalid token
        results.append(("Invalid Token", test_invalid_token()))
        
        # Test 7: Token refresh
        results.append(("Token Refresh", test_token_refresh(token)))
    
    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[OK] PASSED" if result else "[FAIL] FAILED"
        print(f"  {test_name:.<50} {status}")
    
    print("\n" + "=" * 70)
    print(f"  TOTAL: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n  🎉 All tests passed! Authentication system is working correctly.")
    else:
        print(f"\n  [WARN]  {total - passed} test(s) failed. Check the output above.")
    
    print("\n" + "=" * 70)
    print("  DEFAULT USERS:")
    print("=" * 70)
    for username, creds in USERS.items():
        print(f"  Username: {creds['username']:.<20} Password: {creds['password']}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
