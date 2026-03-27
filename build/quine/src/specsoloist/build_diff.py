"""Build diff module for comparing build outputs produced from specs."""

import json
import os
import ast
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from difflib import unified_diff

from specsoloist import ui


@dataclass
class DiffResult:
    """Result of a comparison for a single file path."""
    path: str
    status: str  # One of: PASS, FAIL, MISSING_LEFT, MISSING_RIGHT
    diff: Optional[str] = None


@dataclass
class DiffSummary:
    """Overall summary of a directory comparison."""
    passed: int
    failed: int
    missing_left: int
    missing_right: int
    results: List[DiffResult]
    label_left: str = "left"
    label_right: str = "right"


@dataclass
class BuildRun:
    """Metadata describing a single recorded build run."""
    run_id: str
    path: str
    timestamp: str
    arrangement: Optional[str] = None
    meta: Dict[str, Any] = None

    def __post_init__(self):
        if self.meta is None:
            self.meta = {}


def normalize_source(content: bytes, filename: str) -> bytes:
    """Reduce source code to canonical semantic form for comparison."""
    # Try to decode as text; if it fails, treat as binary
    try:
        text_content = content.decode('utf-8')
    except (UnicodeDecodeError, AttributeError):
        # Binary file or content is already bytes
        return content

    # Handle Python files with AST normalization
    if filename.endswith('.py'):
        try:
            # Parse and unparse to normalize
            tree = ast.parse(text_content)
            # Remove docstrings before unparsing
            tree = _remove_docstrings(tree)
            normalized = ast.unparse(tree)
            return normalized.encode('utf-8')
        except SyntaxError:
            # Fall back to comment stripping
            text_content = _strip_python_comments(text_content)

    # Handle TypeScript/JavaScript files
    elif filename.endswith(('.ts', '.tsx', '.js', '.mjs')):
        text_content = _strip_js_comments(text_content)

    # For all text files: normalize line endings and strip trailing whitespace
    lines = text_content.split('\n')
    normalized_lines = [line.rstrip() for line in lines]
    normalized = '\n'.join(normalized_lines)

    return normalized.encode('utf-8')


def _remove_docstrings(tree: ast.AST) -> ast.AST:
    """Remove docstrings from an AST tree."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Check if first statement is a docstring (Expr node containing a Constant)
            if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                # Remove the docstring
                node.body = node.body[1:]
    return tree


def _strip_python_comments(text: str) -> str:
    """Strip # comments from Python source (fallback when AST parsing fails)."""
    lines = text.split('\n')
    result = []
    for line in lines:
        # Remove inline comments
        if '#' in line:
            # Be careful with strings
            in_string = False
            string_char = None
            for i, char in enumerate(line):
                if char in ('"', "'") and (i == 0 or line[i - 1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                if char == '#' and not in_string:
                    line = line[:i].rstrip()
                    break
        result.append(line)

    # Strip trailing whitespace and normalize multiple blank lines
    result = [line.rstrip() for line in result]

    return '\n'.join(result)


def _strip_js_comments(text: str) -> str:
    """Strip // and /* */ comments from JavaScript/TypeScript source."""
    result = []
    i = 0
    while i < len(text):
        # Check for // comment
        if i < len(text) - 1 and text[i:i+2] == '//':
            # Skip to end of line
            while i < len(text) and text[i] != '\n':
                i += 1
            if i < len(text):
                result.append('\n')
                i += 1
            continue

        # Check for /* */ comment
        if i < len(text) - 1 and text[i:i+2] == '/*':
            # Skip to end of comment
            i += 2
            while i < len(text) - 1:
                if text[i:i+2] == '*/':
                    i += 2
                    break
                if text[i] == '\n':
                    result.append('\n')
                i += 1
            continue

        # Regular character
        result.append(text[i])
        i += 1

    text = ''.join(result)

    # Normalize whitespace and line endings
    lines = text.split('\n')
    lines = [line.rstrip() for line in lines]
    return '\n'.join(lines)


def compare_files(left_path: str, right_path: str, relative_path: str) -> DiffResult:
    """Compare two files at arbitrary absolute paths."""
    left_exists = os.path.exists(left_path)
    right_exists = os.path.exists(right_path)

    if not left_exists:
        return DiffResult(path=relative_path, status="MISSING_LEFT")

    if not right_exists:
        return DiffResult(path=relative_path, status="MISSING_RIGHT")

    # Both exist; compare normalized content
    with open(left_path, 'rb') as f:
        left_content = f.read()
    with open(right_path, 'rb') as f:
        right_content = f.read()

    left_normalized = normalize_source(left_content, left_path)
    right_normalized = normalize_source(right_content, right_path)

    if left_normalized == right_normalized:
        return DiffResult(path=relative_path, status="PASS")

    # Generate unified diff of original (un-normalized) contents
    try:
        left_text = left_content.decode('utf-8')
    except UnicodeDecodeError:
        left_text = "<binary file>"

    try:
        right_text = right_content.decode('utf-8')
    except UnicodeDecodeError:
        right_text = "<binary file>"

    left_lines = left_text.split('\n') if left_text != "<binary file>" else [left_text]
    right_lines = right_text.split('\n') if right_text != "<binary file>" else [right_text]

    diff_lines = list(unified_diff(
        left_lines,
        right_lines,
        fromfile=f"{relative_path} (left)",
        tofile=f"{relative_path} (right)",
        lineterm=''
    ))

    diff_text = '\n'.join(diff_lines)

    return DiffResult(path=relative_path, status="FAIL", diff=diff_text)


def compare_directories(left_dir: str, right_dir: str,
                       label_left: str = "left",
                       label_right: str = "right") -> DiffSummary:
    """Recursively walk both directories and compare all files."""
    ignored_patterns = {
        '__pycache__',
        '.git',
        'node_modules',
        '.DS_Store',
        'run_meta.json',
    }

    def should_ignore(path: str) -> bool:
        """Check if path matches ignored patterns."""
        path_parts = Path(path).parts
        if any(part in ignored_patterns for part in path_parts):
            return True
        if path.endswith('.pyc') or path.endswith('.spec.md'):
            return True
        return False

    # Collect all files from both directories
    files = {}

    if os.path.exists(left_dir):
        for root, dirs, filenames in os.walk(left_dir):
            # Remove ignored directories from dirs in-place (affects os.walk iteration)
            dirs[:] = [d for d in dirs if d not in ignored_patterns]

            for filename in filenames:
                full_path = os.path.join(root, filename)
                if should_ignore(full_path):
                    continue
                rel_path = os.path.relpath(full_path, left_dir)
                if rel_path not in files:
                    files[rel_path] = {}
                files[rel_path]['left'] = full_path

    if os.path.exists(right_dir):
        for root, dirs, filenames in os.walk(right_dir):
            dirs[:] = [d for d in dirs if d not in ignored_patterns]

            for filename in filenames:
                full_path = os.path.join(root, filename)
                if should_ignore(full_path):
                    continue
                rel_path = os.path.relpath(full_path, right_dir)
                if rel_path not in files:
                    files[rel_path] = {}
                files[rel_path]['right'] = full_path

    # Compare all files
    results = []
    for rel_path in sorted(files.keys()):
        left_path = files[rel_path].get('left')
        right_path = files[rel_path].get('right')

        # Use default paths if one directory exists but file not found
        if left_path is None:
            left_path = os.path.join(left_dir, rel_path)
        if right_path is None:
            right_path = os.path.join(right_dir, rel_path)

        result = compare_files(left_path, right_path, rel_path)
        results.append(result)

    # Count results
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    missing_left = sum(1 for r in results if r.status == "MISSING_LEFT")
    missing_right = sum(1 for r in results if r.status == "MISSING_RIGHT")

    return DiffSummary(
        passed=passed,
        failed=failed,
        missing_left=missing_left,
        missing_right=missing_right,
        results=results,
        label_left=label_left,
        label_right=label_right,
    )


def list_build_runs(build_dir: str) -> List[BuildRun]:
    """Discover and return all recorded build runs under build_dir."""
    if not os.path.exists(build_dir):
        return []

    runs = []
    for entry in os.listdir(build_dir):
        entry_path = os.path.join(build_dir, entry)
        if not os.path.isdir(entry_path):
            continue

        run_meta_path = os.path.join(entry_path, 'run_meta.json')
        if not os.path.exists(run_meta_path):
            continue

        try:
            with open(run_meta_path, 'r') as f:
                data = json.load(f)

            run = BuildRun(
                run_id=data['run_id'],
                path=entry_path,
                timestamp=data['timestamp'],
                arrangement=data.get('arrangement'),
                meta={k: v for k, v in data.items()
                      if k not in ('run_id', 'timestamp', 'arrangement', 'path')}
            )
            runs.append(run)
        except (json.JSONDecodeError, KeyError):
            continue

    # Sort by timestamp, oldest first
    runs.sort(key=lambda r: r.timestamp)
    return runs


def record_build_run(output_dir: str, arrangement: Optional[str] = None,
                    meta: Optional[Dict[str, Any]] = None) -> BuildRun:
    """Record a build run by writing run_meta.json inside output_dir."""
    if not os.path.exists(output_dir):
        raise FileNotFoundError(f"output_dir does not exist: {output_dir}")

    # Generate run_id from current UTC timestamp (ISO-8601, colons replaced with hyphens)
    now = datetime.utcnow()
    timestamp = now.isoformat() + 'Z'
    run_id = timestamp.replace(':', '-').replace('.', '-').rstrip('Z')

    if meta is None:
        meta = {}

    # Prepare manifest data
    manifest_data = {
        'run_id': run_id,
        'timestamp': timestamp,
        'arrangement': arrangement,
    }
    manifest_data.update(meta)

    # Write run_meta.json
    run_meta_path = os.path.join(output_dir, 'run_meta.json')
    with open(run_meta_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)

    return BuildRun(
        run_id=run_id,
        path=output_dir,
        timestamp=timestamp,
        arrangement=arrangement,
        meta=meta,
    )


def run_diff(left_dir: str, right_dir: str, report_path: str,
            label_left: str = "left", label_right: str = "right") -> DiffSummary:
    """Main entry point for a single diff operation."""
    # 1. Compare directories
    summary = compare_directories(left_dir, right_dir, label_left, label_right)

    # 2. Print summary table
    table = ui.create_table([label_left, "Status", label_right], title="Build Diff Results")

    for result in summary.results:
        status_style = {
            "PASS": "green",
            "FAIL": "red",
            "MISSING_LEFT": "yellow",
            "MISSING_RIGHT": "yellow",
        }.get(result.status, "white")

        status_text = f"[{status_style}]{result.status}[/{status_style}]"
        table.add_row(result.path, status_text, result.path)

    ui.console.print(table)

    # 3. Print diffs for FAIL results
    for result in summary.results:
        if result.status == "FAIL" and result.diff:
            ui.console.print(f"\n[bold red]{result.path}[/]")
            ui.console.print(result.diff)

    # 4. Print verdict
    if summary.failed == 0 and summary.missing_left == 0 and summary.missing_right == 0:
        ui.print_success("All files match - SUCCESS")
    else:
        ui.print_error(f"Differences found - FAILURE ({summary.failed} diffs, "
                      f"{summary.missing_left} missing in left, "
                      f"{summary.missing_right} missing in right)")

    # 5. Save JSON report
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    report_data = {
        'passed': summary.passed,
        'failed': summary.failed,
        'missing_left': summary.missing_left,
        'missing_right': summary.missing_right,
        'label_left': summary.label_left,
        'label_right': summary.label_right,
        'results': [
            {
                'path': r.path,
                'status': r.status,
                'diff': r.diff,
            }
            for r in summary.results
        ]
    }

    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)

    return summary
