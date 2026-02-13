#!/usr/bin/env python3
"""
Check GitHub authentication status.
Returns 0 if authenticated with write access, 1 otherwise.
Provides helpful instructions if authentication is missing.

Usage:
  python .instructions/scripts/check_github_auth.py
  python .instructions/scripts/check_github_auth.py --verbose
  python .instructions/scripts/check_github_auth.py --ci

Exit codes:
  0 - Authenticated with write access
  1 - Not authenticated or no write access
  2 - Authentication method found but needs verification
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_gh_cli_auth() -> tuple[bool, str]:
    """Check if gh CLI is authenticated."""
    if not shutil.which("gh"):
        return False, "GitHub CLI (gh) not installed"
    
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Parse output to find account and scopes
            output = result.stdout + result.stderr
            
            # Check for logged in user
            if "Logged in to" in output or "✓" in output:
                # Try to get current user
                try:
                    user_result = subprocess.run(
                        ["gh", "api", "user", "--jq", ".login"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if user_result.returncode == 0:
                        username = user_result.stdout.strip()
                        return True, f"Authenticated as {username} via gh CLI"
                except Exception:
                    pass
                
                return True, "Authenticated via gh CLI"
            else:
                return False, "gh CLI installed but not authenticated"
        else:
            return False, "gh CLI not authenticated"
    except Exception as e:
        return False, f"Error checking gh CLI: {e}"


def check_token_auth() -> tuple[bool, str]:
    """Check if GITHUB_TOKEN is set."""
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    
    if not token:
        return False, "No GITHUB_TOKEN or GH_TOKEN environment variable"
    
    # Basic validation
    if not token.startswith(("ghp_", "gho_", "github_pat_")):
        return False, "Token found but format looks invalid"
    
    # Try to verify token works
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "-H", f"Authorization: token {token}",
             "https://api.github.com/user"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.stdout.strip() == "200":
            return True, "Token authenticated (GITHUB_TOKEN)"
        elif result.stdout.strip() == "401":
            return False, "Token is invalid or expired"
        else:
            return False, f"Token verification failed (HTTP {result.stdout.strip()})"
    except Exception as e:
        return False, f"Error verifying token: {e}"


def get_auth_instructions() -> str:
    """Get instructions for setting up authentication."""
    instructions = """
🔐 GitHub Authentication Required

To enable automatic issue and PR creation, you need GitHub write access.

Option 1: Use GitHub CLI (Recommended)
─────────────────────────────────────
Install:
  macOS:     brew install gh
  Ubuntu:    sudo apt install gh
  Windows:   winget install --id GitHub.cli

Authenticate:
  gh auth login
  
Follow the prompts to authenticate with your GitHub account.

Option 2: Personal Access Token
───────────────────────────────
Create a token:
  1. Go to: https://github.com/settings/tokens
  2. Click "Generate new token (classic)"
  3. Select scopes:
     ☑ repo (full control of private repositories)
     ☑ workflow (update GitHub Action workflows)
  4. Generate and copy the token

Set the token:
  export GITHUB_TOKEN=ghp_your_token_here
  
Or save to .env.local (gitignored):
  echo "GITHUB_TOKEN=ghp_your_token_here" >> .env.local

Verify Authentication:
  python .instructions/scripts/check_github_auth.py --verbose

Skip Integration:
─────────────────
If you prefer not to integrate with GitHub, you can:
1. Complete tasks locally
2. Manually create issues/PRs when ready
3. Update the agent ledger manually

To skip GitHub integration for a specific task:
  python .instructions/scripts/github_integrator.py T001 --skip-pr
"""
    return instructions


def main():
    parser = argparse.ArgumentParser(
        description="Check GitHub authentication status"
    )
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed status")
    parser.add_argument("--ci", action="store_true",
                        help="CI mode (no interactive prompts)")
    
    args = parser.parse_args()
    
    # Check both authentication methods
    gh_ok, gh_msg = check_gh_cli_auth()
    token_ok, token_msg = check_token_auth()
    
    # Determine overall status
    if gh_ok or token_ok:
        if args.verbose:
            print("✅ GitHub Authentication: OK")
            print(f"   Method: {gh_msg if gh_ok else token_msg}")
            
            # Show repo if detectable
            try:
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"   Repository: {result.stdout.strip()}")
            except Exception:
                pass
        else:
            print("GitHub authentication: OK")
        
        return 0
    
    # Not authenticated
    if args.verbose:
        print("❌ GitHub Authentication: NOT FOUND")
        print(f"   gh CLI: {gh_msg}")
        print(f"   Token: {token_msg}")
        print()
        print(get_auth_instructions())
    elif not args.ci:
        print("❌ GitHub authentication not found")
        print("Run with --verbose for setup instructions")
        print("Or run: gh auth login")
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
