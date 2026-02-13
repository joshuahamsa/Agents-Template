#!/usr/bin/env python3
"""
Validate linkage between tasks and reports.
Ensures every task has a corresponding report and vice versa.

Usage:
  python scripts/validate_agent_linkage.py
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


TASKS_DIR = Path(".agent/tasks")
REPORTS_DIR = Path(".agent/reports")
LEDGER_PATH = Path(".agent/ledger.yaml")


def _fail(msg: str) -> int:
    print(f"❌ {msg}", file=sys.stderr)
    return 1


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_task_ids(tasks_dir: Path) -> set[str]:
    """Extract task IDs from task files."""
    ids: set[str] = set()
    if not tasks_dir.exists():
        return ids
    for path in tasks_dir.rglob("*.yaml"):
        # Extract ID from filename (e.g., T001.yaml -> T001)
        task_id = path.stem
        ids.add(task_id)
    return ids


def get_report_ids(reports_dir: Path) -> set[str]:
    """Extract report IDs from report files."""
    ids: set[str] = set()
    if not reports_dir.exists():
        return ids
    for path in reports_dir.rglob("*.yaml"):
        # Extract ID from filename (e.g., T001.report.yaml -> T001)
        filename = path.stem
        if filename.endswith(".report"):
            report_id = filename[:-7]  # Remove .report suffix
            ids.add(report_id)
    return ids


def get_ledger_tasks(ledger_path: Path) -> set[str]:
    """Extract task IDs from ledger."""
    ids: set[str] = set()
    if not ledger_path.exists():
        return ids
    try:
        data = load_yaml(ledger_path)
        if isinstance(data, dict) and "tasks" in data:
            for task in data["tasks"]:
                if isinstance(task, dict) and "id" in task:
                    ids.add(task["id"])
    except Exception:
        pass
    return ids


def main(argv: list[str]) -> int:
    errors: list[str] = []

    task_ids = get_task_ids(TASKS_DIR)
    report_ids = get_report_ids(REPORTS_DIR)
    ledger_ids = get_ledger_tasks(LEDGER_PATH)

    # Tasks without reports
    tasks_without_reports = task_ids - report_ids
    if tasks_without_reports:
        for tid in sorted(tasks_without_reports):
            errors.append(f"Task '{tid}' has no corresponding report in {REPORTS_DIR}")

    # Reports without tasks
    reports_without_tasks = report_ids - task_ids
    if reports_without_tasks:
        for rid in sorted(reports_without_tasks):
            errors.append(f"Report '{rid}' has no corresponding task in {TASKS_DIR}")

    # Ledger consistency
    ledger_missing_tasks = task_ids - ledger_ids
    if ledger_missing_tasks:
        for tid in sorted(ledger_missing_tasks):
            errors.append(f"Task '{tid}' is not recorded in {LEDGER_PATH}")

    if errors:
        print("Linkage validation failed:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"✅ Linkage validated: {len(task_ids)} tasks, {len(report_ids)} reports, {len(ledger_ids)} ledger entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
