"""
test_parser.py
Unit tests for the new robust DeveloperAgent code parser.
Run: venv\Scripts\python.exe test_parser.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from agents.developer_agent.developer_agent import DeveloperAgent

agent = DeveloperAgent(use_retriever=False, use_memory=False)

PASS = "[PASS]"
FAIL = "[FAIL]"

# ── Test 1: canonical ### FILE: marker ─────────────────────────────────────
r1 = agent._parse_code_response(
    "### FILE: backend/auth.py\n"
    "```python\n"
    "def login(email, password):\n"
    "    return {'token': 'abc'}\n"
    "```\n"
    "### IMPLEMENTATION NOTES:\n"
    "Added login function.\n",
    "TEST-1"
)
t1 = r1.success and "backend/auth.py" in r1.generated_files
print(f"{PASS if t1 else FAIL} Test 1 (### FILE:)    -> files={list(r1.generated_files.keys())}")

# ── Test 2: ## FILE: variant ────────────────────────────────────────────────
r2 = agent._parse_code_response(
    "## FILE: backend/utils.py\n"
    "```python\n"
    "def helper():\n"
    "    pass\n"
    "```\n",
    "TEST-2"
)
t2 = r2.success and "backend/utils.py" in r2.generated_files
print(f"{PASS if t2 else FAIL} Test 2 (## FILE:)     -> files={list(r2.generated_files.keys())}")

# ── Test 3: filename with trailing LLM comment ──────────────────────────────
r3 = agent._parse_code_response(
    "### FILE: backend/models.py  # new file\n"
    "```python\n"
    "class User:\n"
    "    pass\n"
    "```\n",
    "TEST-3"
)
t3 = r3.success and "backend/models.py" in r3.generated_files
print(f"{PASS if t3 else FAIL} Test 3 (trailing #)   -> files={list(r3.generated_files.keys())}")

# ── Test 4: **FILE:** variant ────────────────────────────────────────────────
r4 = agent._parse_code_response(
    "**FILE:** backend/routes.py\n"
    "```python\n"
    "from fastapi import APIRouter\n"
    "router = APIRouter()\n"
    "```\n",
    "TEST-4"
)
t4 = r4.success and "backend/routes.py" in r4.generated_files
print(f"{PASS if t4 else FAIL} Test 4 (**FILE:**)     -> files={list(r4.generated_files.keys())}")

# ── Test 5: multiple files in one response ───────────────────────────────────
r5 = agent._parse_code_response(
    "### FILE: app/main.py\n"
    "```python\n"
    "from fastapi import FastAPI\n"
    "app = FastAPI()\n"
    "```\n"
    "\n"
    "### FILE: app/models.py\n"
    "```python\n"
    "from pydantic import BaseModel\n"
    "class Item(BaseModel):\n"
    "    name: str\n"
    "```\n"
    "### IMPLEMENTATION NOTES:\n"
    "Two files created.\n",
    "TEST-5"
)
t5 = r5.success and len(r5.generated_files) == 2
print(f"{PASS if t5 else FAIL} Test 5 (multi-file)   -> files={list(r5.generated_files.keys())}")

# ── Test 6: no file markers — should fail gracefully with diagnostics ────────
r6 = agent._parse_code_response("Here is some explanation without file markers.", "TEST-6")
t6 = not r6.success and "No code files" in r6.error
print(f"{PASS if t6 else FAIL} Test 6 (no markers)   -> error='{r6.error[:60]}'")

# ── Test 7: code inside file is captured correctly ───────────────────────────
r7 = agent._parse_code_response(
    "### FILE: service/auth_service.py\n"
    "```python\n"
    "import jwt\n"
    "import bcrypt\n"
    "\n"
    "def hash_password(password: str) -> str:\n"
    "    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()\n"
    "\n"
    "def verify_password(plain: str, hashed: str) -> bool:\n"
    "    return bcrypt.checkpw(plain.encode(), hashed.encode())\n"
    "```\n",
    "TEST-7"
)
t7 = r7.success and "bcrypt" in r7.generated_files.get("service/auth_service.py", "")
print(f"{PASS if t7 else FAIL} Test 7 (code capture)  -> code_len={len(r7.generated_files.get('service/auth_service.py',''))}")

print()
all_pass = all([t1, t2, t3, t4, t5, t6, t7])
print("=" * 50)
print(f"  RESULT: {'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
print("=" * 50)
