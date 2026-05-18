"""
tests/test_llm.py
---------------------------------------------
LLM Testing Phase:
  - API key valid           -> Success
  - LLM response generated  -> Success
  - Invalid key handled     -> Safe error
"""

import sys
import io
import os
import unittest
from unittest.mock import patch, MagicMock

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from agents.llm import get_llm, call_llm, DEFAULT_MODEL, DEFAULT_TEMPERATURE


# =============================================================
# TEST SUITE
# =============================================================

class TestLLM(unittest.TestCase):

    # ---------------------------------------------------------
    # TEST 1: API key valid — LLM object created
    # ---------------------------------------------------------
    def test_1_api_key_valid(self):
        """GROQ_API_KEY in .env must allow LLM instance creation."""
        print("\n[TEST 1] API Key Valid")
        print("-" * 50)

        try:
            llm = get_llm()
            self.assertIsNotNone(llm)
            print(f"  [OK] LLM instance created : {type(llm).__name__}")
            print(f"  [OK] Model                : {DEFAULT_MODEL}")
            print(f"  [OK] Temperature          : {DEFAULT_TEMPERATURE}")
            print("  => PASS")
        except EnvironmentError as e:
            self.fail(f"API key missing: {e}")
        except Exception as e:
            self.fail(f"LLM creation failed: {e}")

    # ---------------------------------------------------------
    # TEST 2: LLM response generated (live call)
    # ---------------------------------------------------------
    def test_2_llm_response_generated(self):
        """LLM must return a non-empty string response."""
        print("\n[TEST 2] LLM Response Generated (Live Call)")
        print("-" * 50)

        try:
            response = call_llm(
                user_prompt   = "Reply with exactly one word: CONNECTED",
                system_prompt = "You are a test assistant. Reply with exactly one word.",
            )

            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)

            print(f"  [OK] Response type   : {type(response).__name__}")
            print(f"  [OK] Response length : {len(response)} chars")
            print(f"  [OK] Response        : '{response}'")
            print("  => PASS")
        except Exception as e:
            self.fail(f"LLM call failed: {e}")

    # ---------------------------------------------------------
    # TEST 3: Invalid key handled — safe error
    # ---------------------------------------------------------
    def test_3_invalid_key_safe_error(self):
        """Missing GROQ_API_KEY must raise EnvironmentError, not crash."""
        print("\n[TEST 3] Invalid Key -> Safe Error")
        print("-" * 50)

        with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=False):
            try:
                get_llm()
                self.fail("Expected EnvironmentError was not raised")
            except EnvironmentError as e:
                print(f"  [OK] EnvironmentError raised : {str(e)[:60]}")
                print("  => PASS — Missing key handled safely")
            except Exception as e:
                self.fail(f"Wrong exception type: {type(e).__name__}: {e}")

    # ---------------------------------------------------------
    # TEST 4: LLM call with custom system prompt
    # ---------------------------------------------------------
    def test_4_custom_system_prompt(self):
        """LLM must respect custom system prompts."""
        print("\n[TEST 4] Custom System Prompt")
        print("-" * 50)

        response = call_llm(
            system_prompt = "You are a Python expert. Always respond in one sentence.",
            user_prompt   = "What is a list comprehension?",
        )

        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 10)

        print(f"  [OK] Response      : '{response[:80]}...'")
        print(f"  [OK] Length        : {len(response)} chars")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 5: LLM call with code-generation prompt
    # ---------------------------------------------------------
    def test_5_code_generation_prompt(self):
        """LLM must generate valid Python code when prompted."""
        print("\n[TEST 5] Code Generation Prompt")
        print("-" * 50)

        response = call_llm(
            system_prompt = "You are a Python code generator. Return only Python code, no explanation.",
            user_prompt   = "Write a Python function that adds two numbers and returns the result.",
        )

        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 10)
        # Should contain Python code keywords
        has_code = any(kw in response for kw in ["def ", "return", "+"])
        self.assertTrue(has_code, f"Response doesn't look like code: {response[:100]}")

        print(f"  [OK] Contains code : {has_code}")
        print(f"  [OK] Length        : {len(response)} chars")
        print(f"  [OK] Preview       : '{response[:80]}...'")
        print("  => PASS")

    # ---------------------------------------------------------
    # TEST 6: API failure handled — RuntimeError not crash
    # ---------------------------------------------------------
    def test_6_api_failure_safe(self):
        """If Groq API fails mid-call, must raise RuntimeError not crash."""
        print("\n[TEST 6] API Failure -> Safe RuntimeError")
        print("-" * 50)

        with patch("agents.llm.ChatGroq") as MockGroq:
            mock_instance = MockGroq.return_value
            mock_instance.invoke.side_effect = Exception("Connection refused")

            try:
                call_llm(user_prompt="test")
                self.fail("Expected RuntimeError was not raised")
            except RuntimeError as e:
                print(f"  [OK] RuntimeError raised   : {str(e)[:60]}")
                print("  => PASS — API failure handled safely")
            except Exception as e:
                self.fail(f"Wrong exception type: {type(e).__name__}: {e}")


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  LLM — FULL TESTING PHASE")
    print("=" * 55)

    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite  = loader.loadTestsFromTestCase(TestLLM)

    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 55)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    if result.wasSuccessful():
        print("  [ALL PASS] Groq LLM is connected and production ready!")
    else:
        for f in result.failures + result.errors:
            print(f"  [FAIL] {f[0]}")
            print(f"         {f[1][:200]}")
    print("=" * 55 + "\n")
