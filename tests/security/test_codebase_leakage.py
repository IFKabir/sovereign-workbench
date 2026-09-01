import subprocess
import pytest

def test_no_cloud_ai_endpoints_in_codebase():
    forbidden_domains = [
        "api.openai.com",
        "api.anthropic.com",
        "generativelanguage.googleapis.com",
        "api.cohere.ai",
        "api.together.xyz"
    ]
    for domain in forbidden_domains:
        result = subprocess.run(
            ["grep", "-rnE", domain, "packages/", "apps/", "--exclude-dir=node_modules", "--exclude-dir=.next"],
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == "", f"Found forbidden cloud endpoint '{domain}' in codebase:\n{result.stdout}"
