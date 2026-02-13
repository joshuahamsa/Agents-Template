# Documentation Playbook

## When To Use
- README updates
- API documentation
- Playbooks and contracts
- Architecture notes

## Acceptance Criteria
- Scope of change clearly documented
- Terminology consistent with repo
- Examples use repo paths and contracts
- No secrets in examples

## Rules
- Prefer concise, actionable prose
- Avoid full file dumps
- Use diffs or short excerpts

## Verification
- Links and paths resolve
- Examples match current repository structure

## Sub-Agent Output
- Return ONLY the structured output format in the template
  `.instructions/templates/subagent_prompt.md`
- No conversational filler
- Master agent copies output into `.agent/reports/{task_id}.report.yaml`
- Validate with:
  - `python .instructions/scripts/validate_agent_report.py .agent/reports/`
  - `python .instructions/scripts/validate_agent_linkage.py`
