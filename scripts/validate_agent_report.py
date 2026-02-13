#!/usr/bin/env python3
"""
Validate sub-agent report YAML files against the repo's report contract.

Usage:
  python scripts/validate_agent_report.py reports/T123.report.yaml
  python scripts/validate_agent_report.py reports/
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


CONTRACT_PATH = Path("docs/agents/contracts/report.contract.yaml")


def _is_list_of_str(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def _fail(msg: str) -> int:
    print(f"❌ {msg}", file=sys.stderr)
    return 1


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_report(report: dict[str, Any], contract: dict[str, Any], report_path: Path) -> list[str]:
    errors: list[str] = []

    # Required top-level fields
    required = contract.get("required_fields", [])
    for k in required:
        if k not in report:
            errors.append(f"{report_path}: missing required field '{k}'")

    # Status enum
    status = report.get("status")
    allowed_status = contract.get("enums", {}).get("status", [])
    if status not in allowed_status:
        errors.append(f"{report_path}: status '{status}' not in {allowed_status}")

    # Summary constraints
    summary = report.get("summary")
    if not _is_list_of_str(summary):
        errors.append(f"{report_path}: 'summary' must be a list of strings")
    else:
        max_lines = contract.get("constraints", {}).get("summary_max_lines", 6)
        if summary is not None and len(summary) > max_lines:
            errors.append(f"{report_path}: 'summary' has {len(summary)} lines > {max_lines}")

    # Acceptance criteria results shape
    acr = report.get("acceptance_criteria_results")
    item_req = contract.get("acceptance_criteria_results_item", {}).get("required_fields", [])
    if not isinstance(acr, list) or not acr:
        errors.append(f"{report_path}: 'acceptance_criteria_results' must be a non-empty list")
    else:
        for i, item in enumerate(acr):
            if not isinstance(item, dict):
                errors.append(f"{report_path}: acceptance_criteria_results[{i}] must be a mapping")
                continue
            for k in item_req:
                if k not in item:
                    errors.append(f"{report_path}: acceptance_criteria_results[{i}] missing '{k}'")
            if "passed" in item and not isinstance(item["passed"], bool):
                errors.append(f"{report_path}: acceptance_criteria_results[{i}].passed must be boolean")

    # Files modified shape
    files = report.get("files_modified")
    if not isinstance(files, list):
        errors.append(f"{report_path}: 'files_modified' must be a list")
    else:
        for i, f in enumerate(files):
            if not isinstance(f, dict) or "path" not in f or "description" not in f:
                errors.append(f"{report_path}: files_modified[{i}] must have 'path' and 'description'")

    # Verification shape
    verification = report.get("verification")
    v_req = contract.get("verification", {}).get("required_fields", [])
    if not isinstance(verification, dict):
        errors.append(f"{report_path}: 'verification' must be a mapping")
    else:
        for k in v_req:
            if k not in verification:
                errors.append(f"{report_path}: verification missing '{k}'")
        if "commands_run" in verification and not _is_list_of_str(verification["commands_run"]):
            errors.append(f"{report_path}: verification.commands_run must be a list of strings")
        if "results" in verification and not _is_list_of_str(verification["results"]):
            errors.append(f"{report_path}: verification.results must be a list of strings")

    # Risks + next steps
    for k in ("risks", "next_steps"):
        if k in report and not _is_list_of_str(report[k]):
            errors.append(f"{report_path}: '{k}' must be a list of strings")

    return errors


def iter_report_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted([p for p in path.rglob("*.yaml") if p.is_file()])
    return [path]


def main(argv: list[str]) -> int:
    if not CONTRACT_PATH.exists():
        return _fail(f"Contract not found at {CONTRACT_PATH}")

    if len(argv) != 2:
        return _fail("Usage: python scripts/validate_agent_report.py <report.yaml or reports_dir>")

    target = Path(argv[1])
    if not target.exists():
        return _fail(f"Target not found: {target}")

    contract = load_yaml(CONTRACT_PATH)
    report_files = iter_report_files(target)

    all_errors: list[str] = []
    for rf in report_files:
        try:
            data = load_yaml(rf)
        except Exception as e:
            all_errors.append(f"{rf}: failed to parse YAML: {e}")
            continue

        if not isinstance(data, dict):
            all_errors.append(f"{rf}: top-level YAML must be a mapping/object")
            continue

        all_errors.extend(validate_report(data, contract, rf))

    if all_errors:
        print("Validation failed:\n" + "\n".join(all_errors), file=sys.stderr)
        return 1

    print(f"✅ Validated {len(report_files)} report file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
