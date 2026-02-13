# GitHub Integration Playbook

## When To Use

**AFTER** completing any code task and passing verification.

This playbook orchestrates the automated creation of GitHub Issues, Pull Requests, and project board updates to maintain full traceability.

## Prerequisites

- Task verification passed (acceptance criteria met)
- Changes staged or committed locally
- GitHub write access available

## Quick Start

```bash
# Run after task completion
python .instructions/scripts/github_integrator.py T001

# The script will:
# 1. Check GitHub authentication
# 2. Create or update GitHub Issue
# 3. Create branch: feature/T001-short-description
# 4. Commit with conventional commit format
# 5. Push to remote
# 6. Create Pull Request
# 7. Auto-request CODEOWNERS review
# 8. Update agent ledger
```

## Detailed Workflow

### Phase 1: Authentication Check

The script automatically detects GitHub authentication:

#### Option A: GitHub CLI (Recommended)
```bash
# Check if authenticated
gh auth status

# If not authenticated:
gh auth login
# Follow prompts for HTTPS or SSH
```

#### Option B: Personal Access Token
```bash
# Create token at: https://github.com/settings/tokens
# Required scopes: repo, workflow

# Set environment variable
export GITHUB_TOKEN=ghp_your_token_here

# Or store in .env.local (gitignored)
echo "GITHUB_TOKEN=ghp_your_token_here" > .env.local
```

#### Option C: Skip Integration
If no auth is detected, the script will prompt:
```
🔐 GitHub Authentication Required

Options:
1. Use GitHub CLI (recommended) - Run: gh auth login
2. Provide Personal Access Token
3. Skip GitHub integration (complete locally only)

Enter choice (1/2/3): 
```

**Selecting option 3** allows task completion without GitHub integration. You can manually create issue/PR later.

### Phase 2: Issue Creation

The script searches for existing issues with the task ID:

- **If found**: Updates issue body with latest report
- **If not found**: Creates new issue using template

**Issue Details:**
- **Title**: `[T001] Task Title`
- **Labels**: `agent-task`, `automation`
- **Body** includes:
  - Task goal and context
  - Acceptance criteria
  - Implementation summary (from report)
  - Verification results
  - Files modified
  - Link to PR (after creation)

### Phase 3: Branch Creation

**Branch Naming Convention:**
```
feature/{task_id}-{short-description}
```

Examples:
```
feature/T001-initial-setup
feature/BUG-003-fix-type-errors
feature/FEAT-042-add-user-auth
```

**Rules:**
- Max 50 characters total
- Lowercase with hyphens
- No special characters except hyphens
- Based on task title, auto-generated

### Phase 4: Committing Changes

**Conventional Commit Format:**
```
feat(T001): add user authentication

- Implement JWT token validation
- Add login/logout endpoints
- Include error handling

Closes #42
```

**Commit Types (auto-detected from task):**
- `feat`: New feature implementation
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting
- `refactor`: Code restructuring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Auto-generated footer:**
- Always includes `Closes #{issue_number}`

### Phase 5: Pull Request Creation

**PR Details:**
- **Branch**: `feature/T001-description`
- **Target**: Default branch (main/master)
- **Title**: Same as issue: `[T001] Task Title`
- **Template**: `.instructions/templates/PULL_REQUEST_TEMPLATE.md`
- **Reviewers**: Auto-assigned from CODEOWNERS

**PR Body Auto-populated with:**
- Task summary
- Changes list (from report)
- Verification steps
- Checklist

### Phase 6: Project Board (Optional)

Only enabled if `GITHUB_PROJECT_NUMBER` is set:

```bash
# Enable project board integration
export GITHUB_PROJECT_NUMBER=1
```

When enabled:
- Adds issue to project board
- Sets status to "In Review"

### Phase 7: CI Trigger

Creating the PR automatically triggers:
- Standard CI workflow (tests, lint)
- Extended validation workflow
- Status checks on PR

### Phase 8: Ledger Update

The script updates `.agent/ledger.yaml`:

```yaml
tasks:
  - id: T001
    status: completed
    github:
      issue_url: https://github.com/user/repo/issues/42
      issue_number: 42
      pr_url: https://github.com/user/repo/pull/43
      pr_number: 43
      branch: feature/T001-initial-setup
    completed: "2024-01-15"
```

## Error Handling

| Scenario | Action |
|----------|--------|
| **No GitHub token** | Interactive prompt for auth method |
| **Token lacks permissions** | Log specific missing scopes, offer skip |
| **Issue creation fails** | Log error, continue with branch/PR |
| **Branch exists** | Reuse existing branch, add commits |
| **PR already exists** | Update PR description with latest |
| **Push rejected** | Pull with rebase, retry push |
| **Rate limited** | Exponential backoff, max 3 retries |
| **CODEOWNERS missing** | Create PR without reviewers |

## CI Mode

When running in GitHub Actions (CI=true):
- Uses `GITHUB_TOKEN` from environment
- Non-interactive (fails if no auth)
- Creates PRs but doesn't prompt
- Logs all actions for debugging

## Manual Override

If automated integration fails or you prefer manual control:

```bash
# Create issue manually
gh issue create --title "[T001] Task Title" \
                --label "agent-task,automation" \
                --body-file .agent/tasks/T001.yaml

# Create branch and push
git checkout -b feature/T001-description
git add .
git commit -m "feat(T001): task description"
git push -u origin feature/T001-description

# Create PR
gh pr create --title "[T001] Task Title" \
             --body "Closes #{issue_number}"

# Update ledger manually, then validate
python .instructions/scripts/validate_agent_linkage.py
```

## Success Criteria

- [ ] Issue created with `[{task_id}]` prefix
- [ ] Branch created with `feature/{task_id}-*` format
- [ ] Commits use conventional commit format
- [ ] PR created linking to issue
- [ ] CODEOWNERS auto-assigned as reviewers
- [ ] CI running on PR
- [ ] Ledger updated with GitHub URLs
- [ ] All changes pushed to remote

## Verification

After integration completes, verify:

```bash
# Check GitHub Issue exists
gh issue view {issue_number}

# Check PR exists and is linked
gh pr view {pr_number}

# Check ledger updated
cat .agent/ledger.yaml | grep -A5 "id: T001"

# Validate linkage
python .instructions/scripts/validate_agent_linkage.py
```

## Troubleshooting

### "No GitHub authentication detected"
Run `gh auth login` or set `GITHUB_TOKEN` environment variable.

### "Permission denied" errors
Your token needs `repo` and `workflow` scopes. Create new token at GitHub Settings > Developer Settings > Personal Access Tokens.

### "Branch already exists"
The script will reuse the existing branch and add new commits. This is expected if re-running integration.

### "PR creation failed"
Check if:
- Branch was pushed successfully
- Base branch exists (main/master)
- You have permission to create PRs

### "CODEOWNERS not found"
Create `.github/CODEOWNERS` file or the script will skip auto-assignment:
```
* @username
```

## Integration with Other Playbooks

### Python Playbook
After completing Python task:
1. Run tests: `pytest`
2. Run linter: `ruff check .`
3. Run integrator: `python .instructions/scripts/github_integrator.py T001`

### TypeScript Playbook
After completing TypeScript task:
1. Run tests: `npm test`
2. Run typecheck: `tsc --noEmit`
3. Run integrator: `python .instructions/scripts/github_integrator.py T001`

### CI/CD Playbook
Integration is automatic when:
- Workflow triggers on `feature/*` branch push
- Uses `GITHUB_TOKEN` for authentication
- Runs extended validation checks

## Best Practices

1. **Always verify before integrating** - Don't push failing code
2. **Use descriptive task titles** - They become issue/PR titles
3. **Keep acceptance criteria clear** - They populate issue body
4. **Write good commit messages** - First line becomes PR title
5. **Update ledger immediately** - Don't delay, prevents desync
6. **Check CI status** - Red CI blocks merge
7. **Request reviews promptly** - Don't let PRs sit idle

## Related Files

- Contract: `.instructions/contracts/github-integration.contract.yaml`
- Script: `.instructions/scripts/github_integrator.py`
- Helper: `.instructions/scripts/check_github_auth.py`
- Workflow: `.github/workflows/post-task-integration.yml`
- Template PR: `.instructions/templates/PULL_REQUEST_TEMPLATE.md`
- Template Issue: `.instructions/templates/agent_task.md`
