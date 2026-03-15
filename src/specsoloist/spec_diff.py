"""
Spec vs code drift detection for SpecSoloist.

Compares a spec's declared public symbols against the compiled implementation,
reporting missing symbols, undocumented symbols, and test gaps.
"""

import ast
import json
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SpecDiffIssue:
    """A single drift issue found by spec_diff."""
    kind: str  # "MISSING" | "UNDOCUMENTED" | "TEST_GAP"
    symbol: str
    detail: str


@dataclass
class SpecDiffResult:
    """Result of comparing a spec against its compiled code."""
    spec_name: str
    code_path: Optional[str]
    test_path: Optional[str]
    issues: List[SpecDiffIssue] = field(default_factory=list)

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    def to_dict(self) -> dict:
        return {
            "spec_name": self.spec_name,
            "code_path": self.code_path,
            "test_path": self.test_path,
            "issue_count": self.issue_count,
            "issues": [
                {"kind": i.kind, "symbol": i.symbol, "detail": i.detail}
                for i in self.issues
            ],
        }


# ---------------------------------------------------------------------------
# Symbol extraction from spec
# ---------------------------------------------------------------------------

def extract_spec_symbols(parsed_spec) -> List[str]:
    """
    Extract the declared public symbol names from a ParsedSpec.

    For bundle specs, returns keys from bundle_functions + bundle_types plus
    any ## HeadingName symbols found in the body.

    For function specs, returns [metadata.name].

    For all other specs (module, type, workflow, etc.), parses
    '## SymbolName' and '## SymbolName(...)' headings from the body.
    """
    spec_type = parsed_spec.metadata.type
    symbols: List[str] = []

    if spec_type == "bundle":
        # yaml:functions and yaml:types blocks give us explicit names
        symbols.extend(parsed_spec.bundle_functions.keys())
        symbols.extend(parsed_spec.bundle_types.keys())
        # Also scan for ## headings that look like function/class declarations
        # (some specs use prose ## headings instead of yaml blocks)
        if not symbols:
            symbols.extend(_extract_heading_symbols(parsed_spec.body))
    elif spec_type in ("function", "class"):
        # Single-function spec: the spec name is the symbol
        if parsed_spec.metadata.name:
            symbols.append(parsed_spec.metadata.name)
    elif spec_type == "reference":
        # Reference specs document external libraries — nothing to diff
        pass
    else:
        # module, type, workflow, orchestrator, etc.
        # Parse ## headings for public symbol names
        symbols.extend(_extract_heading_symbols(parsed_spec.body))

    return _deduplicate(symbols)


def _extract_heading_symbols(body: str) -> List[str]:
    """
    Extract symbol names from Markdown headings that look like code identifiers.

    Handles three heading depths:
    - `# Name` or `# Name(...)` — top-level class/type name
    - `## Name` or `## Name(...)` — function or class declared at level-2
    - `### Name(...)` — method-level declarations

    Skips headings that are clearly section titles (Overview, Behavior,
    Examples, Types, Functions, Test Scenarios, etc.).
    """
    _SKIP_WORDS = {
        "overview", "behavior", "examples", "types", "functions",
        "interface", "exports", "steps", "test scenarios", "notes",
        "error handling", "validation", "schema", "api", "verification",
        "background", "motivation", "design", "usage", "configuration",
        "constraints", "requirements", "semantics", "philosophy",
        "incremental rebuild logic", "report format", "ignored patterns",
        "semantic comparison philosophy", "constructor", "methods",
        "frontmatter", "template", "creation", "extraction",
        "behavior", "errors", "returns", "parameters", "arguments",
        "fields", "properties", "attributes", "example", "examples",
        "installation", "quickstart", "setup", "summary", "details",
        "description", "definition", "definitions", "operations",
        "commands", "format", "patterns", "rules", "contract",
        "invariants", "pre", "post",
    }
    symbols: List[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        # Match # Name, ## Name, ### Name
        m = re.match(r'^(#{1,3})\s+(.+)$', stripped)
        if not m:
            continue
        depth = len(m.group(1))
        heading = m.group(2).strip()

        # Extract the identifier part: first token before ( or whitespace
        name = re.split(r'[\s(]', heading)[0]

        # Skip common section titles by checking the full heading and the name
        heading_lower = heading.lower().rstrip(".")
        name_lower = name.lower()
        if name_lower in _SKIP_WORDS or heading_lower in _SKIP_WORDS:
            continue
        # Skip multi-word section headings that aren't identifiers
        if " " in heading and "(" not in heading:
            continue

        # Resolve dotted names (Class.method → method)
        if "." in name:
            name = name.split(".")[-1]

        # Must look like a valid Python identifier
        if not (name and re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name)):
            continue

        # At depth 1, only pick up UpperCamelCase names (class/type names)
        if depth == 1:
            if re.match(r'^[A-Z][A-Za-z0-9]*$', name):
                symbols.append(name)
        else:
            # Depths 2 and 3: pick up snake_case function names and
            # UpperCamelCase class names, but NOT single-word prose titles
            # that could be section headers.
            #
            # Heuristic: a heading at depth 2/3 is a symbol if it either
            # contains a '(' (signature) or is snake_case / UpperCamelCase.
            is_signature = "(" in heading
            is_snake = "_" in name
            is_camel = bool(re.match(r'^[A-Z][A-Za-z0-9]+$', name))
            if is_signature or is_snake or is_camel:
                symbols.append(name)
    return symbols


def _deduplicate(seq: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Symbol extraction from Python source (via AST)
# ---------------------------------------------------------------------------

def extract_code_symbols(code_path: str) -> List[str]:
    """
    Return a list of top-level function/class names AND public class method names
    defined in a Python source file.  Uses the AST module — the file is never
    imported/executed.

    Returns an empty list if the file does not exist or cannot be parsed.
    """
    if not os.path.exists(code_path):
        return []
    try:
        with open(code_path, "r", encoding="utf-8") as fh:
            source = fh.read()
        tree = ast.parse(source, filename=code_path)
    except (OSError, SyntaxError):
        return []

    symbols: List[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(node.name)
        elif isinstance(node, ast.ClassDef):
            symbols.append(node.name)
            # Also include public method names from the class body
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not child.name.startswith("__") or child.name in ("__init__",):
                        symbols.append(child.name)
    return symbols


# ---------------------------------------------------------------------------
# Test gap detection
# ---------------------------------------------------------------------------

def extract_test_names(test_path: str) -> List[str]:
    """
    Return all function names beginning with 'test_' from a Python test file.
    Returns an empty list if the file does not exist or cannot be parsed.
    """
    if not test_path or not os.path.exists(test_path):
        return []
    try:
        with open(test_path, "r", encoding="utf-8") as fh:
            source = fh.read()
        tree = ast.parse(source, filename=test_path)
    except (OSError, SyntaxError):
        return []

    names: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                names.append(node.name)
    return names


def extract_test_scenarios(body: str) -> List[str]:
    """
    Extract scenario descriptions from a '## Test Scenarios' section in the
    spec body.  Returns the first sentence / heading text for each list item
    or sub-heading.
    """
    if "## Test Scenarios" not in body and "# Test Scenarios" not in body:
        return []

    # Grab text between the Test Scenarios heading and the next top-level heading
    pattern = r"#{1,3}\s+Test Scenarios\s*\n(.*?)(?=\n#{1,3}\s|\Z)"
    match = re.search(pattern, body, re.DOTALL)
    if not match:
        return []

    section = match.group(1)
    scenarios: List[str] = []
    for line in section.splitlines():
        line = line.strip()
        # List item: "- description" or "* description"
        if line.startswith(("- ", "* ", "+ ")):
            desc = line[2:].strip()
            if desc:
                scenarios.append(desc)
        # Sub-heading: "### scenario title"
        elif line.startswith("###"):
            desc = line.lstrip("#").strip()
            if desc:
                scenarios.append(desc)
    return scenarios


def _scenario_has_test(scenario: str, test_names: List[str]) -> bool:
    """
    Returns True if at least one test name contains any significant word
    from the scenario description.  A word is 'significant' if it is at
    least 4 characters long and not a stop word.
    """
    _STOP = {
        "when", "with", "that", "this", "from", "into", "have", "been",
        "should", "must", "does", "will", "the", "and", "for", "not",
        "given", "then", "returns", "raises", "return", "raise",
    }
    words = [
        w.lower() for w in re.split(r'\W+', scenario)
        if len(w) >= 4 and w.lower() not in _STOP
    ]
    if not words:
        return True  # Too short to check; don't flag

    combined = " ".join(test_names).lower()
    return any(w in combined for w in words)


# ---------------------------------------------------------------------------
# Path resolution helpers
# ---------------------------------------------------------------------------

def _find_code_file(spec_name: str, root_dir: str, arrangement=None) -> Optional[str]:
    """
    Locate the compiled implementation file for a spec.

    Search order:
    1. arrangement.output_paths.resolve_implementation(spec_name) if arrangement provided
    2. src/specsoloist/<spec_name>.py (framework source — the quine target)
    3. build/<spec_name>.py (default build output)
    4. src/<spec_name>.py
    """
    candidates: List[str] = []

    if arrangement is not None:
        try:
            rel = arrangement.output_paths.resolve_implementation(spec_name)
            # resolve_implementation may return a relative path
            if not os.path.isabs(rel):
                candidates.append(os.path.join(root_dir, rel))
            else:
                candidates.append(rel)
        except Exception:
            pass

    # Framework self-hosting: score specs map to src/specsoloist/<name>.py
    candidates.append(os.path.join(root_dir, "src", "specsoloist", f"{spec_name}.py"))
    # Also try spechestra for conductor/composer
    candidates.append(os.path.join(root_dir, "src", "spechestra", f"{spec_name}.py"))
    # Default build output
    candidates.append(os.path.join(root_dir, "build", f"{spec_name}.py"))
    candidates.append(os.path.join(root_dir, "src", f"{spec_name}.py"))

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _find_test_file(spec_name: str, root_dir: str, arrangement=None) -> Optional[str]:
    """
    Locate the test file for a spec.

    Search order:
    1. arrangement.output_paths.resolve_tests(spec_name) if arrangement provided
    2. tests/test_<spec_name>.py (standard pytest layout)
    3. build/tests/test_<spec_name>.py
    """
    candidates: List[str] = []

    if arrangement is not None:
        try:
            rel = arrangement.output_paths.resolve_tests(spec_name)
            if not os.path.isabs(rel):
                candidates.append(os.path.join(root_dir, rel))
            else:
                candidates.append(rel)
        except Exception:
            pass

    candidates.append(os.path.join(root_dir, "tests", f"test_{spec_name}.py"))
    candidates.append(os.path.join(root_dir, "build", "tests", f"test_{spec_name}.py"))

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def diff_spec(
    spec_name: str,
    root_dir: str,
    arrangement=None,
    code_path: Optional[str] = None,
    test_path: Optional[str] = None,
) -> SpecDiffResult:
    """
    Compare a spec against its compiled implementation.

    Args:
        spec_name: The spec name (e.g. 'parser', 'manifest').
        root_dir: Project root directory (used for path resolution).
        arrangement: Optional Arrangement object for path resolution.
        code_path: Explicit path to implementation file (overrides auto-detect).
        test_path: Explicit path to test file (overrides auto-detect).

    Returns:
        A SpecDiffResult with any detected issues.
    """
    from .parser import SpecParser

    # Resolve spec file
    spec_dir = os.path.join(root_dir, "score")
    if not os.path.isdir(spec_dir):
        spec_dir = os.path.join(root_dir, "src")

    parser = SpecParser(spec_dir)
    try:
        parsed = parser.parse_spec(spec_name)
    except FileNotFoundError:
        # Try the project's default src dir
        src_dir = os.path.join(root_dir, "src")
        parser2 = SpecParser(src_dir)
        try:
            parsed = parser2.parse_spec(spec_name)
        except FileNotFoundError:
            return SpecDiffResult(
                spec_name=spec_name,
                code_path=None,
                test_path=None,
                issues=[SpecDiffIssue(
                    kind="MISSING",
                    symbol=spec_name,
                    detail=f"Spec file not found in {spec_dir} or {src_dir}",
                )],
            )

    # Resolve code and test paths
    if code_path is None:
        code_path = _find_code_file(spec_name, root_dir, arrangement)
    if test_path is None:
        test_path = _find_test_file(spec_name, root_dir, arrangement)

    result = SpecDiffResult(
        spec_name=spec_name,
        code_path=code_path,
        test_path=test_path,
    )

    # Skip reference specs — they document external libraries
    if parsed.metadata.type == "reference":
        return result

    # Extract declared symbols from spec
    spec_symbols = extract_spec_symbols(parsed)

    # Extract actual symbols from code
    code_symbols = extract_code_symbols(code_path) if code_path else []
    code_symbol_set = set(code_symbols)

    # 1. MISSING: in spec but not in code
    for sym in spec_symbols:
        if sym not in code_symbol_set:
            loc = code_path or "<no code file found>"
            result.issues.append(SpecDiffIssue(
                kind="MISSING",
                symbol=sym,
                detail=f"in spec, not in {loc}",
            ))

    # 2. UNDOCUMENTED: in code but not in spec
    spec_symbol_set = set(spec_symbols)
    for sym in code_symbols:
        # Only flag public symbols (no leading underscore)
        if sym.startswith("_"):
            continue
        if sym not in spec_symbol_set:
            result.issues.append(SpecDiffIssue(
                kind="UNDOCUMENTED",
                symbol=sym,
                detail=f"in {code_path}, not in spec",
            ))

    # 3. TEST_GAP: scenario described in spec with no corresponding test
    scenarios = extract_test_scenarios(parsed.body)
    if scenarios:
        test_names = extract_test_names(test_path)
        for scenario in scenarios:
            if not _scenario_has_test(scenario, test_names):
                result.issues.append(SpecDiffIssue(
                    kind="TEST_GAP",
                    symbol=f'"{scenario}"',
                    detail="scenario described in spec, no matching test found",
                ))

    return result


def format_result_text(result: SpecDiffResult) -> str:
    """Format a SpecDiffResult as human-readable terminal output."""
    if result.issue_count == 0:
        return f"{result.spec_name} — no issues"

    lines = [f"{result.spec_name} — {result.issue_count} issue(s)"]
    for issue in result.issues:
        if issue.kind == "MISSING":
            marker = "  \u2717 MISSING       "
        elif issue.kind == "UNDOCUMENTED":
            marker = "  \u26a0 UNDOCUMENTED  "
        else:
            marker = "  \u26a0 TEST GAP      "
        lines.append(f"{marker}{issue.symbol}  ({issue.detail})")
    return "\n".join(lines)


def format_result_json(result: SpecDiffResult) -> str:
    """Format a SpecDiffResult as JSON."""
    return json.dumps(result.to_dict(), indent=2)
