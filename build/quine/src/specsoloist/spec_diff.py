"""Spec-vs-code drift detection for SpecSoloist.

Compares a spec's declared public symbols against compiled implementation
and test files, reporting three categories of issue:
- MISSING: symbol declared in spec but absent from code
- UNDOCUMENTED: public symbol in code but not declared in spec
- TEST_GAP: test scenario in spec with no matching test function
"""

import ast
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SpecDiffIssue:
    """A single drift issue found by spec_diff."""
    kind: str  # "MISSING", "UNDOCUMENTED", "TEST_GAP"
    symbol: str  # Symbol name or quoted scenario description
    detail: str  # Human-readable explanation


@dataclass
class SpecDiffResult:
    """Result of comparing a spec against its compiled code."""
    spec_name: str
    code_path: Optional[str] = None
    test_path: Optional[str] = None
    issues: List[SpecDiffIssue] = field(default_factory=list)

    @property
    def issue_count(self) -> int:
        """Return the total number of issues."""
        return len(self.issues)

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        return {
            "spec_name": self.spec_name,
            "code_path": self.code_path,
            "test_path": self.test_path,
            "issue_count": self.issue_count,
            "issues": [
                {
                    "kind": issue.kind,
                    "symbol": issue.symbol,
                    "detail": issue.detail,
                }
                for issue in self.issues
            ],
        }


def extract_spec_symbols(parsed_spec: Any) -> List[str]:
    """Extract the declared public symbol names from a parsed spec object.

    Args:
        parsed_spec: A ParsedSpec object from the parser module.

    Returns:
        A deduplicated list of symbol names.
    """
    symbols = []

    spec_type = parsed_spec.metadata.type

    if spec_type == "reference":
        # External libraries — nothing to diff
        return []

    if spec_type == "bundle":
        # Return keys from bundle_functions and bundle_types
        if parsed_spec.bundle_functions or parsed_spec.bundle_types:
            symbols.extend(parsed_spec.bundle_functions.keys())
            symbols.extend(parsed_spec.bundle_types.keys())
        else:
            # Fallback: scan ## headings in body
            symbols.extend(_scan_heading_symbols(parsed_spec.body))
    elif spec_type in ("function", "class"):
        # Return the spec name
        symbols.append(parsed_spec.metadata.name)
    else:
        # module, type, workflow, etc.: scan ## and ### headings
        symbols.extend(_scan_heading_symbols(parsed_spec.body))

    # Deduplicate
    return list(dict.fromkeys(symbols))


def _scan_heading_symbols(body: str) -> List[str]:
    """Scan ## and ### headings for function/class-like identifiers.

    Skips common prose section titles.
    """
    prose_titles = {
        "overview",
        "behavior",
        "examples",
        "test scenarios",
        "exports",
        "types",
        "functions",
        "steps",
        "error handling",
        "constraints",
        "frontmatter parsing",
        "yaml block extraction",
        "see also",
        "interface",
        "schema",
        "verification",
    }

    symbols = []
    for line in body.split("\n"):
        # Match ## or ### headings
        match = re.match(r"^#{2,3}\s+(.+)$", line)
        if not match:
            continue

        heading = match.group(1).strip()

        # Skip prose titles
        if heading.lower() in prose_titles:
            continue

        # Extract identifier: look for snake_case, UpperCamelCase, or function signature
        # Handle signatures like "function_name(params)"
        if "(" in heading:
            # Extract identifier before parentheses
            ident = heading.split("(")[0].strip()
        else:
            # Take the whole heading as identifier
            ident = heading.split()[0] if heading else ""

        # Validate identifier: must be valid Python identifier
        if ident and _is_valid_identifier(ident):
            symbols.append(ident)

    return symbols


def _is_valid_identifier(name: str) -> bool:
    """Check if a name is a valid Python identifier."""
    return name.isidentifier() and not name.startswith("_")


def extract_code_symbols(code_path: str) -> List[str]:
    """Return top-level function and class names from a Python source file.

    Also includes public method names from each class (no __ prefix, plus __init__).

    Uses AST module — the file is never imported or executed.

    Args:
        code_path: Path to the Python source file.

    Returns:
        A list of symbol names, or empty list if file doesn't exist or can't be parsed.
    """
    if not code_path or not os.path.exists(code_path):
        return []

    try:
        with open(code_path, "r") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, ValueError):
        return []

    symbols = []

    for node in ast.walk(tree):
        # Top-level functions and classes
        if isinstance(node, ast.Module):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(item.name)
                elif isinstance(item, ast.ClassDef):
                    symbols.append(item.name)
                    # Add public methods (no leading _)
                    for method in item.body:
                        if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            # Include __init__ but not other dunder or private methods
                            if method.name == "__init__" or (not method.name.startswith("_")):
                                symbols.append(method.name)

    return symbols


def extract_test_names(test_path: str) -> List[str]:
    """Return all function names starting with 'test_' from a Python test file.

    Walks the full AST (not just top-level) to find test functions inside classes.

    Uses AST module — the file is never imported or executed.

    Args:
        test_path: Path to the test file.

    Returns:
        A list of test function names, or empty list if file doesn't exist or can't be parsed.
    """
    if not test_path or not os.path.exists(test_path):
        return []

    try:
        with open(test_path, "r") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, ValueError):
        return []

    test_names = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                test_names.append(node.name)

    return test_names


def extract_test_scenarios(body: str) -> List[str]:
    """Extract scenario descriptions from a '## Test Scenarios' section.

    Returns one entry per list item (-, *, +) or ### sub-heading found.

    Args:
        body: The spec body text.

    Returns:
        A list of scenario descriptions.
    """
    # Find "## Test Scenarios" or "# Test Scenarios"
    pattern = r"^#+ Test Scenarios\s*$"
    match = re.search(pattern, body, re.MULTILINE | re.IGNORECASE)

    if not match:
        return []

    # Get text from heading to next top-level heading (not ###)
    start = match.end()
    remaining = body[start:]

    # Find next heading (## or # but not ###)
    next_heading = re.search(r"^#{1,2}[^#]", remaining, re.MULTILINE)
    if next_heading:
        section = remaining[: next_heading.start()]
    else:
        section = remaining

    scenarios = []

    # Extract list items (-, *, +) and ### headings
    for line in section.split("\n"):
        stripped = line.strip()
        if stripped and stripped[0] in "-*+":
            # Remove bullet marker and leading spaces
            scenario = re.sub(r"^[-*+]\s+", "", stripped).strip()
            if scenario:
                scenarios.append(scenario)
        elif stripped.startswith("###"):
            # Extract ### heading as scenario
            heading = re.sub(r"^#+\s+", "", stripped).strip()
            if heading:
                scenarios.append(heading)

    return scenarios


def diff_spec(
    spec_name: str,
    root_dir: str,
    arrangement: Optional[Any] = None,
    code_path: Optional[str] = None,
    test_path: Optional[str] = None,
) -> SpecDiffResult:
    """Compare a spec against its compiled implementation.

    Args:
        spec_name: The spec name (e.g., "parser", "manifest").
        root_dir: Project root directory used for path resolution.
        arrangement: Optional Arrangement object for path resolution.
        code_path: Explicit path to implementation file (overrides auto-detection).
        test_path: Explicit path to test file (overrides auto-detection).

    Returns:
        A SpecDiffResult with detected issues.
    """
    result = SpecDiffResult(spec_name=spec_name)

    # Resolve spec file path
    spec_path = _resolve_spec_path(spec_name, root_dir)
    if not spec_path:
        # Spec file not found
        result.issues.append(
            SpecDiffIssue(
                kind="MISSING",
                symbol=spec_name,
                detail=f"Spec file not found for '{spec_name}'",
            )
        )
        return result

    # Parse the spec
    try:
        from .parser import SpecParser, ParsedSpec

        parser = SpecParser(os.path.dirname(spec_path))
        parsed_spec = parser.parse_spec(os.path.basename(spec_path))
    except Exception:
        # If spec can't be parsed, return early
        result.issues.append(
            SpecDiffIssue(
                kind="MISSING",
                symbol=spec_name,
                detail=f"Could not parse spec file for '{spec_name}'",
            )
        )
        return result

    # Skip reference specs
    if parsed_spec.metadata.type == "reference":
        return result

    # Resolve code and test paths
    if not code_path:
        code_path = _resolve_code_path(spec_name, root_dir, arrangement)
    if code_path:
        result.code_path = code_path

    if not test_path:
        test_path = _resolve_test_path(spec_name, root_dir, arrangement)
    if test_path:
        result.test_path = test_path

    # Extract symbols
    spec_symbols = extract_spec_symbols(parsed_spec)
    code_symbols = extract_code_symbols(code_path) if code_path else []
    test_names = extract_test_names(test_path) if test_path else []
    test_scenarios = extract_test_scenarios(parsed_spec.body)

    # Detect MISSING: in spec but not in code
    spec_set = set(spec_symbols)
    code_set = set(code_symbols)
    for sym in spec_set - code_set:
        result.issues.append(
            SpecDiffIssue(
                kind="MISSING",
                symbol=sym,
                detail=f"Symbol '{sym}' declared in spec but not found in implementation",
            )
        )

    # Detect UNDOCUMENTED: in code but not in spec (and not private)
    for sym in code_set - spec_set:
        if not sym.startswith("_"):
            result.issues.append(
                SpecDiffIssue(
                    kind="UNDOCUMENTED",
                    symbol=sym,
                    detail=f"Symbol '{sym}' present in implementation but not declared in spec",
                )
            )

    # Detect TEST_GAP: scenario in spec with no matching test
    test_set = set(test_names)
    for scenario in test_scenarios:
        if not _scenario_matches_test(scenario, test_set):
            result.issues.append(
                SpecDiffIssue(
                    kind="TEST_GAP",
                    symbol=f'"{scenario}"',
                    detail=f"Test scenario '{scenario}' not covered by any test function",
                )
            )

    return result


def _resolve_spec_path(spec_name: str, root_dir: str) -> Optional[str]:
    """Resolve the spec file path for a given spec name."""
    candidates = [
        os.path.join(root_dir, "score", f"{spec_name}.spec.md"),
        os.path.join(root_dir, "src", f"{spec_name}.spec.md"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _resolve_code_path(
    spec_name: str, root_dir: str, arrangement: Optional[Any] = None
) -> Optional[str]:
    """Resolve implementation file path with fallback strategy."""
    # Try arrangement first
    if arrangement and hasattr(arrangement, "output_paths"):
        try:
            path = arrangement.output_paths.resolve_implementation(spec_name)
            if os.path.exists(path):
                return path
        except Exception:
            pass

    # Fallback search order
    candidates = [
        os.path.join(root_dir, "src", "specsoloist", f"{spec_name}.py"),
        os.path.join(root_dir, "src", "spechestra", f"{spec_name}.py"),
        os.path.join(root_dir, "build", f"{spec_name}.py"),
        os.path.join(root_dir, "src", f"{spec_name}.py"),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def _resolve_test_path(
    spec_name: str, root_dir: str, arrangement: Optional[Any] = None
) -> Optional[str]:
    """Resolve test file path with fallback strategy."""
    # Try arrangement first
    if arrangement and hasattr(arrangement, "output_paths"):
        try:
            path = arrangement.output_paths.resolve_tests(spec_name)
            if os.path.exists(path):
                return path
        except Exception:
            pass

    # Fallback search order
    candidates = [
        os.path.join(root_dir, "tests", f"test_{spec_name}.py"),
        os.path.join(root_dir, "build", "tests", f"test_{spec_name}.py"),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def _scenario_matches_test(scenario: str, test_names: set) -> bool:
    """Check if scenario matches any test function using fuzzy matching.

    A scenario matches if any significant word (≥4 chars, not a stop word)
    appears in any test function name.
    """
    stop_words = {"and", "the", "with", "from", "into", "test"}

    # Extract significant words from scenario
    words = re.findall(r"\b\w{4,}\b", scenario.lower())
    significant_words = [w for w in words if w not in stop_words]

    if not significant_words:
        return False

    # Check if any significant word appears in any test name
    for word in significant_words:
        for test_name in test_names:
            if word in test_name.lower():
                return True

    return False


def format_result_text(result: SpecDiffResult) -> str:
    """Format a SpecDiffResult as human-readable terminal output.

    If issue_count == 0, returns a clean message.
    Otherwise, returns multi-line output with one line per issue.
    """
    if result.issue_count == 0:
        return f"{result.spec_name} — no issues"

    lines = []
    for issue in result.issues:
        marker = _get_issue_marker(issue.kind)
        kind_display = issue.kind.replace("_", " ")
        lines.append(f"{marker} {kind_display}: {issue.symbol} — {issue.detail}")

    return "\n".join(lines)


def _get_issue_marker(kind: str) -> str:
    """Return the marker symbol for an issue kind."""
    markers = {
        "MISSING": "✗",
        "UNDOCUMENTED": "◆",
        "TEST_GAP": "◇",
    }
    return markers.get(kind, "•")


def format_result_json(result: SpecDiffResult) -> str:
    """Format a SpecDiffResult as a JSON string."""
    return json.dumps(result.to_dict(), indent=2)
