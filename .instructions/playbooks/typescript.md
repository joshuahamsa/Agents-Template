# TypeScript / JS Playbook

## When To Use
- Frontend components
- Node services
- Utility libraries

## Acceptance Criteria
- Types defined (no implicit any)
- Public APIs documented
- Edge cases handled
- Unit tests added

## Rules
- Strict typing enabled
- No console logs in production code
- No unused exports
- Prefer functional components

## Verification
- tsc passes
- Tests pass
- Lint passes

## Sub-Agent Output
- Return ONLY the structured output format in the template
  `.instructions/templates/subagent_prompt.md`
- No conversational filler
- Master agent copies output into `.agent/reports/{task_id}.report.yaml`
- Validate with:
  - `python .instructions/scripts/validate_agent_report.py .agent/reports/`
  - `python .instructions/scripts/validate_agent_linkage.py`
