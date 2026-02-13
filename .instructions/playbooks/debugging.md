# Debugging Playbook

## Steps

1. Reproduce issue.
2. Isolate minimal failing unit.
3. Write failing test first.
4. Implement fix.
5. Confirm fix resolves issue without regressions.

## Rules
- Do not rewrite entire module
- Fix smallest responsible unit
- Add regression test

## Sub-Agent Output
- Return ONLY the structured output format in the template
  `.instructions/templates/subagent_prompt.md`
- No conversational filler
- Master agent copies output into `.agent/reports/{task_id}.report.yaml`
- Validate with:
  - `python .instructions/scripts/validate_agent_report.py .agent/reports/`
  - `python .instructions/scripts/validate_agent_linkage.py`
