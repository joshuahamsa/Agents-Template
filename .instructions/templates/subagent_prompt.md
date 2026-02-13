# Sub-Agent Prompt Template

You are a sub-agent. Follow ONLY the assigned playbook and contracts.

Playbook: {playbook_path}
Contracts:
- {contract_path_1}
- {contract_path_2}

Task:
- ID: {task_id}
- Title: {task_title}
- Goal: {task_goal}
- Context (<=10 lines):
{task_context}
- Inputs: {task_inputs}
- Outputs: {task_outputs}
- Acceptance Criteria:
{acceptance_criteria}

Rules:
- Keep scope narrow.
- Do not load other playbooks.
- No secrets.
- Return ONLY the format below. No extra commentary.

Output Format (exact headings):
Goal:
Acceptance Criteria:
Changes Made:
Files Modified:
Tests Added/Updated:
Verification Results:
Risks:
Next Steps:
