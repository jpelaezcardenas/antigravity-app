#!/usr/bin/env python3
"""
Cloud-Only LLM Architecture Verification Script

This script validates that the Cloud-Only migration is complete and working:
1. No Ollama references in code
2. API keys configured
3. Model selector routes correctly
4. Failover chain is valid
5. All endpoints registered

Run: python scripts/verify_cloud_only_setup.py
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

from agents.llm_engine import LLMProvider
from core.model_selector import choose_model_for_task, get_task_tier


def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_check(passed, message):
    """Print check result"""
    symbol = "[PASS]" if passed else "[FAIL]"
    print(f"{symbol} {message}")
    return passed


def verify_no_ollama():
    """Verify Ollama is completely removed"""
    print_header("1. Verify No Ollama References")

    checks = []

    # Check enum
    has_ollama = hasattr(LLMProvider, 'OLLAMA')
    checks.append(print_check(
        not has_ollama,
        "LLMProvider.OLLAMA removed from enum"
    ))

    # Check code files
    backend_path = Path(__file__).parent.parent / "apps" / "backend"
    for py_file in backend_path.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "_call_ollama" in content:
                    checks.append(print_check(False, f"Found _call_ollama in {py_file.name}"))
                if "ollama_base_url" in content and "OLLAMA_BASE_URL" not in content:
                    checks.append(print_check(False, f"Found ollama_base_url in {py_file.name}"))
        except Exception:
            pass

    if len(checks) == 1:  # Only enum check
        checks.append(print_check(True, "No _call_ollama() methods found"))
        checks.append(print_check(True, "No ollama_base_url references in code"))

    return all(checks)


def verify_api_keys():
    """Verify required API keys are configured"""
    print_header("2. Verify API Keys Configuration")

    checks = []

    # Check OpenRouter Free
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    checks.append(print_check(
        bool(openrouter_key),
        f"OPENROUTER_API_KEY configured: {'sk-or-...' if openrouter_key else 'NOT SET'}"
    ))

    # Check Groq
    groq_key = os.getenv("GROQ_API_KEY")
    checks.append(print_check(
        bool(groq_key),
        f"GROQ_API_KEY configured: {'gsk_...' if groq_key else 'NOT SET'}"
    ))

    # Check Claude (for development)
    claude_key = os.getenv("CLAUDE_API_KEY")
    checks.append(print_check(
        bool(claude_key),
        f"CLAUDE_API_KEY configured: {'sk-ant-...' if claude_key else 'NOT SET (optional)'}"
    ))

    return all(checks)


def verify_model_selector():
    """Verify model selector routes correctly"""
    print_header("3. Verify Model Selector Routing")

    test_cases = [
        ("taty_faq", "tier_1", LLMProvider.OPENROUTER_FREE),
        ("social_content_gen", "tier_1", LLMProvider.OPENROUTER_FREE),
        ("pulso_analysis", "tier_2", LLMProvider.OPENROUTER_FREE),
        ("centinela_monitoring", "tier_2", LLMProvider.OPENROUTER_FREE),
        ("centinela_decision", "tier_3", LLMProvider.GROQ),
        ("compliance_audit", "tier_3", LLMProvider.GROQ),
    ]

    checks = []
    for task, expected_tier, expected_provider in test_cases:
        provider = choose_model_for_task(task)
        tier = get_task_tier(task)

        provider_ok = provider == expected_provider
        tier_ok = tier == expected_tier
        ok = provider_ok and tier_ok

        checks.append(print_check(
            ok,
            f"{task:30s} -> {provider.value:20s} [{tier}]"
        ))

    return all(checks)


def verify_failover_chain():
    """Verify failover chain order"""
    print_header("4. Verify Failover Chain Order")

    checks = []

    # Check provider order (if accessible)
    from agents.llm_engine import LLMEngine
    engine = LLMEngine()

    expected_order = [
        LLMProvider.OPENROUTER_FREE,
        LLMProvider.GROQ,
        LLMProvider.CEREBRAS,
        LLMProvider.MISTRAL,
        LLMProvider.GEMINI,
        LLMProvider.OPENROUTER,
    ]

    checks.append(print_check(
        engine.provider_order == expected_order,
        f"Failover chain order correct"
    ))

    # Print chain
    print("\n  Failover chain:")
    for i, provider in enumerate(engine.provider_order, 1):
        print(f"    {i}. {provider.value}")

    return all(checks)


def verify_endpoints():
    """Verify agent endpoints are registered"""
    print_header("5. Verify API Endpoints")

    checks = []

    # Check that endpoints exist
    from presentation.agents_endpoints import router as agents_router

    expected_endpoints = [
        "/taty/ask",
        "/social/generate-content",
        "/pulso/analyze",
        "/centinela/monitor",
        "/centinela/decide",
        "/compliance/audit",
        "/task-info/{task_type}",
    ]

    # Count routes
    route_paths = {route.path for route in agents_router.routes}

    for endpoint in expected_endpoints:
        exists = any(endpoint in path for path in route_paths)
        checks.append(print_check(
            exists,
            f"Endpoint {endpoint:35s} registered"
        ))

    return all(checks)


def print_summary(results):
    """Print summary of verification"""
    print_header("VERIFICATION SUMMARY")

    checks = [
        ("No Ollama References", results[0]),
        ("API Keys Configured", results[1]),
        ("Model Selector Routing", results[2]),
        ("Failover Chain", results[3]),
        ("API Endpoints", results[4]),
    ]

    all_passed = all(passed for _, passed in checks)

    for name, passed in checks:
        symbol = "[OK]" if passed else "[FAIL]"
        print(f"{symbol} {name}")

    print(f"\n{'='*60}")
    if all_passed:
        print("  [OK] ALL CHECKS PASSED - Cloud-Only setup is complete!")
        print("  Ready for staging/production deployment.")
    else:
        print("  [ERROR] SOME CHECKS FAILED - Review errors above.")
        print("  Please fix before deploying to production.")
    print(f"{'='*60}\n")

    return all_passed


def main():
    """Run all verification checks"""
    print("\n[INFO] Verifying Cloud-Only LLM Architecture Setup...\n")

    try:
        results = [
            verify_no_ollama(),
            verify_api_keys(),
            verify_model_selector(),
            verify_failover_chain(),
            verify_endpoints(),
        ]

        success = print_summary(results)
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n[ERROR] Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
