"""
build_diff: Compare build outputs produced from specs.

Supports semantic (not syntactic) comparison of generated source code directories,
producing both human-readable (colored) and machine-readable (JSON) reports.
"""

from __future__ import annotations

import ast
import dataclasses
import difflib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.table import Table
from rich.text import Text

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

IGNORED_PATTERNS = {
    "__pycache__",
    ".git",
    "node_modules",
    ".DS_Store",
    "run_meta.json",
}
IGNORED_SUFFIXES = {".pyc", ".spec.md"}


@dataclasses.dataclass
class DiffResult:
    """Result of a comparison for a single file path."""

    path: str
    status: str  # PASS | FAIL | MISSING_LEFT | MISSING_RIGHT
    diff: Optional[str] = None


@dataclasses.dataclass
class DiffSummary:
    """Overall summary of a directory comparison."""

    passed: int = 0
    failed: int = 0
    missing_left: int = 0
    missing_right: int = 0
    results: List[DiffResult] = dataclasses.field(default_factory=list)
    label_left: str = "left"
    label_right: str = "right"


@dataclasses.dataclass
class BuildRun:
    """Metadata describing a single recorded build run."""

    run_id: str
    path: str
    timestamp: str
    arrangement: Optional[str] = None
    meta: Dict = dataclasses.field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONSOLE = Console()


def _is_ignored(rel_path: str) -> bool:
    """Return True if the relative path matches any ignored pattern."""
    parts = Path(rel_path).parts
    for part in parts:
        if part in IGNORED_PATTERNS:
            return True
    name = Path(rel_path).name
    if name in IGNORED_PATTERNS:
        return True
    if name.endswith(".spec.md"):
        return True
    suffix = Path(rel_path).suffix
    if suffix in IGNORED_SUFFIXES:
        return True
    return False


def _is_binary(data: bytes) -> bool:
    """Heuristic: if a file contains a null byte it is treated as binary."""
    return b"\x00" in data


def _strip_js_comments(content: str) -> str:
    """Strip // line comments and /* */ block comments from JS/TS source."""
    # Remove block comments
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    # Remove line comments
    content = re.sub(r"//[^\n]*", "", content)
    return content


def _normalize_whitespace(content: str) -> str:
    """Normalize line endings, strip trailing whitespace, collapse blank lines."""
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [line.rstrip() for line in lines]
    # Collapse multiple consecutive blank lines to one
    result: List[str] = []
    prev_blank = False
    for line in lines:
        is_blank = line == ""
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank
    return "\n".join(result).strip()


# ---------------------------------------------------------------------------
# normalize_source
# ---------------------------------------------------------------------------


class _DocstringStripper(ast.NodeTransformer):
    """AST transformer that removes docstrings from functions, classes, and modules."""

    def _strip_docstring(self, node):
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            node.body = node.body[1:]
            # Ensure body is never empty after stripping
            if not node.body:
                node.body = [ast.Pass()]
        return self.generic_visit(node)

    def visit_Module(self, node):
        return self._strip_docstring(node)

    def visit_FunctionDef(self, node):
        return self._strip_docstring(node)

    def visit_AsyncFunctionDef(self, node):
        return self._strip_docstring(node)

    def visit_ClassDef(self, node):
        return self._strip_docstring(node)


def normalize_source(content: str, filename: str) -> str:
    """
    Reduce source code to a canonical semantic form.

    - .py: AST round-trip (strips comments and docstrings); falls back to comment
      stripping on SyntaxError.
    - .ts/.tsx/.js/.mjs: strip // and /* */ comments, normalize whitespace.
    - Other text: normalize line endings, strip trailing whitespace.
    - Binary content: returned unchanged (caller handles).
    """
    suffix = Path(filename).suffix.lower()

    if suffix == ".py":
        try:
            tree = ast.parse(content)
            tree = _DocstringStripper().visit(tree)
            ast.fix_missing_locations(tree)
            normalized = ast.unparse(tree)
            return normalized
        except SyntaxError:
            # Fall back: strip # comment lines, normalize whitespace
            lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
            stripped = [
                line for line in lines if not line.lstrip().startswith("#")
            ]
            return _normalize_whitespace("\n".join(stripped))

    if suffix in {".ts", ".tsx", ".js", ".mjs"}:
        content = _strip_js_comments(content)
        return _normalize_whitespace(content)

    # All other text files
    return _normalize_whitespace(content)


# ---------------------------------------------------------------------------
# compare_files
# ---------------------------------------------------------------------------


def compare_files(
    left_path: str, right_path: str, relative_path: str
) -> DiffResult:
    """
    Compare two files at arbitrary absolute paths.

    Returns DiffResult with status PASS, FAIL, MISSING_LEFT, or MISSING_RIGHT.
    FAIL includes a unified diff of the original (un-normalised) file contents.
    """
    lp = Path(left_path)
    rp = Path(right_path)

    if not lp.exists():
        return DiffResult(path=relative_path, status="MISSING_LEFT")
    if not rp.exists():
        return DiffResult(path=relative_path, status="MISSING_RIGHT")

    left_bytes = lp.read_bytes()
    right_bytes = rp.read_bytes()

    # Binary comparison
    if _is_binary(left_bytes) or _is_binary(right_bytes):
        if left_bytes == right_bytes:
            return DiffResult(path=relative_path, status="PASS")
        # Produce a minimal diff note for binary files
        diff_text = f"Binary files differ: {relative_path}"
        return DiffResult(path=relative_path, status="FAIL", diff=diff_text)

    left_text = left_bytes.decode("utf-8", errors="replace")
    right_text = right_bytes.decode("utf-8", errors="replace")

    left_norm = normalize_source(left_text, relative_path)
    right_norm = normalize_source(right_text, relative_path)

    if left_norm == right_norm:
        return DiffResult(path=relative_path, status="PASS")

    # Produce unified diff of original content
    left_lines = left_text.splitlines(keepends=True)
    right_lines = right_text.splitlines(keepends=True)
    diff_lines = list(
        difflib.unified_diff(
            left_lines,
            right_lines,
            fromfile=f"left/{relative_path}",
            tofile=f"right/{relative_path}",
        )
    )
    diff_text = "".join(diff_lines)
    return DiffResult(path=relative_path, status="FAIL", diff=diff_text)


# ---------------------------------------------------------------------------
# compare_directories
# ---------------------------------------------------------------------------


def _collect_files(directory: Path) -> set:
    """Walk directory and collect all relative file paths, ignoring ignored patterns."""
    found: set = set()
    if not directory.exists():
        return found
    for root, dirs, files in os.walk(directory):
        # Prune ignored directories in-place
        dirs[:] = [
            d
            for d in dirs
            if d not in IGNORED_PATTERNS and not d.endswith(".pyc")
        ]
        for fname in files:
            abs_path = Path(root) / fname
            rel_path = abs_path.relative_to(directory).as_posix()
            if not _is_ignored(rel_path):
                found.add(rel_path)
    return found


def compare_directories(
    left_dir: str,
    right_dir: str,
    label_left: str = "left",
    label_right: str = "right",
) -> DiffSummary:
    """
    Recursively walk both directories, compare each file, and aggregate results.
    """
    ldir = Path(left_dir)
    rdir = Path(right_dir)

    left_files = _collect_files(ldir)
    right_files = _collect_files(rdir)
    all_files = sorted(left_files | right_files)

    summary = DiffSummary(label_left=label_left, label_right=label_right)

    for rel_path in all_files:
        result = compare_files(
            str(ldir / rel_path),
            str(rdir / rel_path),
            rel_path,
        )
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


# ---------------------------------------------------------------------------
# list_build_runs
# ---------------------------------------------------------------------------


def list_build_runs(build_dir: str) -> List[BuildRun]:
    """
    Discover and return all recorded build runs under build_dir.

    Looks for subdirectories containing a run_meta.json file.
    Returns runs sorted by timestamp, oldest first.
    """
    bd = Path(build_dir)
    if not bd.exists():
        return []

    runs: List[BuildRun] = []
    for subdir in bd.iterdir():
        if not subdir.is_dir():
            continue
        meta_file = subdir / "run_meta.json"
        if not meta_file.exists():
            continue
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        run_id = data.get("run_id")
        timestamp = data.get("timestamp")
        if not run_id or not timestamp:
            continue
        arrangement = data.get("arrangement")
        meta = {
            k: v
            for k, v in data.items()
            if k not in {"run_id", "timestamp", "arrangement"}
        }
        runs.append(
            BuildRun(
                run_id=run_id,
                path=str(subdir.resolve()),
                timestamp=timestamp,
                arrangement=arrangement,
                meta=meta,
            )
        )

    runs.sort(key=lambda r: r.timestamp)
    return runs


# ---------------------------------------------------------------------------
# record_build_run
# ---------------------------------------------------------------------------


def record_build_run(
    output_dir: str,
    arrangement: Optional[str] = None,
    meta: Optional[Dict] = None,
) -> BuildRun:
    """
    Record a build run by writing a run_meta.json manifest inside output_dir.

    Raises FileNotFoundError if output_dir does not exist.
    """
    od = Path(output_dir)
    if not od.exists():
        raise FileNotFoundError(f"output_dir does not exist: {output_dir}")

    timestamp = datetime.utcnow().isoformat()
    run_id = timestamp.replace(":", "-")

    manifest: Dict = {
        "run_id": run_id,
        "timestamp": timestamp,
        "arrangement": arrangement,
    }
    if meta:
        manifest.update(meta)

    meta_file = od / "run_meta.json"
    meta_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return BuildRun(
        run_id=run_id,
        path=str(od.resolve()),
        timestamp=timestamp,
        arrangement=arrangement,
        meta=meta or {},
    )


# ---------------------------------------------------------------------------
# run_diff
# ---------------------------------------------------------------------------

_STATUS_STYLE = {
    "PASS": "green",
    "FAIL": "red",
    "MISSING_LEFT": "yellow",
    "MISSING_RIGHT": "yellow",
}


def _summary_to_dict(summary: DiffSummary) -> dict:
    """Serialize DiffSummary to a plain dict for JSON output."""
    return {
        "passed": summary.passed,
        "failed": summary.failed,
        "missing_left": summary.missing_left,
        "missing_right": summary.missing_right,
        "label_left": summary.label_left,
        "label_right": summary.label_right,
        "results": [
            {
                "path": r.path,
                "status": r.status,
                "diff": r.diff,
            }
            for r in summary.results
        ],
    }


def run_diff(
    left_dir: str,
    right_dir: str,
    report_path: str,
    label_left: str = "left",
    label_right: str = "right",
) -> DiffSummary:
    """
    Main entry point for a single diff operation.

    1. Compares directories.
    2. Prints a summary table (colored by status).
    3. Prints diffs for FAIL results.
    4. Prints overall verdict.
    5. Saves JSON report to report_path.
    6. Returns the DiffSummary.
    """
    summary = compare_directories(left_dir, right_dir, label_left, label_right)

    # Build and print summary table
    table = Table(
        title=f"Build Diff: [{label_left}] vs [{label_right}]",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
    )
    table.add_column("File", style="", no_wrap=False)
    table.add_column("Status", justify="center")

    for result in summary.results:
        style = _STATUS_STYLE.get(result.status, "")
        table.add_row(
            result.path,
            Text(result.status, style=style),
        )

    _CONSOLE.print(table)

    # Print diffs for FAIL results
    for result in summary.results:
        if result.status == "FAIL" and result.diff:
            _CONSOLE.print(f"\n[bold red]FAIL:[/] {result.path}")
            _CONSOLE.print(result.diff)

    # Overall verdict
    if summary.failed == 0 and summary.missing_left == 0 and summary.missing_right == 0:
        _CONSOLE.print("\n[bold green]SUCCESS[/] - All files match semantically.")
    else:
        _CONSOLE.print(
            f"\n[bold red]FAILURE[/] - "
            f"{summary.failed} failed, "
            f"{summary.missing_left} missing left, "
            f"{summary.missing_right} missing right."
        )

    # Save JSON report
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(_summary_to_dict(summary), indent=2), encoding="utf-8"
    )

    return summary
