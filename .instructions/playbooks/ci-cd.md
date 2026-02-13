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

## Sub-Agent Output
- Return ONLY the structured output format in the template
  `.instructions/templates/subagent_prompt.md`
- No conversational filler
- Master agent copies output into `.agent/reports/{task_id}.report.yaml`
- Validate with:
  - `python .instructions/scripts/validate_agent_report.py .agent/reports/`
  - `python .instructions/scripts/validate_agent_linkage.py`
