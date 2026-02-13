# Agent Routing Reference

This file expands on the routing table in AGENTS.md.

Agents MUST:
- Load only the relevant playbook.
- Avoid loading multiple playbooks unless the task explicitly spans domains.
- If multiple domains apply, decompose into separate subtasks and spawn sub-agents.

---

## Primary Routing Rules

### Python Work
Use: playbooks/python.md  
Includes:
- New modules
- Refactors
- CLI tools
- Backend services
- Data processing scripts

---

### TypeScript / JavaScript
Use: playbooks/typescript.md  
Includes:
- Frontend components
- Node services
- Utility libraries
- Build tooling

---

### CI/CD
Use: playbooks/ci-cd.md  
Includes:
- GitHub Actions
- Deployment pipelines
- Security scans
- Release workflows

---

### Documentation
Use: playbooks/docs.md  
Includes:
- README updates
- API docs
- ADRs
- Changelogs

---

### Debugging / Incidents
Use: playbooks/debugging.md  
Includes:
- Reproducing bugs
- Writing regression tests
- Root cause analysis

---

### Security / Auth
Use: playbooks/security.md  
Includes:
- Authentication flows
- Token validation
- Secret handling
- Dependency audits

---

## Decomposition Rule

If a task touches multiple domains:

1. Break into independent subtasks.
2. Spawn sub-agents per domain.
3. Merge only verified outputs.
