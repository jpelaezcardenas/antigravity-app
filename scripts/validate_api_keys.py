#!/usr/bin/env python3
"""
T6: API Key Validation Script
Validates all 6 LLM provider keys from Bitwarden vault.
Generates report in openspec/changes/keeper-migration-2026-06-15/reports/
"""

import subprocess
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration
PROVIDERS = {
    "groq": {
        "item_name": "groq",
        "url": "https://api.groq.com/openai/v1/models",
        "header": "Authorization",
        "header_format": "Bearer {key}",
    },
    "openai": {
        "item_name": "openai",
        "url": "https://api.openai.com/v1/models",
        "header": "Authorization",
        "header_format": "Bearer {key}",
    },
    "gemini": {
        "item_name": "gemini",
        "url": "https://generativelanguage.googleapis.com/v1/models/gemini-pro?key={key}",
        "header": None,
        "header_format": None,
    },
    "mistral": {
        "item_name": "mistral",
        "url": "https://api.mistral.ai/v1/models",
        "header": "Authorization",
        "header_format": "Bearer {key}",
    },
    "cerebras": {
        "item_name": "cerebras",
        "url": "https://api.cerebras.ai/v1/models",
        "header": "Authorization",
        "header_format": "Bearer {key}",
    },
    "openrouter": {
        "item_name": "openrouter",
        "url": "https://openrouter.ai/api/v1/models",
        "header": "Authorization",
        "header_format": "Bearer {key}",
    },
}

def get_key_from_bw(item_name):
    """Extract API key from Bitwarden vault."""
    try:
        result = subprocess.run(
            ["bw", "get", "item", item_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return None, f"bw error: {result.stderr}"

        item = json.loads(result.stdout)
        key = item.get("login", {}).get("password")
        return key, None
    except Exception as e:
        return None, str(e)

def validate_key(provider_name, config, key):
    """Validate API key against provider's API."""
    try:
        if config["header"]:
            headers = {config["header"]: config["header_format"].format(key=key)}
            url = config["url"]
        else:
            url = config["url"].format(key=key)
            headers = {}

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return True, f"✅ Status {response.status_code}"
        else:
            return False, f"❌ Status {response.status_code}: {response.text[:100]}"
    except requests.exceptions.Timeout:
        return False, "❌ Timeout"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def main():
    print("=" * 80)
    print("T6: API Key Validation")
    print("=" * 80)

    results = {}
    passed = 0
    failed = 0

    for provider_name, config in PROVIDERS.items():
        print(f"\n▶ {provider_name.upper()}...", end=" ")

        # Get key from Bitwarden
        key, bw_error = get_key_from_bw(config["item_name"])

        if bw_error:
            print(f"❌ Not found: {bw_error}")
            results[provider_name] = {"status": "MISSING", "error": bw_error}
            failed += 1
            continue

        if not key:
            print("❌ Key is empty")
            results[provider_name] = {"status": "EMPTY", "error": "Key is empty"}
            failed += 1
            continue

        # Validate key
        is_valid, message = validate_key(provider_name, config, key)

        print(message)
        results[provider_name] = {
            "status": "VALID" if is_valid else "INVALID",
            "message": message,
            "key_format": key[:20] + "..." if key else None,
        }

        if is_valid:
            passed += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed} PASSED, {failed} FAILED")
    print("=" * 80)

    # Generate report
    report_path = Path("openspec/changes/keeper-migration-2026-06-15/reports")
    report_path.mkdir(parents=True, exist_ok=True)

    report_file = report_path / f"T6-API-VALIDATION-{datetime.now().strftime('%Y-%m-%d')}.md"

    with open(report_file, "w") as f:
        f.write(f"# T6: API Key Validation Report\n\n")
        f.write(f"**Date:** {datetime.now().isoformat()}\n")
        f.write(f"**Status:** {'✅ GATE 1 PASSED' if failed == 0 else '❌ GATE 1 FAILED'}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Passed:** {passed}/{len(PROVIDERS)}\n")
        f.write(f"- **Failed:** {failed}/{len(PROVIDERS)}\n\n")
        f.write(f"## Details\n\n")

        for provider, result in results.items():
            f.write(f"### {provider.upper()}\n\n")
            f.write(f"- Status: {result['status']}\n")
            if 'message' in result:
                f.write(f"- Message: {result['message']}\n")
            if 'error' in result:
                f.write(f"- Error: {result['error']}\n")
            if 'key_format' in result and result['key_format']:
                f.write(f"- Key Format: {result['key_format']}\n")
            f.write("\n")

    print(f"\n📊 Report saved: {report_file}")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())
