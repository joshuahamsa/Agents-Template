# Python Playbook

## When To Use
- New modules
- Refactors
- Utility scripts
- Backend logic

## Acceptance Criteria Must Include
- Function signatures defined
- Type hints required
- Tests created or updated
- Edge cases enumerated

## Testing Rules
- Use pytest
- Test happy path
- Test edge cases
- Test failure cases

## Implementation Constraints
- No global state unless justified
- Pure functions preferred
- Explicit imports
- Avoid side effects

## Verification
- pytest passes
- Lint passes (ruff/flake8 if applicable)
- Type check passes (mypy/pyright if applicable)
- No new warnings

## Post-Completion: GitHub Integration

After implementation and verification pass, complete GitHub integration:

### Automated Steps
```bash
# Run GitHub integrator (handles auth, issue, PR creation)
python .instructions/scripts/github_integrator.py {task_id}
```

This will:
1. Check GitHub authentication (prompts if needed)
2. Create or update GitHub Issue with task details
3. Create branch: `feature/{task_id}-{description}`
4. Commit changes with conventional commits format
5. Push branch to remote
6. Create Pull Request linking to issue
7. Auto-request CODEOWNERS review
8. Update agent ledger with GitHub URLs

### Manual Steps (if automation skipped)
```bash
# Create branch
git checkout -b feature/{task_id}-{description}

# Commit with conventional format
git commit -m "feat({task_id}): description"
git commit -m "fix({task_id}): description"

# Push and create PR manually
git push -u origin feature/{task_id}-{description}
gh pr create --title "[{task_id}] Task Title"

# Update ledger manually
cat >> .agent/ledger.yaml << EOF
  - id: {task_id}
    status: completed
    github:
      issue_url: https://github.com/user/repo/issues/X
      pr_url: https://github.com/user/repo/pull/Y
      branch: feature/{task_id}-{description}
EOF
```

### Required GitHub Artifacts
- [ ] Issue: `[{task_id}] {task_title}` with acceptance criteria
- [ ] Branch: `feature/{task_id}-{short-description}`
- [ ] PR: Links to issue, includes verification steps
- [ ] Reviewers: CODEOWNERS auto-assigned
- [ ] CI: Running on PR

### First Time Setup
If GitHub integration fails due to auth:
```bash
# Option 1: Use GitHub CLI
gh auth login

# Option 2: Set token
export GITHUB_TOKEN=ghp_your_token_here
# Create at: https://github.com/settings/tokens
# Required scopes: repo, workflow
```

See full details: `.instructions/playbooks/github-integration.md`
