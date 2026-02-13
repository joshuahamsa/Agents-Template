# Agent System Overview

This repository uses a modular, test-first, sub-agent architecture.

Goals:
- Minimize context window bloat
- Enforce decomposition
- Ensure verification before merge
- Maintain deterministic outputs

Master agents act as:
- Task routers
- Ledger keepers
- Merge coordinators

Sub-agents:
- Execute narrowly scoped tasks
- Operate under a single playbook
- Return structured reports only

## Delegation Workflow
1. Create a task file in `.agent/tasks/` (see task contract).
2. Dispatch a sub-agent using `.instructions/templates/subagent_prompt.md`.
3. Save the sub-agent response as `.agent/reports/{task_id}.report.yaml`.
4. Validate artifacts:
   - `python .instructions/scripts/validate_agent_task.py .agent/tasks/`
   - `python .instructions/scripts/validate_agent_report.py .agent/reports/`
   - `python .instructions/scripts/validate_agent_linkage.py`

## Worked Example (Skeleton)

Task file: `.agent/tasks/T010.yaml`
```yaml
task_id: T010
title: Add delegation notes
goal: Document sub-agent delegation flow
context: |
  Keep context under 10 lines.
inputs:
  - AGENTS.md
outputs:
  - Updated delegation section
acceptance_criteria:
  - Delegation steps documented
routing:
  playbook: .instructions/playbooks/docs.md
  contracts:
    - .instructions/contracts/task.contract.yaml
    - .instructions/contracts/report.contract.yaml
    - .instructions/contracts/test.contract.yaml
```

Sub-agent output saved as: `.agent/reports/T010.report.yaml`
```yaml
task_id: T010
status: success
summary:
  - Added delegation steps and validation commands
acceptance_criteria_results:
  - criterion: Delegation steps documented
    passed: true
    evidence: AGENTS.md updated with delegation protocol
changes_made:
  - Documented sub-agent workflow
files_modified:
  - path: AGENTS.md
    description: Added delegation protocol section
verification:
  commands_run:
    - python .instructions/scripts/validate_agent_task.py .agent/tasks/
  results:
    - All task files validated
risks:
  - None
next_steps:
  - None
```
