# AGENTS.md

## 1. Repo Purpose
<2–5 sentence description of what this repository does and who it serves.>

## 2. Repository Map
- src/              → application source code
- tests/            → automated tests
- .instructions/    → agent system (playbooks, contracts, scripts)
- .github/          → GitHub-specific config (CODEOWNERS, minimal)
- .agent/           → task tracking (tasks, reports, ledger)

## 3. Global Invariants (Always True)
- Tasks MUST be decomposed into smallest independently testable units.
- Sub-agents MUST define acceptance criteria before implementation.
- No secrets in code or logs.
- Prefer minimal diffs over large rewrites.
- Behavior changes require updated tests and documentation.
- Never paste full files unless explicitly required — use diffs or excerpts.

## 4. Default Execution Protocol

1. Restate task in ≤ 5 lines.
2. Decompose into smallest coherent subtasks.
3. For each subtask:
   - Define acceptance criteria ("tests").
   - Implement.
   - Verify.
   - Report results.
4. Keep master context lean:
   - Store only decisions, outputs, and next steps.
   - Avoid conversational drift.

## 5. Sub-Agent Delegation Protocol

1. Create a task file in `.agent/tasks/` using the task contract.
2. Keep `context` to 10 lines or fewer.
3. Choose the playbook and contracts for the subtask.
4. Dispatch a sub-agent using `.instructions/templates/subagent_prompt.md`.
5. Sub-agent returns ONLY the structured output format (no extra prose).
6. Copy the output into `.agent/reports/{task_id}.report.yaml`.
7. Validate artifacts:
   - `python .instructions/scripts/validate_agent_task.py .agent/tasks/`
   - `python .instructions/scripts/validate_agent_report.py .agent/reports/`
   - `python .instructions/scripts/validate_agent_linkage.py`

## 6. Routing Table

| Task Type | Playbook |
|-----------|----------|
| Python implementation | .instructions/playbooks/python.md |
| TypeScript / JS | .instructions/playbooks/typescript.md |
| CI / GitHub Actions | .instructions/playbooks/ci-cd.md |
| Documentation | .instructions/playbooks/docs.md |
| Debugging | .instructions/playbooks/debugging.md |
| Security / Auth | .instructions/playbooks/security.md |
| GitHub Integration | .instructions/playbooks/github-integration.md |

Agents MUST load only the relevant playbook.

## 7. Definition of Done (Universal)
- Acceptance criteria met
- Tests/verifiers pass
- Diff summary provided
- Risks noted
- Next subtasks identified (if applicable)

## 8. Context Budget Rule
- Task recap ≤ 10 lines
- Do not paste large files
- Use path references + diffs
- Summaries over repetition

## Contract Loading Rule
Agents MUST load only the contracts needed for the task.

Default contracts:
- .instructions/contracts/task.contract.yaml
- .instructions/contracts/report.contract.yaml
- .instructions/contracts/test.contract.yaml

Domain contracts are optional and task-specific.

## 9. Runtime Notes (Platform Appendix)

### OpenCode
If the `Task` tool is available, use it to spawn sub-agents with the template
in `.instructions/templates/subagent_prompt.md`. If the tool is not available,
run the subtask in a separate session (or manual worker) and still require the
same report format and validation steps.

## 10. Code Task Completion Protocol (GitHub Integration)

All code tasks MUST complete GitHub integration after verification passes.

### Automated Workflow

Run the GitHub integrator immediately after completing a code task:

```bash
python .instructions/scripts/github_integrator.py {task_id}
```

This single command will:

1. **Authentication Check** - Verifies `gh` CLI auth or `GITHUB_TOKEN` env var
2. **Issue Management** - Creates/updates GitHub Issue with task details
3. **Branch Creation** - Creates `feature/{task_id}-{description}` branch
4. **Commit Changes** - Uses conventional commit format
5. **Push & PR** - Pushes branch and creates Pull Request
6. **Auto-Review** - Requests CODEOWNERS review
7. **Ledger Update** - Records GitHub URLs in `.agent/ledger.yaml`

### GitHub Artifacts Required

- [ ] **Issue**: `[{task_id}] {task_title}` with acceptance criteria
- [ ] **Branch**: `feature/{task_id}-{short-description}`
- [ ] **Commit**: Conventional commit format (`feat:`, `fix:`, etc.)
- [ ] **PR**: Links to issue, includes verification steps
- [ ] **Reviewers**: CODEOWNERS auto-assigned
- [ ] **CI**: Running on PR

### First Time Setup

If GitHub integration fails due to missing authentication:

```bash
# Option 1: Use GitHub CLI (recommended)
gh auth login

# Option 2: Set token
export GITHUB_TOKEN=ghp_your_token_here
# Create at: https://github.com/settings/tokens
# Required scopes: repo, workflow
```

Verify authentication:
```bash
python .instructions/scripts/check_github_auth.py --verbose
```

### Skip Integration

To complete a task without GitHub integration:

```bash
python .instructions/scripts/github_integrator.py T001 --skip-pr
```

This creates the Issue only (no PR). Useful for tracking tasks that don't need code changes.

### CI/CD Integration

The workflow `.github/workflows/post-task-integration.yml` automatically:
- Detects task IDs from branch names
- Runs integration in CI mode
- Validates ledger updates
- Posts status comments on PRs

Triggers on:
- Push to `feature/*` branches
- Pull request events

### Manual Override

If automation fails, create artifacts manually:

```bash
# Create branch
git checkout -b feature/T001-description

# Commit with conventional format
git commit -m "feat(T001): add user authentication"

# Push and create PR manually
git push -u origin feature/T001-description
gh pr create --title "[T001] Task Title" --body "Closes #{issue}"

# Update ledger manually
```

### Success Criteria

A code task is only complete when:
- ✅ All acceptance criteria verified
- ✅ GitHub Issue exists with task ID
- ✅ PR created linking to issue
- ✅ Branch pushed to remote
- ✅ CODEOWNERS assigned
- ✅ CI passing
- ✅ Ledger updated with GitHub refs

### Related Files

- **Playbook**: `.instructions/playbooks/github-integration.md`
- **Contract**: `.instructions/contracts/github-integration.contract.yaml`
- **Integrator**: `.instructions/scripts/github_integrator.py`
- **Auth Check**: `.instructions/scripts/check_github_auth.py`
- **Workflow**: `.github/workflows/post-task-integration.yml`
- **PR Template**: `.instructions/templates/PULL_REQUEST_TEMPLATE.md`
- **Issue Template**: `.instructions/templates/agent_task.md`
