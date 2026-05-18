"""
agents/llm.py
---------------------------------------------
LLM Setup Module
Configures and provides LLM instances with fallback support.
Supports multiple providers: Groq, OpenAI, Anthropic

Primary: Groq (fast, free tier available)
Fallback: OpenAI (if Groq rate limited)
"""

import os
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# ─── Model config ────────────────────────────
DEFAULT_MODEL       = "llama-3.3-70b-versatile"
FALLBACK_MODEL      = "llama-3.1-8b-instant"  # Updated: llama3-8b-8192 is decommissioned
DEFAULT_TEMPERATURE = 0.2    # low = more deterministic code output
DEFAULT_MAX_TOKENS  = 2048
MAX_RETRIES         = 3
RETRY_DELAY         = 2  # seconds


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
    use_fallback:  bool = True,
) -> str:
    """
    Calls the LLM with a user + optional system prompt.
    Returns the text response string.
    
    Includes automatic retry logic and fallback to smaller model on rate limits.

    Args:
        user_prompt:   The user message
        system_prompt: The system/role message
        model:         Groq model name
        temperature:   Sampling temperature
        use_fallback:  Whether to fallback to smaller model on rate limit

    Returns:
        str: LLM text response

    Raises:
        EnvironmentError: On missing API key
        Exception: On API failure after all retries
    """
    last_error = None
    
    # Try primary model with retries
    for attempt in range(MAX_RETRIES):
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
            error_str = str(e)
            last_error = e
            
            # Check if it's a rate limit error
            if "rate_limit" in error_str.lower() or "429" in error_str:
                print(f"⚠️  Rate limit hit on {model} (attempt {attempt + 1}/{MAX_RETRIES})")
                
                # Try fallback model if enabled and not already using it
                if use_fallback and model != FALLBACK_MODEL:
                    print(f"🔄 Switching to fallback model: {FALLBACK_MODEL}")
                    try:
                        llm = get_llm(model=FALLBACK_MODEL, temperature=temperature, max_tokens=DEFAULT_MAX_TOKENS)
                        messages = [
                            SystemMessage(content=system_prompt),
                            HumanMessage(content=user_prompt),
                        ]
                        response = llm.invoke(messages)
                        return response.content.strip()
                    except Exception as fallback_error:
                        print(f"❌ Fallback model also failed: {str(fallback_error)}")
                        last_error = fallback_error
                
                # Wait before retry
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
            else:
                # Non-rate-limit error, raise immediately
                raise RuntimeError(f"LLM call failed: {error_str}")
    
    # All retries exhausted
    raise RuntimeError(f"LLM call failed after {MAX_RETRIES} attempts: {str(last_error)}")


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
