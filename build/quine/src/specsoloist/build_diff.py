"""General-purpose tool for comparing build outputs produced from specs."""

from __future__ import annotations

import ast
import difflib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from specsoloist import ui


@dataclass
class DiffResult:
    """Result of a comparison for a single file path."""

    path: str
    status: str  # PASS, FAIL, MISSING_LEFT, MISSING_RIGHT
    diff: Optional[str] = None


@dataclass
class DiffSummary:
    """Overall summary of a directory comparison."""

    passed: int = 0
    failed: int = 0
    missing_left: int = 0
    missing_right: int = 0
    results: list[DiffResult] = field(default_factory=list)
    label_left: str = "left"
    label_right: str = "right"


@dataclass
class BuildRun:
    """Metadata describing a single recorded build run."""

    run_id: str
    path: str
    timestamp: str
    arrangement: Optional[str] = None
    meta: dict = field(default_factory=dict)


# Patterns to ignore during comparison
_IGNORE_PATTERNS = {
    "__pycache__",
    ".git",
    "node_modules",
    ".DS_Store",
    "run_meta.json",
}
_IGNORE_EXTENSIONS = {".pyc"}
_IGNORE_SPEC = ".spec.md"


def normalize_source(content: str, filename: str) -> str:
    """Reduce source code to canonical semantic form."""
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".py":
        # Try AST-based normalization
        try:
            tree = ast.parse(content)
            # Remove docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                    if (node.body and isinstance(node.body[0], ast.Expr)
                            and isinstance(node.body[0].value, ast.Constant)
                            and isinstance(node.body[0].value.value, str)):
                        node.body.pop(0)
                        if not node.body:
                            node.body.append(ast.Pass())
            return ast.unparse(tree)
        except SyntaxError:
            # Fallback: strip # comments and normalize whitespace
            lines = []
            for line in content.split("\n"):
                stripped = re.sub(r"\s*#.*$", "", line).rstrip()
                lines.append(stripped)
            return "\n".join(line for line in lines if line.strip())

    elif ext in (".ts", ".tsx", ".js", ".mjs"):
        # Strip // line comments and /* */ block comments
        content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        # Normalize whitespace
        lines = [line.rstrip() for line in content.split("\n")]
        return "\n".join(line for line in lines if line.strip())

    else:
        # Normalize line endings and strip trailing whitespace
        lines = [line.rstrip() for line in content.replace("\r\n", "\n").split("\n")]
        return "\n".join(lines)


def compare_files(left_path: str, right_path: str, relative_path: str) -> DiffResult:
    """Compare two files at arbitrary absolute paths."""
    left_exists = os.path.exists(left_path)
    right_exists = os.path.exists(right_path)

    if not left_exists:
        return DiffResult(path=relative_path, status="MISSING_LEFT")

    if not right_exists:
        return DiffResult(path=relative_path, status="MISSING_RIGHT")

    filename = os.path.basename(relative_path)

    try:
        with open(left_path) as f:
            left_content = f.read()
        with open(right_path) as f:
            right_content = f.read()
    except UnicodeDecodeError:
        # Binary files: byte-by-byte comparison
        with open(left_path, "rb") as f:
            left_bytes = f.read()
        with open(right_path, "rb") as f:
            right_bytes = f.read()
        if left_bytes == right_bytes:
            return DiffResult(path=relative_path, status="PASS")
        else:
            return DiffResult(path=relative_path, status="FAIL", diff="Binary files differ")

    left_norm = normalize_source(left_content, filename)
    right_norm = normalize_source(right_content, filename)

    if left_norm == right_norm:
        return DiffResult(path=relative_path, status="PASS")

    # Generate unified diff of original content
    diff = "".join(difflib.unified_diff(
        left_content.splitlines(keepends=True),
        right_content.splitlines(keepends=True),
        fromfile=f"left/{relative_path}",
        tofile=f"right/{relative_path}",
    ))
    return DiffResult(path=relative_path, status="FAIL", diff=diff)


def _should_ignore(path: str) -> bool:
    """Check if a path should be ignored."""
    parts = path.replace("\\", "/").split("/")
    for part in parts:
        if part in _IGNORE_PATTERNS:
            return True
    if path.endswith(_IGNORE_SPEC):
        return True
    _, ext = os.path.splitext(path)
    if ext in _IGNORE_EXTENSIONS:
        return True
    return False


def compare_directories(
    left_dir: str,
    right_dir: str,
    label_left: str = "left",
    label_right: str = "right",
) -> DiffSummary:
    """Recursively compare two directories."""
    summary = DiffSummary(label_left=label_left, label_right=label_right)

    # Collect all files from both directories
    def collect_files(base_dir: str) -> set[str]:
        files = set()
        if not os.path.exists(base_dir):
            return files
        for root, dirs, filenames in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in _IGNORE_PATTERNS and not d.startswith(".")]
            for fname in filenames:
                full_path = os.path.join(root, fname)
                rel = os.path.relpath(full_path, base_dir)
                if not _should_ignore(rel):
                    files.add(rel)
        return files

    left_files = collect_files(left_dir)
    right_files = collect_files(right_dir)
    all_files = sorted(left_files | right_files)

    for rel_path in all_files:
        left_path = os.path.join(left_dir, rel_path)
        right_path = os.path.join(right_dir, rel_path)
        result = compare_files(left_path, right_path, rel_path)
        summary.results.append(result)

        if result.status == "PASS":
            summary.passed += 1
        elif result.status == "FAIL":
            summary.failed += 1
        elif result.status == "MISSING_LEFT":
            summary.missing_left += 1
        elif result.status == "MISSING_RIGHT":
            summary.missing_right += 1

    return summary


def list_build_runs(build_dir: str) -> list[BuildRun]:
    """Discover and return all recorded build runs under build_dir."""
    if not os.path.exists(build_dir):
        return []

    runs = []
    for entry in os.scandir(build_dir):
        if not entry.is_dir():
            continue
        meta_path = os.path.join(entry.path, "run_meta.json")
        if not os.path.exists(meta_path):
            continue
        try:
            with open(meta_path) as f:
                data = json.load(f)
            if "run_id" not in data or "timestamp" not in data:
                continue
            run = BuildRun(
                run_id=data["run_id"],
                path=entry.path,
                timestamp=data["timestamp"],
                arrangement=data.get("arrangement"),
                meta={k: v for k, v in data.items()
                      if k not in ("run_id", "timestamp", "arrangement")},
            )
            runs.append(run)
        except (json.JSONDecodeError, KeyError):
            continue

    runs.sort(key=lambda r: r.timestamp)
    return runs


def record_build_run(
    output_dir: str,
    arrangement: Optional[str] = None,
    meta: Optional[dict] = None,
) -> BuildRun:
    """Record a build run by writing a run_meta.json manifest."""
    if not os.path.exists(output_dir):
        raise FileNotFoundError(f"Output directory not found: {output_dir}")

    now = datetime.now(timezone.utc)
    run_id = now.isoformat().replace(":", "-")
    timestamp = now.isoformat()

    data: dict = {
        "run_id": run_id,
        "timestamp": timestamp,
        "arrangement": arrangement,
    }
    if meta:
        data.update(meta)

    meta_path = os.path.join(output_dir, "run_meta.json")
    with open(meta_path, "w") as f:
        json.dump(data, f, indent=2)

    return BuildRun(
        run_id=run_id,
        path=output_dir,
        timestamp=timestamp,
        arrangement=arrangement,
        meta=meta or {},
    )


def run_diff(
    left_dir: str,
    right_dir: str,
    report_path: str,
    label_left: str = "left",
    label_right: str = "right",
) -> DiffSummary:
    """Main entry point for a single diff operation."""
    summary = compare_directories(left_dir, right_dir, label_left, label_right)

    # Print summary table
    ui.print_header("Build Diff", subtitle=f"{label_left} vs {label_right}")
    table = ui.create_table(["File", "Status"], title="Comparison Results")

    for result in summary.results:
        status_color = {
            "PASS": "[green]PASS[/green]",
            "FAIL": "[red]FAIL[/red]",
            "MISSING_LEFT": "[yellow]MISSING_LEFT[/yellow]",
            "MISSING_RIGHT": "[yellow]MISSING_RIGHT[/yellow]",
        }.get(result.status, result.status)
        table.add_row(result.path, status_color)

    ui.console.print(table)

    # Print diffs for failed files
    for result in summary.results:
        if result.status == "FAIL" and result.diff:
            ui.print_error(f"DIFF: {result.path}")
            ui.console.print(result.diff)

    # Overall verdict
    if summary.failed == 0 and summary.missing_left == 0 and summary.missing_right == 0:
        ui.print_success("SUCCESS: All files match semantically")
    else:
        ui.print_error(
            f"FAILURE: {summary.failed} failed, "
            f"{summary.missing_left} missing left, "
            f"{summary.missing_right} missing right"
        )

    # Save report
    report_dir = os.path.dirname(report_path)
    if report_dir:
        os.makedirs(report_dir, exist_ok=True)

    report_data = {
        "passed": summary.passed,
        "failed": summary.failed,
        "missing_left": summary.missing_left,
        "missing_right": summary.missing_right,
        "label_left": summary.label_left,
        "label_right": summary.label_right,
        "results": [
            {"path": r.path, "status": r.status, "diff": r.diff}
            for r in summary.results
        ],
    }
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)

    return summary
