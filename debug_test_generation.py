"""
Debug Test Generation
Helps diagnose why pytest shows 0/0 tests
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agents.qa_agent import QAAgent

# Mock data
requirements = {
    "functional_requirements": [
        "Create GET /api/users/profile endpoint",
        "Return user's email, name, and account creation date",
        "Require authentication (JWT token)",
    ],
    "edge_cases": "Handle unauthenticated requests, invalid tokens",
}

generated_code = {
    "backend/auth/auth_routes.py": """
from fastapi import APIRouter, Depends
from backend.auth.auth_utils import get_current_user

router = APIRouter()

@router.get("/profile")
async def get_profile(current_user = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "name": current_user.name,
        "created_at": current_user.created_at
    }
""",
}

print("\n" + "=" * 70)
print("  DEBUG: Test Generation for SCRUM-6")
print("=" * 70)

# Create QA agent
agent = QAAgent(use_memory=False)

# Generate tests
print("\n[1] Generating test files...")
test_files = agent._generate_test_files(
    ticket_id="SCRUM-6",
    functional_reqs=requirements["functional_requirements"],
    generated_code=generated_code,
    edge_cases=requirements["edge_cases"],
)

print(f"\n[2] Generated {len(test_files)} test file(s):")
for filename in test_files.keys():
    print(f"  - {filename}")

print("\n[3] Test file contents:")
for filename, code in test_files.items():
    print(f"\n{'=' * 70}")
    print(f"FILE: {filename}")
    print('=' * 70)
    print(code[:500])
    if len(code) > 500:
        print(f"\n... ({len(code) - 500} more characters)")
    print()

print("\n[4] Checking for common issues:")
for filename, code in test_files.items():
    print(f"\n  Checking {filename}:")
    
    # Check 1: Has test functions
    test_count = code.count("def test_")
    print(f"    ✓ Test functions found: {test_count}")
    
    # Check 2: Has imports
    has_pytest = "import pytest" in code or "from pytest" in code
    print(f"    {'✓' if has_pytest else '✗'} Pytest import: {has_pytest}")
    
    # Check 3: Syntax check
    try:
        compile(code, filename, 'exec')
        print(f"    ✓ Syntax: Valid")
    except SyntaxError as e:
        print(f"    ✗ Syntax Error: {e}")
    
    # Check 4: File naming
    starts_with_test = filename.startswith("test_")
    print(f"    {'✓' if starts_with_test else '✗'} Naming convention: {starts_with_test}")

print("\n[5] Executing pytest...")
result = agent._execute_pytest(
    generated_code=generated_code,
    test_files=test_files,
)

print(f"\n[6] Pytest Results:")
print(f"  Exit Code: {result['exit_code']}")
print(f"  Tests Passed: {result['tests_passed']}")
print(f"  Tests Failed: {result['tests_failed']}")
print(f"  Tests Total: {result['tests_total']}")
print(f"\n  Output (first 1000 chars):")
print(f"  {'-' * 70}")
print(f"  {result['output'][:1000]}")
if len(result['output']) > 1000:
    print(f"  ... ({len(result['output']) - 1000} more characters)")

print("\n" + "=" * 70)
print("  DEBUG COMPLETE")
print("=" * 70 + "\n")
