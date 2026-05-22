#!/usr/bin/env python3
"""
Cloud-Only LLM Staging Test
Tests OpenRouter Free + Groq failover without requiring Supabase
"""

import sys
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / "apps" / "backend" / ".env")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "backend"))

from agents.llm_engine import LLMEngine, LLMProvider
from core.model_selector import choose_model_for_task, get_task_tier


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_result(passed, message):
    symbol = "[OK]" if passed else "[FAIL]"
    print(f"{symbol} {message}")
    return passed


def test_environment():
    """Verify environment variables are set"""
    print_header("1. Environment Setup")

    checks = []

    # Check OpenRouter key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    checks.append(print_result(
        bool(openrouter_key) and not "XXXXXXXX" in openrouter_key,
        f"OPENROUTER_API_KEY configured: {openrouter_key[:20] + '...' if openrouter_key else 'NOT SET'}"
    ))

    # Check Groq key
    groq_key = os.getenv("GROQ_API_KEY")
    checks.append(print_result(
        bool(groq_key) and not "XXXXXXXX" in groq_key,
        f"GROQ_API_KEY configured: {groq_key[:20] + '...' if groq_key else 'NOT SET'}"
    ))

    return all(checks)


def test_model_selector():
    """Test model routing logic"""
    print_header("2. Model Selector Routing")

    test_cases = [
        ("taty_faq", "tier_1", LLMProvider.OPENROUTER_FREE),
        ("social_content_gen", "tier_1", LLMProvider.OPENROUTER_FREE),
        ("pulso_analysis", "tier_2", LLMProvider.OPENROUTER_FREE),
        ("centinela_decision", "tier_3", LLMProvider.GROQ),
    ]

    checks = []
    for task, expected_tier, expected_provider in test_cases:
        provider = choose_model_for_task(task)
        tier = get_task_tier(task)

        provider_ok = provider == expected_provider
        tier_ok = tier == expected_tier
        ok = provider_ok and tier_ok

        checks.append(print_result(
            ok,
            f"{task:30s} -> {provider.value:20s} [{tier}]"
        ))

    return all(checks)


def test_openrouter_free():
    """Test OpenRouter Free API (Tier 1)"""
    print_header("3. OpenRouter Free (Tier 1 - Non-sensitive)")

    engine = LLMEngine()

    try:
        prompt = "What is the definition of 'Renta' in Colombian tax context? (answer in one sentence)"
        system_prompt = "You are a helpful assistant. Answer briefly."

        print(f"Testing OpenRouter Free with prompt: '{prompt}'")
        response = engine.get_ai_response(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="text",
            max_tokens=150,
            temperature=0.7,
            timeout=15
        )

        success = isinstance(response, str) and len(response) > 10
        print_result(success, f"OpenRouter Free response: {response[:80]}...")

        return success

    except Exception as e:
        print_result(False, f"OpenRouter Free failed: {str(e)[:100]}")
        return False


def test_groq():
    """Test Groq API (Tier 3 - Critical)"""
    print_header("4. Groq (Tier 3 - Critical/Fiscal)")

    engine = LLMEngine()

    try:
        prompt = "Should a Colombian company with 10M COP annual revenue file a tax return? (Yes/No + brief reason)"
        system_prompt = "You are a tax advisor. Answer precisely for fiscal decisions."

        print(f"Testing Groq with prompt: '{prompt}'")
        response = engine.get_ai_response(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="text",
            max_tokens=150,
            temperature=0.5,
            timeout=15
        )

        success = isinstance(response, str) and len(response) > 10
        print_result(success, f"Groq response: {response[:80]}...")

        return success

    except Exception as e:
        print_result(False, f"Groq failed: {str(e)[:100]}")
        return False


def test_failover():
    """Test failover chain"""
    print_header("5. Failover Chain Validation")

    engine = LLMEngine()

    checks = []

    # Check provider order
    expected_order = [
        LLMProvider.OPENROUTER_FREE,
        LLMProvider.GROQ,
        LLMProvider.CEREBRAS,
        LLMProvider.MISTRAL,
        LLMProvider.GEMINI,
        LLMProvider.OPENROUTER,
    ]

    checks.append(print_result(
        engine.provider_order == expected_order,
        f"Failover chain order: {' -> '.join([p.value for p in engine.provider_order])}"
    ))

    return all(checks)


def print_summary(results):
    """Print test summary"""
    print_header("STAGING TEST SUMMARY")

    tests = [
        ("Environment Setup", results[0]),
        ("Model Selector Routing", results[1]),
        ("OpenRouter Free (Tier 1)", results[2]),
        ("Groq (Tier 3)", results[3]),
        ("Failover Chain", results[4]),
    ]

    all_passed = all(passed for _, passed in tests)

    for name, passed in tests:
        symbol = "[OK]" if passed else "[FAIL]"
        print(f"{symbol} {name}")

    print(f"\n{'='*60}")
    if all_passed:
        print("  [SUCCESS] All staging tests passed!")
        print("  Cloud-Only LLM architecture is ready for deployment.")
    else:
        print("  [ERROR] Some tests failed. Review errors above.")
    print(f"{'='*60}\n")

    return all_passed


def main():
    """Run all staging tests"""
    print("\n[INFO] Cloud-Only LLM Staging Tests\n")

    try:
        results = [
            test_environment(),
            test_model_selector(),
            test_openrouter_free(),
            test_groq(),
            test_failover(),
        ]

        success = print_summary(results)
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n[ERROR] Staging test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
