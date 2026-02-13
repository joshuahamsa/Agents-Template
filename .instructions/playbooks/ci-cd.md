# CI/CD Playbook

## When To Use
- GitHub Actions
- Release workflows
- Security scans
- Build pipelines

## Acceptance Criteria
- Workflow triggers defined
- Jobs deterministic
- No secrets hardcoded
- Fail-fast enabled

## Rules
- Use matrix builds when appropriate
- Cache dependencies
- Pin versions
- Minimal permissions

## Verification
- Workflow syntax valid
- Jobs simulate successfully
- Required checks enforced
