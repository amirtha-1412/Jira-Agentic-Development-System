"""
agents/llm.py
---------------------------------------------
LLM Setup Module
Configures and provides a Groq LLM instance
for all AI agents in the system.

Model: llama3-8b-8192 (fast, free on Groq)
  - 8B parameters
  - 8192 token context
  - ~500 tokens/sec on Groq
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# ─── Model config ────────────────────────────
DEFAULT_MODEL       = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE = 0.2    # low = more deterministic code output
DEFAULT_MAX_TOKENS  = 2048


# ─────────────────────────────────────────────
# LLM Factory
# ─────────────────────────────────────────────

def get_llm(
    model:       str   = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens:  int   = DEFAULT_MAX_TOKENS,
) -> ChatGroq:
    """
    Creates and returns a configured ChatGroq LLM instance.
    Validates API key before returning.

    Args:
        model:       Groq model name
        temperature: Sampling temperature (0=deterministic)
        max_tokens:  Max output tokens

    Returns:
        ChatGroq: Configured LLM instance

    Raises:
        EnvironmentError: If GROQ_API_KEY is not set
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not found. "
            "Add it to your .env file: GROQ_API_KEY=gsk_..."
        )

    return ChatGroq(
        model        = model,
        temperature  = temperature,
        max_tokens   = max_tokens,
        api_key      = api_key,
    )


# ─────────────────────────────────────────────
# Convenience: Call LLM with a prompt
# ─────────────────────────────────────────────

def call_llm(
    user_prompt:   str,
    system_prompt: str  = "You are a helpful software engineering assistant.",
    model:         str  = DEFAULT_MODEL,
    temperature:   float= DEFAULT_TEMPERATURE,
) -> str:
    """
    Calls the LLM with a user + optional system prompt.
    Returns the text response string.

    Args:
        user_prompt:   The user message
        system_prompt: The system/role message
        model:         Groq model name
        temperature:   Sampling temperature

    Returns:
        str: LLM text response

    Raises:
        EnvironmentError: On missing API key
        Exception: On API failure
    """
    try:
        llm = get_llm(model=model, temperature=temperature)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = llm.invoke(messages)
        return response.content.strip()

    except EnvironmentError:
        raise
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {str(e)}")


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("\n" + "=" * 55)
    print("  LLM SETUP - TEST RUN")
    print("=" * 55)

    print(f"\n  [OK] Model       : {DEFAULT_MODEL}")
    print(f"  [OK] Temperature : {DEFAULT_TEMPERATURE}")
    print(f"  [OK] Max tokens  : {DEFAULT_MAX_TOKENS}")

    print(f"\n  Testing LLM connection...")
    try:
        response = call_llm(
            user_prompt   = "Say 'LLM is connected!' and nothing else.",
            system_prompt = "You are a test assistant. Respond exactly as instructed.",
        )
        print(f"  [OK] Response    : {response}")
        print(f"  [OK] Length      : {len(response)} chars")
    except Exception as e:
        print(f"  [FAIL] {e}")

    print("\n" + "=" * 55)
    print("  [DONE] LLM test complete.")
    print("=" * 55 + "\n")
