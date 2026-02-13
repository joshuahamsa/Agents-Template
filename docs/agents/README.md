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
