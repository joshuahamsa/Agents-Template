#!/usr/bin/env python3
"""
GitHub integration automation for agent tasks.
Creates issues, PRs, and updates project boards after task completion.

Usage:
  python scripts/github_integrator.py T001                    # Full integration
  python scripts/github_integrator.py T001 --skip-pr         # Issue only
  python scripts/github_integrator.py T001 --ci-mode         # Non-interactive

Environment:
  GITHUB_TOKEN        - Personal access token with repo, workflow scopes
  GITHUB_PROJECT_NUMBER - Optional: project board number
  GITHUB_REPOSITORY   - Optional: defaults to detected remote
  
  Or use authenticated gh CLI (preferred).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# Constants
TASKS_DIR = Path(".agent/tasks")
REPORTS_DIR = Path(".agent/reports")
LEDGER_PATH = Path(".agent/ledger.yaml")
CONTRACT_PATH = Path("docs/agents/contracts/github-integration.contract.yaml")


@dataclass
class GitHubAuth:
    method: str  # 'gh_cli' or 'token'
    token: Optional[str] = None


@dataclass
class TaskInfo:
    task_id: str
    title: str
    goal: str
    context: str
    acceptance_criteria: list[str]


@dataclass
class ReportInfo:
    status: str
    summary: list[str]
    acceptance_criteria_results: list[dict]
    files_modified: list[dict]
    verification: dict


class GitHubIntegrator:
    def __init__(self, ci_mode: bool = False):
        self.ci_mode = ci_mode
        self.auth: Optional[GitHubAuth] = None
        self.repo: Optional[str] = None
        
    def run(self, task_id: str, skip_pr: bool = False) -> int:
        """Main entry point."""
        print(f"🔧 GitHub Integration for {task_id}\n")
        
        # Load task and report
        task = self._load_task(task_id)
        if not task:
            return 1
            
        report = self._load_report(task_id)
        if not report:
            print(f"⚠️  No report found for {task_id}, continuing with task info only")
            
        # Detect repository
        self.repo = self._detect_repository()
        if not self.repo:
            print("❌ Could not detect GitHub repository", file=sys.stderr)
            return 1
        print(f"📦 Repository: {self.repo}\n")
        
        # Check authentication
        self.auth = self._ensure_auth()
        if not self.auth:
            return 1
        print(f"✅ Authenticated via {self.auth.method}\n")
        
        # Create or update issue
        issue_data = self._create_or_update_issue(task, report)
        if not issue_data:
            print("⚠️  Issue creation failed, continuing...")
            issue_data = {"number": None, "url": None}
        else:
            print(f"✅ Issue: {issue_data['url']}\n")
        
        if skip_pr:
            print("⏭️  Skipping PR creation (--skip-pr)")
            self._update_ledger(task_id, issue_data, None)
            return 0
        
        # Create branch and PR
        pr_data = self._create_branch_and_pr(task, report, issue_data)
        if not pr_data:
            print("⚠️  PR creation failed")
            self._update_ledger(task_id, issue_data, None)
            return 1
        
        print(f"✅ Pull Request: {pr_data['url']}\n")
        
        # Update ledger
        self._update_ledger(task_id, issue_data, pr_data)
        
        # Optionally update project board
        self._maybe_update_project_board(issue_data)
        
        print("\n🎉 GitHub integration complete!")
        return 0
    
    def _load_task(self, task_id: str) -> Optional[TaskInfo]:
        """Load task YAML file."""
        task_path = TASKS_DIR / f"{task_id}.yaml"
        if not task_path.exists():
            print(f"❌ Task file not found: {task_path}", file=sys.stderr)
            return None
        
        try:
            with open(task_path) as f:
                data = yaml.safe_load(f)
            
            return TaskInfo(
                task_id=data.get("task_id", task_id),
                title=data.get("title", "Untitled"),
                goal=data.get("goal", ""),
                context=data.get("context", ""),
                acceptance_criteria=data.get("acceptance_criteria", [])
            )
        except Exception as e:
            print(f"❌ Failed to load task: {e}", file=sys.stderr)
            return None
    
    def _load_report(self, task_id: str) -> Optional[ReportInfo]:
        """Load report YAML file."""
        report_path = REPORTS_DIR / f"{task_id}.report.yaml"
        if not report_path.exists():
            return None
        
        try:
            with open(report_path) as f:
                data = yaml.safe_load(f)
            
            return ReportInfo(
                status=data.get("status", "unknown"),
                summary=data.get("summary", []),
                acceptance_criteria_results=data.get("acceptance_criteria_results", []),
                files_modified=data.get("files_modified", []),
                verification=data.get("verification", {})
            )
        except Exception as e:
            print(f"⚠️  Failed to load report: {e}")
            return None
    
    def _detect_repository(self) -> Optional[str]:
        """Detect GitHub repository from git remote."""
        # Check env override
        if os.getenv("GITHUB_REPOSITORY"):
            return os.getenv("GITHUB_REPOSITORY")
        
        # Try to get from git remote
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True
            )
            remote_url = result.stdout.strip()
            
            # Parse GitHub URL
            # ssh: git@github.com:user/repo.git
            # https: https://github.com/user/repo.git
            if "github.com" in remote_url:
                # Remove .git suffix and extract owner/repo
                remote_url = remote_url.replace(".git", "")
                if remote_url.startswith("git@github.com:"):
                    return remote_url.replace("git@github.com:", "")
                elif "github.com/" in remote_url:
                    return remote_url.split("github.com/")[-1]
        except subprocess.CalledProcessError:
            pass
        
        return None
    
    def _ensure_auth(self) -> Optional[GitHubAuth]:
        """Ensure GitHub authentication is available."""
        # Check for gh CLI auth first (preferred)
        if shutil.which("gh"):
            try:
                result = subprocess.run(
                    ["gh", "auth", "status"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return GitHubAuth(method="gh_cli")
            except Exception:
                pass
        
        # Check for token in environment
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if token:
            return GitHubAuth(method="token", token=token)
        
        # CI mode: fail if no auth
        if self.ci_mode:
            print("❌ No GitHub authentication found in CI mode", file=sys.stderr)
            print("Set GITHUB_TOKEN environment variable", file=sys.stderr)
            return None
        
        # Interactive mode: prompt user
        return self._prompt_for_auth()
    
    def _prompt_for_auth(self) -> Optional[GitHubAuth]:
        """Interactive prompt for authentication."""
        print("🔐 GitHub Authentication Required\n")
        print("Options:")
        print("  1. Use GitHub CLI (recommended)")
        print("     Run: gh auth login")
        print("     Then retry this command.")
        print()
        print("  2. Provide Personal Access Token")
        print("     Create at: https://github.com/settings/tokens")
        print("     Required scopes: repo, workflow")
        print()
        print("  3. Skip GitHub integration")
        print("     Task will complete locally only.")
        print()
        
        try:
            choice = input("Enter choice (1/2/3): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Aborted")
            return None
        
        if choice == "1":
            print("\n👉 Please run: gh auth login")
            print("Then retry this command.")
            return None
        
        elif choice == "2":
            try:
                token = input("\nPaste your token: ").strip()
                if token:
                    # Save to .env.local for future use
                    env_local = Path(".env.local")
                    with open(env_local, "a") as f:
                        f.write(f"\nGITHUB_TOKEN={token}\n")
                    print(f"✅ Token saved to {env_local}")
                    return GitHubAuth(method="token", token=token)
            except (EOFError, KeyboardInterrupt):
                print("\n❌ Aborted")
                return None
        
        elif choice == "3":
            print("\n⏭️  Skipping GitHub integration")
            print("You can manually create issue/PR later.")
            return None
        
        else:
            print("❌ Invalid choice")
            return None
    
    def _create_or_update_issue(self, task: TaskInfo, report: Optional[ReportInfo]) -> Optional[dict]:
        """Create or update GitHub issue."""
        issue_title = f"[{task.task_id}] {task.title}"
        
        # Search for existing issue
        existing = self._find_existing_issue(task.task_id)
        
        # Build issue body
        body = self._build_issue_body(task, report)
        
        if existing:
            print(f"📝 Updating existing issue #{existing['number']}")
            return self._update_issue(existing["number"], body)
        else:
            print(f"📝 Creating new issue: {issue_title}")
            return self._create_issue(issue_title, body)
    
    def _find_existing_issue(self, task_id: str) -> Optional[dict]:
        """Search for existing issue with task ID."""
        if self.auth is None or self.repo is None:
            return None
        try:
            if self.auth.method == "gh_cli":
                result = subprocess.run(
                    ["gh", "issue", "list", 
                     "--repo", self.repo,
                     "--search", task_id,
                     "--json", "number,title,url",
                     "--limit", "10"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                issues = json.loads(result.stdout)
                for issue in issues:
                    if task_id in issue["title"]:
                        return issue
            else:
                # Use API via curl
                token = self.auth.token
                if token:
                    result = subprocess.run(
                        ["curl", "-s", "-H", f"Authorization: token {token}",
                         f"https://api.github.com/repos/{self.repo}/issues?state=all&per_page=30"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    issues = json.loads(result.stdout)
                    for issue in issues:
                        if task_id in issue.get("title", ""):
                            return {
                                "number": issue["number"],
                                "title": issue["title"],
                                "url": issue["html_url"]
                            }
        except Exception as e:
            print(f"⚠️  Could not search for existing issue: {e}")
        
        return None
    
    def _build_issue_body(self, task: TaskInfo, report: Optional[ReportInfo]) -> str:
        """Build issue body from task and report."""
        lines = [
            f"## Goal\n{task.goal}\n",
            f"## Context\n{task.context}\n",
            "## Acceptance Criteria",
        ]
        
        for criteria in task.acceptance_criteria:
            lines.append(f"- [ ] {criteria}")
        
        lines.append("")
        
        if report:
            lines.append("## Implementation Report\n")
            lines.append(f"**Status:** {report.status}\n")
            
            if report.summary:
                lines.append("### Summary")
                for item in report.summary:
                    lines.append(f"- {item}")
                lines.append("")
            
            if report.acceptance_criteria_results:
                lines.append("### Verification Results")
                for result in report.acceptance_criteria_results:
                    status = "✅" if result.get("passed") else "❌"
                    lines.append(f"{status} {result.get('criterion', 'Unknown')}")
                lines.append("")
            
            if report.files_modified:
                lines.append("### Files Modified")
                for f in report.files_modified:
                    path = f.get("path", "unknown")
                    desc = f.get("description", "")
                    lines.append(f"- `{path}` - {desc}")
                lines.append("")
        
        lines.append("---")
        lines.append("*This issue was automatically created by the agent system.*")
        
        return "\n".join(lines)
    
    def _create_issue(self, title: str, body: str) -> Optional[dict]:
        """Create new GitHub issue."""
        if self.auth is None or self.repo is None:
            return None
        try:
            if self.auth.method == "gh_cli":
                result = subprocess.run(
                    ["gh", "issue", "create",
                     "--repo", self.repo,
                     "--title", title,
                     "--body", body,
                     "--label", "agent-task,automation"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Extract issue number from output
                url = result.stdout.strip()
                number = url.split("/")[-1]
                return {"number": int(number), "url": url}
            else:
                # Use API
                token = self.auth.token
                if not token:
                    return None
                data = {
                    "title": title,
                    "body": body,
                    "labels": ["agent-task", "automation"]
                }
                result = subprocess.run(
                    ["curl", "-s", "-X", "POST",
                     "-H", f"Authorization: token {token}",
                     "-H", "Accept: application/vnd.github.v3+json",
                     "-d", json.dumps(data),
                     f"https://api.github.com/repos/{self.repo}/issues"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                issue = json.loads(result.stdout)
                return {
                    "number": issue["number"],
                    "url": issue["html_url"]
                }
        except Exception as e:
            print(f"❌ Failed to create issue: {e}", file=sys.stderr)
            return None
    
    def _update_issue(self, issue_number: int, body: str) -> Optional[dict]:
        """Update existing GitHub issue."""
        if self.auth is None or self.repo is None:
            return None
        try:
            if self.auth.method == "gh_cli":
                subprocess.run(
                    ["gh", "issue", "edit", str(issue_number),
                     "--repo", self.repo,
                     "--body", body],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return {
                    "number": issue_number,
                    "url": f"https://github.com/{self.repo}/issues/{issue_number}"
                }
            else:
                # Use API
                token = self.auth.token
                if not token:
                    return None
                data = {"body": body}
                subprocess.run(
                    ["curl", "-s", "-X", "PATCH",
                     "-H", f"Authorization: token {token}",
                     "-H", "Accept: application/vnd.github.v3+json",
                     "-d", json.dumps(data),
                     f"https://api.github.com/repos/{self.repo}/issues/{issue_number}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return {
                    "number": issue_number,
                    "url": f"https://github.com/{self.repo}/issues/{issue_number}"
                }
        except Exception as e:
            print(f"❌ Failed to update issue: {e}", file=sys.stderr)
            return None
    
    def _create_branch_and_pr(self, task: TaskInfo, report: Optional[ReportInfo], 
                              issue_data: dict) -> Optional[dict]:
        """Create branch, commit, push, and create PR."""
        # Generate branch name
        branch_name = self._generate_branch_name(task)
        print(f"🌿 Branch: {branch_name}")
        
        # Check if branch exists
        branch_exists = self._branch_exists(branch_name)
        
        if branch_exists:
            print(f"⚠️  Branch {branch_name} already exists, switching to it")
            subprocess.run(["git", "checkout", branch_name], check=True)
        else:
            # Create and checkout branch
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        
        # Stage and commit changes
        if self._has_changes():
            commit_msg = self._generate_commit_message(task, issue_data)
            print(f"💾 Commit: {commit_msg.split(chr(10))[0]}")
            
            subprocess.run(["git", "add", "-A"], check=True)
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        else:
            print("ℹ️  No changes to commit")
        
        # Push branch
        print(f"📤 Pushing to origin...")
        try:
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            # Try force push if rejected (e.g., branch exists with different commits)
            print("⚠️  Push rejected, attempting force push...")
            subprocess.run(
                ["git", "push", "-f", "-u", "origin", branch_name],
                check=True
            )
        
        # Create PR
        pr_title = f"[{task.task_id}] {task.title}"
        pr_body = self._build_pr_body(task, report, issue_data)
        
        print(f"📋 Creating Pull Request...")
        return self._create_pr(pr_title, pr_body, branch_name)
    
    def _generate_branch_name(self, task: TaskInfo) -> str:
        """Generate branch name from task."""
        # Clean title: lowercase, replace spaces/special chars with hyphens
        clean_title = re.sub(r'[^\w\s-]', '', task.title.lower())
        clean_title = re.sub(r'[-\s]+', '-', clean_title)
        clean_title = clean_title[:30]  # Limit length
        clean_title = clean_title.strip('-')
        
        branch = f"feature/{task.task_id}-{clean_title}"
        
        # Truncate to 50 chars max
        if len(branch) > 50:
            branch = branch[:50].rsplit('-', 1)[0]
        
        return branch
    
    def _branch_exists(self, branch_name: str) -> bool:
        """Check if branch exists locally or remotely."""
        try:
            # Check local
            result = subprocess.run(
                ["git", "branch", "--list", branch_name],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                return True
            
            # Check remote
            result = subprocess.run(
                ["git", "ls-remote", "--heads", "origin", branch_name],
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except Exception:
            return False
    
    def _has_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())
    
    def _generate_commit_message(self, task: TaskInfo, issue_data: dict) -> str:
        """Generate conventional commit message."""
        # Determine commit type from task
        task_lower = task.title.lower()
        if "fix" in task_lower or "bug" in task_lower:
            commit_type = "fix"
        elif "test" in task_lower:
            commit_type = "test"
        elif "doc" in task_lower:
            commit_type = "docs"
        elif "refactor" in task_lower:
            commit_type = "refactor"
        else:
            commit_type = "feat"
        
        # Short description
        desc = re.sub(r'[^\w\s-]', '', task.title.lower())
        desc = desc[:50]
        
        lines = [
            f"{commit_type}({task.task_id}): {desc}",
            "",
            f"- {task.goal}",
        ]
        
        # Add acceptance criteria as bullet points
        for criteria in task.acceptance_criteria[:3]:  # Limit to 3
            lines.append(f"- {criteria}")
        
        # Add closes footer
        if issue_data.get("number"):
            lines.append("")
            lines.append(f"Closes #{issue_data['number']}")
        
        return "\n".join(lines)
    
    def _build_pr_body(self, task: TaskInfo, report: Optional[ReportInfo], 
                       issue_data: dict) -> str:
        """Build PR body."""
        lines = ["## Task"]
        
        if issue_data.get("number"):
            lines.append(f"Closes #{issue_data['number']}")
        lines.append("")
        
        lines.append("## Summary")
        if report and report.summary:
            for item in report.summary:
                lines.append(f"- {item}")
        else:
            lines.append(f"- {task.goal}")
        lines.append("")
        
        lines.append("## Changes")
        if report and report.files_modified:
            for f in report.files_modified:
                path = f.get("path", "unknown")
                desc = f.get("description", "")
                lines.append(f"- `{path}` - {desc}")
        else:
            lines.append("_See commit history for details_")
        lines.append("")
        
        lines.append("## Verification")
        if report and report.verification:
            if report.verification.get("commands_run"):
                lines.append("**Commands Run:**")
                for cmd in report.verification["commands_run"]:
                    lines.append(f"- `{cmd}`")
                lines.append("")
            if report.verification.get("results"):
                lines.append("**Results:**")
                for result in report.verification["results"]:
                    lines.append(f"- {result}")
        else:
            lines.append("- [ ] Tests pass")
            lines.append("- [ ] Acceptance criteria met")
        lines.append("")
        
        lines.append("## Checklist")
        lines.append("- [ ] Tests pass")
        lines.append("- [ ] Acceptance criteria met")
        lines.append("- [ ] No secrets committed")
        lines.append("- [ ] Documentation updated")
        
        return "\n".join(lines)
    
    def _create_pr(self, title: str, body: str, branch: str) -> Optional[dict]:
        """Create pull request."""
        if self.auth is None or self.repo is None:
            return None
        try:
            token = self.auth.token
            if self.auth.method == "gh_cli":
                cmd = [
                    "gh", "pr", "create",
                    "--repo", self.repo,
                    "--title", title,
                    "--body", body,
                    "--head", branch,
                    "--base", "main"
                ]
                
                # Try main first, then master
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                except subprocess.CalledProcessError:
                    cmd[-1] = "master"
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                url = result.stdout.strip()
                number = url.split("/")[-1]
                return {"number": int(number), "url": url}
            elif token:
                # Use API
                data = {
                    "title": title,
                    "body": body,
                    "head": branch,
                    "base": "main"
                }
                result = subprocess.run(
                    ["curl", "-s", "-X", "POST",
                     "-H", f"Authorization: token {token}",
                     "-H", "Accept: application/vnd.github.v3+json",
                     "-d", json.dumps(data),
                     f"https://api.github.com/repos/{self.repo}/pulls"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    # Try master
                    data["base"] = "master"
                    result = subprocess.run(
                        ["curl", "-s", "-X", "POST",
                         "-H", f"Authorization: token {token}",
                         "-H", "Accept: application/vnd.github.v3+json",
                         "-d", json.dumps(data),
                         f"https://api.github.com/repos/{self.repo}/pulls"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                
                pr = json.loads(result.stdout)
                return {
                    "number": pr["number"],
                    "url": pr["html_url"]
                }
        except Exception as e:
            print(f"❌ Failed to create PR: {e}", file=sys.stderr)
            return None
    
    def _update_ledger(self, task_id: str, issue_data: dict, pr_data: Optional[dict]):
        """Update agent ledger with GitHub URLs."""
        print("📒 Updating ledger...")
        
        ledger = {"version": 2, "tasks": []}
        if LEDGER_PATH.exists():
            try:
                with open(LEDGER_PATH) as f:
                    ledger = yaml.safe_load(f) or ledger
            except Exception:
                pass
        
        # Find or create task entry
        task_entry: dict[str, Any] | None = None
        for task in ledger.get("tasks", []):
            if isinstance(task, dict) and task.get("id") == task_id:
                task_entry = task
                break
        
        if not task_entry:
            task_entry = {"id": task_id}
            ledger.setdefault("tasks", []).append(task_entry)
        
        # Update fields
        task_entry["status"] = "completed"
        task_entry["github"] = {
            "issue_url": issue_data.get("url"),
            "issue_number": issue_data.get("number"),
            "branch": f"feature/{task_id}"
        }
        
        if pr_data:
            task_entry["github"]["pr_url"] = pr_data.get("url")
            task_entry["github"]["pr_number"] = pr_data.get("number")
        
        task_entry["completed"] = time.strftime("%Y-%m-%d")
        
        # Write back
        with open(LEDGER_PATH, "w") as f:
            yaml.dump(ledger, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Ledger updated: {LEDGER_PATH}")
    
    def _maybe_update_project_board(self, issue_data: dict):
        """Update project board if configured."""
        project_number = os.getenv("GITHUB_PROJECT_NUMBER")
        if not project_number or not issue_data.get("number"):
            return
        
        print(f"📋 Updating project board #{project_number}...")
        
        # This requires GraphQL API for new projects or REST for classic
        # Implementation depends on which project type you use
        print("⚠️  Project board integration not yet implemented")
        print("   Set GITHUB_PROJECT_NUMBER env var to enable")


def main():
    parser = argparse.ArgumentParser(
        description="GitHub integration for agent tasks"
    )
    parser.add_argument("task_id", help="Task ID (e.g., T001)")
    parser.add_argument("--skip-pr", action="store_true",
                        help="Skip PR creation (issue only)")
    parser.add_argument("--ci-mode", action="store_true",
                        help="Non-interactive mode (fails if no auth)")
    
    args = parser.parse_args()
    
    integrator = GitHubIntegrator(ci_mode=args.ci_mode)
    return integrator.run(args.task_id, skip_pr=args.skip_pr)


if __name__ == "__main__":
    sys.exit(main())
