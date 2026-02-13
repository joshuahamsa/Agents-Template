# <Playbook Name>

## When To Use

Describe the category of tasks governed by this playbook.

Examples:
- New feature implementation
- Refactoring
- Infrastructure changes
- Documentation updates

---

## Required Inputs

- File paths involved
- Relevant configuration
- Constraints (performance, security, backward compatibility)
- Existing test coverage status

---

## Task Decomposition Requirements

Before implementation:

1. Break task into smallest independently testable units.
2. Each unit must:
   - Have a clear goal
   - Have explicit acceptance criteria
   - Be verifiable independently

Large tasks must be split.

---

## Acceptance Criteria Template

For each subtask define:

- Functional expectations:
- Edge cases:
- Failure cases:
- Performance constraints:
- Backward compatibility requirements:

---

## Implementation Rules

- Scope changes narrowly.
- Do not refactor unrelated code.
- Follow repository style conventions.
- Prefer explicit logic over clever abstractions.
- Avoid introducing hidden state.

---

## Verification Requirements

At minimum:

- Tests added or updated (if applicable)
- All tests pass
- Lint passes
- No new warnings
- No debug artifacts

If testing is not applicable:
- Provide manual verification checklist.

---

## Sub-Agent Output Format

Return ONLY:

Goal:
Acceptance Criteria:
Changes Made:
Files Modified:
Tests Added/Updated:
Verification Results:
Risks:
Next Steps:

No conversational filler.
Master agent copies output into `.agent/reports/{task_id}.report.yaml` and validates:
- `python .instructions/scripts/validate_agent_report.py .agent/reports/`
- `python .instructions/scripts/validate_agent_linkage.py`
