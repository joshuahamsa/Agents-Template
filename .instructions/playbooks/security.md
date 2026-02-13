# Security Playbook

## Required Checks
- No secrets committed
- Input validation enforced
- No unsafe eval / exec
- Dependency audit reviewed

## For Auth
- Token validation explicit
- Expiration handled
- Scope checked

## Sub-Agent Output
- Return ONLY the structured output format in the template
  `.instructions/templates/subagent_prompt.md`
- No conversational filler
- Master agent copies output into `.agent/reports/{task_id}.report.yaml`
- Validate with:
  - `python .instructions/scripts/validate_agent_report.py .agent/reports/`
  - `python .instructions/scripts/validate_agent_linkage.py`
