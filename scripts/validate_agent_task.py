#!/usr/bin/env python3
"""
Validate sub-agent task YAML files against the repo's task contract.

Usage:
  python scripts/validate_agent_task.py .agent/tasks/T001.yaml
  python scripts/validate_agent_task.py .agent/tasks/
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # PyYAML
except ImportError as e:
    print("ERROR: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
    raise


CONTRACT_PATH = Path("docs/agents/contracts/task.contract.yaml")


def _is_list_of_str(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def _fail(msg: str) -> int:
    print(f"❌ {msg}", file=sys.stderr)
    return 1


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_task(task: dict[str, Any], contract: dict[str, Any], task_path: Path) -> list[str]:
    errors: list[str] = []

    # Required top-level fields
    required = contract.get("required_fields", [])
    for k in required:
        if k not in task:
            errors.append(f"{task_path}: missing required field '{k}'")

    # Check context length (recommended <= 10 lines)
    context = task.get("context")
    if isinstance(context, str):
        lines = len(context.splitlines())
        if lines > 10:
            errors.append(f"{task_path}: context has {lines} lines (recommended <= 10)")

    # Validate inputs/outputs are lists of strings
    for field in ("inputs", "outputs"):
        val = task.get(field)
        if val is not None and not _is_list_of_str(val):
            errors.append(f"{task_path}: '{field}' must be a list of strings")

    # Validate acceptance_criteria is a list of strings
    ac = task.get("acceptance_criteria")
    if ac is not None:
        if not _is_list_of_str(ac):
            errors.append(f"{task_path}: 'acceptance_criteria' must be a list of strings")
        elif len(ac) == 0:
            errors.append(f"{task_path}: 'acceptance_criteria' must not be empty")

    # Validate routing section
    routing = task.get("routing")
    if routing is not None:
        if not isinstance(routing, dict):
            errors.append(f"{task_path}: 'routing' must be a mapping")
        else:
            if "playbook" not in routing:
                errors.append(f"{task_path}: 'routing.playbook' is required")
            if "contracts" not in routing:
                errors.append(f"{task_path}: 'routing.contracts' is required")
            elif not _is_list_of_str(routing.get("contracts", [])):
                errors.append(f"{task_path}: 'routing.contracts' must be a list of strings")

    return errors


def iter_task_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted([p for p in path.rglob("*.yaml") if p.is_file()])
    return [path]


def main(argv: list[str]) -> int:
    if not CONTRACT_PATH.exists():
        return _fail(f"Contract not found at {CONTRACT_PATH}")

    if len(argv) != 2:
        return _fail("Usage: python scripts/validate_agent_task.py <task.yaml or tasks_dir>")

    target = Path(argv[1])
    if not target.exists():
        return _fail(f"Target not found: {target}")

    contract = load_yaml(CONTRACT_PATH)
    if not isinstance(contract, dict):
        return _fail(f"Contract at {CONTRACT_PATH} must be a YAML mapping")

    task_files = iter_task_files(target)

    all_errors: list[str] = []
    for tf in task_files:
        try:
            data = load_yaml(tf)
        except Exception as e:
            all_errors.append(f"{tf}: failed to parse YAML: {e}")
            continue

        if not isinstance(data, dict):
            all_errors.append(f"{tf}: top-level YAML must be a mapping/object")
            continue

        all_errors.extend(validate_task(data, contract, tf))

    if all_errors:
        print("Validation failed:\n" + "\n".join(all_errors), file=sys.stderr)
        return 1

    print(f"✅ Validated {len(task_files)} task file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
