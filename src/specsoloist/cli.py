"""Command-line interface for SpecSoloist.

Usage:
    sp init <name>              Scaffold a new project
    sp list                     List all specs
    sp create <name> <desc>     Create a new spec
    sp validate <name>          Validate a spec
    sp compile <name>           Compile a spec to code
    sp test <name>              Run tests for a spec
    sp fix <name>               Auto-fix failing tests
    sp build                    Compile all specs
    sp doctor                   Check environment health
    sp status                   Show compilation state of each spec
"""

import argparse
import importlib.metadata
import sys
import os

from .core import SpecSoloistCore
from .resolver import CircularDependencyError, MissingDependencyError
from spechestra.composer import SpecComposer, Architecture
from spechestra.conductor import SpecConductor
from .respec import Respecer
from . import ui


def main():
    """Entry point for the sp CLI."""
    parser = argparse.ArgumentParser(
        prog="sp",
        description="Spec-as-Source AI coding framework"
    )

    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"specsoloist {importlib.metadata.version('specsoloist')}"
    )

    # Global output-control flags (work on any command)
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress all non-error output (useful for CI and scripting)"
    )
    parser.add_argument(
        "--json", dest="json_output", action="store_true",
        help="Emit machine-readable JSON instead of Rich terminal output"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list
    list_parser = subparsers.add_parser("list", help="List all specification files")
    list_parser.add_argument("--arrangement", metavar="FILE",
                             help="Path to arrangement YAML (auto-discovers arrangement.yaml)")

    # create
    create_parser = subparsers.add_parser("create", help="Create a new spec from template")
    create_parser.add_argument("name", help="Spec name (e.g., 'auth' creates auth.spec.md)")
    create_parser.add_argument("description", help="Brief description of the component")
    create_parser.add_argument("--type", default="function", help="Type: function, class, module, typedef")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate a spec's structure")
    validate_parser.add_argument("name", help="Spec name to validate")
    validate_parser.add_argument("--arrangement", metavar="FILE", help="Path to arrangement YAML file")
    validate_parser.add_argument("--json", dest="json_output", action="store_true",
                                 help="Emit machine-readable JSON output")

    # verify
    subparsers.add_parser("verify", help="Verify all specs for orchestration readiness")

    # graph
    graph_parser = subparsers.add_parser("graph", help="Export dependency graph as Mermaid")
    graph_parser.add_argument("--arrangement", metavar="FILE",
                              help="Path to arrangement YAML (auto-discovers arrangement.yaml)")

    # compile
    compile_parser = subparsers.add_parser("compile", help="Compile a spec to code")
    compile_parser.add_argument("name", help="Spec name to compile")
    compile_parser.add_argument("--model", help="Override LLM model")
    compile_parser.add_argument("--no-tests", action="store_true", help="Skip test generation")
    compile_parser.add_argument("--arrangement", metavar="FILE", help="Path to arrangement YAML file")
    compile_parser.add_argument("--json", dest="json_output", action="store_true",
                                help="Emit machine-readable JSON output")

    # test
    test_parser = subparsers.add_parser("test", help="Run tests for a spec")
    test_parser.add_argument("name", nargs="?", help="Spec name to test (omit with --all)")
    test_parser.add_argument("--all", action="store_true", dest="test_all",
                             help="Run tests for every compiled spec")

    # fix
    fix_parser = subparsers.add_parser("fix", help="Auto-fix failing tests")
    fix_parser.add_argument("name", help="Spec name to fix")
    fix_parser.add_argument("--no-agent", action="store_true",
                                help="Use direct LLM API instead of agent CLI")
    fix_parser.add_argument("--auto-accept", action="store_true", help="Skip interactive review")
    fix_parser.add_argument("--model", help="Override LLM model")

    # build
    build_parser = subparsers.add_parser("build", help="Compile all specs in dependency order")
    build_parser.add_argument("--incremental", action="store_true", help="Only recompile changed specs")
    build_parser.add_argument("--parallel", action="store_true", help="Compile independent specs concurrently")
    build_parser.add_argument("--workers", type=int, default=4, help="Max parallel workers (default: 4)")
    build_parser.add_argument("--model", help="Override LLM model")
    build_parser.add_argument("--no-tests", action="store_true", help="Skip test generation")
    build_parser.add_argument("--arrangement", metavar="FILE", help="Path to arrangement YAML file")
    build_parser.add_argument("--log-file", metavar="PATH", help="Write NDJSON build events to file (use - for stdout)")
    build_parser.add_argument("--tui", action="store_true", help="Run build inside a live Textual dashboard")

    # compose
    compose_parser = subparsers.add_parser("compose", help="Draft architecture and specs from natural language")
    compose_parser.add_argument("request", help="Description of the system you want to build")
    compose_parser.add_argument("--no-agent", action="store_true",
                                help="Use direct LLM API instead of agent CLI")
    compose_parser.add_argument("--auto-accept", action="store_true", help="Skip interactive review (with --no-agent)")
    compose_parser.add_argument("--model", help="Override LLM model")

    # conduct
    conduct_parser = subparsers.add_parser("conduct", help="Orchestrate project build")
    conduct_parser.add_argument("src_dir", nargs="?", default=None, help="Spec directory (default: src/)")
    conduct_parser.add_argument("--no-agent", action="store_true",
                                help="Use direct LLM API instead of agent CLI")
    conduct_parser.add_argument("--auto-accept", action="store_true", help="Skip interactive review")
    conduct_parser.add_argument("--incremental", action="store_true", help="Only recompile changed specs")
    conduct_parser.add_argument("--parallel", action="store_true", help="Compile independent specs concurrently")
    conduct_parser.add_argument("--workers", type=int, default=4, help="Max parallel workers (default: 4)")
    conduct_parser.add_argument("--model", help="Override LLM model")
    conduct_parser.add_argument("--arrangement", metavar="FILE", help="Path to arrangement YAML file")
    conduct_parser.add_argument("--log-file", metavar="PATH", help="Write NDJSON build events to file (use - for stdout)")
    conduct_parser.add_argument("--tui", action="store_true", help="Run build inside a live Textual dashboard")
    resume_group = conduct_parser.add_mutually_exclusive_group()
    resume_group.add_argument(
        "--resume", action="store_true",
        help="Skip specs already compiled (hash + output files match manifest); recompile stale or missing"
    )
    resume_group.add_argument(
        "--force", action="store_true",
        help="Recompile all specs regardless of manifest state"
    )

    # vibe
    vibe_parser = subparsers.add_parser(
        "vibe",
        help="Single-command pipeline: compose specs from a brief, then build"
    )
    vibe_parser.add_argument(
        "brief", nargs="?", default=None,
        help="Brief as a .md file path or a plain string description"
    )
    vibe_parser.add_argument(
        "--template", metavar="NAME",
        help="Arrangement template to use for the project (e.g. python-fasthtml, nextjs-vitest)"
    )
    vibe_parser.add_argument(
        "--pause-for-review", action="store_true",
        help="Pause after composing specs so you can review and edit before building"
    )
    vibe_parser.add_argument(
        "--resume", action="store_true",
        help="Skip already-compiled specs (incremental build; treats brief as an addendum)"
    )
    vibe_parser.add_argument(
        "--no-agent", action="store_true",
        help="Use direct LLM API instead of agent CLI"
    )
    vibe_parser.add_argument(
        "--auto-accept", action="store_true",
        help="Skip interactive review in compose and conduct steps"
    )
    vibe_parser.add_argument("--model", help="Override LLM model for both compose and conduct")

    # diff
    diff_parser = subparsers.add_parser(
        "diff",
        help="Detect spec vs code drift, or compare two build directories"
    )
    diff_parser.add_argument(
        "left",
        help="Spec name (e.g. 'parser') for spec-drift mode, or left directory for build-diff mode"
    )
    diff_parser.add_argument(
        "right", nargs="?", default=None,
        help="Right directory for build-diff mode (omit to use spec-drift mode)"
    )
    diff_parser.add_argument(
        "--json", dest="json_output", action="store_true",
        help="Output machine-readable JSON (spec-drift mode)"
    )
    diff_parser.add_argument(
        "--label-left", default=None, metavar="LABEL",
        help="Human-readable label for the left directory (build-diff mode)"
    )
    diff_parser.add_argument(
        "--label-right", default=None, metavar="LABEL",
        help="Human-readable label for the right directory (build-diff mode)"
    )
    diff_parser.add_argument(
        "--report", default="build/diff-report.json", metavar="PATH",
        help="Path to write the JSON diff report (build-diff mode; default: build/diff-report.json)"
    )
    diff_parser.add_argument(
        "--runs", type=int, default=None, metavar="N",
        help="Compare the last N build runs recorded in build/runs/ (build-diff mode)"
    )

    # respec
    respec_parser = subparsers.add_parser("respec", help="Reverse engineer code to spec")
    respec_parser.add_argument("file", help="Path to source file")
    respec_parser.add_argument("--test", help="Path to test file (optional)")
    respec_parser.add_argument("--out", help="Output path (optional)")
    respec_parser.add_argument("--no-agent", action="store_true",
                               help="Use direct LLM API instead of agent CLI")
    respec_parser.add_argument("--model", help="LLM model override (with --no-agent)")
    respec_parser.add_argument("--auto-accept", action="store_true", help="Skip interactive review")

    # init
    init_parser = subparsers.add_parser("init", help="Scaffold a new SpecSoloist project")
    init_parser.add_argument("name", nargs="?", help="Project directory name to create")
    init_parser.add_argument(
        "--arrangement", choices=["python", "typescript"], default="python",
        help="Arrangement template to use (default: python)"
    )
    init_parser.add_argument(
        "--template",
        help="Named arrangement template (e.g. python-fasthtml, nextjs-vitest, nextjs-playwright)"
    )
    init_parser.add_argument(
        "--list-templates", action="store_true",
        help="List available arrangement templates"
    )

    # install-skills
    install_skills_parser = subparsers.add_parser(
        "install-skills",
        help="Install SpecSoloist agent skills to your project or global skills directory"
    )
    install_skills_parser.add_argument(
        "--target", default=".claude/skills",
        help="Target directory for skills (default: .claude/skills)"
    )

    # dashboard
    subparsers.add_parser(
        "dashboard",
        help="Connect to a running build's live dashboard (requires sp conduct --serve)"
    )

    # help
    help_parser = subparsers.add_parser(
        "help",
        help="Get help on a specific topic (arrangement, spec-format, conduct, ...)"
    )
    help_parser.add_argument(
        "topic", nargs="?", default=None,
        help="Topic to look up (arrangement, spec-format, conduct, overrides, specs-path)"
    )

    # schema
    schema_parser = subparsers.add_parser(
        "schema",
        help="Show annotated schema for arrangement.yaml"
    )
    schema_parser.add_argument(
        "topic", nargs="?", default=None,
        help="Field to zoom into (e.g. output_paths, environment)"
    )
    schema_parser.add_argument(
        "--json", dest="json_output", action="store_true",
        help="Emit JSON Schema instead of annotated text"
    )

    # doctor
    doctor_parser = subparsers.add_parser("doctor", help="Check environment health (API keys, CLIs, tools)")
    doctor_parser.add_argument("--arrangement", metavar="FILE", help="Path to arrangement YAML; checks declared env_vars")

    # status
    status_parser = subparsers.add_parser("status", help="Show compilation state of each spec")
    status_parser.add_argument("--json", dest="json_output", action="store_true",
                               help="Emit machine-readable JSON output")
    status_parser.add_argument("--arrangement", metavar="FILE",
                               help="Path to arrangement YAML (auto-discovers arrangement.yaml)")

    args = parser.parse_args()

    # Apply global output flags early so all subsequent ui calls respect them
    ui.configure(
        quiet=getattr(args, "quiet", False),
        json_mode=getattr(args, "json_output", False),
    )

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Commands that don't need a project context
    if args.command == "init":
        if args.list_templates:
            cmd_list_templates()
            return
        if args.name is None:
            init_parser.print_help()
            sys.exit(1)
        cmd_init(args.name, args.arrangement, args.template)
        return
    if args.command == "install-skills":
        cmd_install_skills(args.target)
        return
    if args.command == "dashboard":
        cmd_dashboard()
        return
    if args.command == "help":
        cmd_help(getattr(args, "topic", None))
        return
    if args.command == "schema":
        cmd_schema(getattr(args, "topic", None), json_output=getattr(args, "json_output", False))
        return
    if args.command == "doctor":
        cmd_doctor(arrangement_arg=getattr(args, "arrangement", None))
        return

    # Set up event bus + NDJSON subscriber if --log-file is specified
    event_bus = None
    log_file_handle = None
    log_file_arg = getattr(args, "log_file", None)
    if log_file_arg:
        from .events import EventBus
        from .subscribers.ndjson import NdjsonSubscriber
        event_bus = EventBus()
        if log_file_arg == "-":
            log_file_handle = sys.stdout
        else:
            log_file_handle = open(log_file_arg, "w")  # noqa: SIM115
        event_bus.subscribe(NdjsonSubscriber(log_file_handle))

    # Also emit NDJSON to stdout when --json is used with conduct/build
    if getattr(args, "json_output", False) and args.command in ("conduct", "build"):
        from .events import EventBus
        from .subscribers.ndjson import NdjsonSubscriber
        if event_bus is None:
            event_bus = EventBus()
        event_bus.subscribe(NdjsonSubscriber(sys.stdout))

    # Set up TUI subscriber if --tui is specified
    tui_subscriber = None
    use_tui = getattr(args, "tui", False)
    if use_tui and args.command in ("conduct", "build"):
        from .events import EventBus
        from .subscribers.tui import TuiSubscriber
        if event_bus is None:
            event_bus = EventBus()
        tui_subscriber = TuiSubscriber()
        event_bus.subscribe(tui_subscriber)

    # Initialize core
    try:
        core = SpecSoloistCore(os.getcwd(), event_bus=event_bus)
    except Exception as e:
        ui.print_error(f"Failed to initialize SpecSoloist: {e}")
        sys.exit(1)

    try:
        if args.command == "list":
            cmd_list(core, getattr(args, "arrangement", None))
        elif args.command == "create":
            cmd_create(core, args.name, args.description, args.type)
        elif args.command == "validate":
            cmd_validate(core, args.name, getattr(args, "arrangement", None),
                         json_output=getattr(args, "json_output", False))
        elif args.command == "verify":
            cmd_verify(core)
        elif args.command == "graph":
            cmd_graph(core, getattr(args, "arrangement", None))
        elif args.command == "compile":
            cmd_compile(core, args.name, args.model, not args.no_tests, args.arrangement,
                        json_output=getattr(args, "json_output", False))
        elif args.command == "test":
            if args.test_all:
                cmd_test_all(core)
            elif args.name:
                cmd_test(core, args.name)
            else:
                ui.print_error("Specify a spec name or use --all")
                sys.exit(1)
        elif args.command == "fix":
            cmd_fix(core, args.name, args.no_agent, args.auto_accept, args.model)
        elif args.command == "build":
            if use_tui:
                _preflight_tui(getattr(args, "arrangement", None))
                _run_with_tui(tui_subscriber, lambda: cmd_build(
                    core, args.incremental, args.parallel, args.workers,
                    args.model, not args.no_tests, args.arrangement),
                    event_bus=event_bus,
                    command_description="sp build")
            else:
                cmd_build(core, args.incremental, args.parallel, args.workers, args.model, not args.no_tests, args.arrangement)
        elif args.command == "compose":
            cmd_compose(core, args.request, args.no_agent, args.auto_accept, args.model)
        elif args.command == "vibe":
            cmd_vibe(core, args.brief, args.template, args.pause_for_review,
                     args.resume, args.no_agent, args.auto_accept, args.model)
        elif args.command == "conduct":
            if use_tui and args.no_agent:
                _preflight_tui(getattr(args, "arrangement", None))
                _cmd_desc = f"sp conduct {args.src_dir or ''} --no-agent".strip()
                _run_with_tui(tui_subscriber, lambda: cmd_conduct(
                    core, args.src_dir, args.no_agent, args.auto_accept,
                    args.incremental, args.parallel, args.workers, args.model,
                    args.arrangement, resume=args.resume, force=args.force),
                    event_bus=event_bus,
                    command_description=_cmd_desc)
            elif use_tui:
                ui.print_warning("--tui requires --no-agent for sp conduct (agent mode uses its own output)")
                sys.exit(1)
            else:
                cmd_conduct(core, args.src_dir, args.no_agent, args.auto_accept,
                            args.incremental, args.parallel, args.workers, args.model, args.arrangement,
                            resume=args.resume, force=args.force)
        elif args.command == "diff":
            if args.right is None and args.runs is None:
                # Spec-drift mode: single spec name argument
                cmd_spec_diff(core, args.left, args.json_output)
            else:
                cmd_diff(core, args.left, args.right, args.label_left, args.label_right,
                         args.report, args.runs)
        elif args.command == "respec":
            cmd_respec(core, args.file, args.test, args.out, args.no_agent, args.model, args.auto_accept)
        elif args.command == "status":
            cmd_status(core, getattr(args, "arrangement", None),
                       json_output=getattr(args, "json_output", False))
    except KeyboardInterrupt:
        ui.print_warning("\nOperation cancelled by user.")
        sys.exit(130)
    except CircularDependencyError as e:
        ui.print_error(str(e))
        sys.exit(1)
    except MissingDependencyError as e:
        ui.print_error(str(e))
        sys.exit(1)
    except Exception as e:
        ui.print_error(f"Unexpected error: {e}")
        # In verbose mode, we might want to print the stack trace
        sys.exit(1)
    finally:
        if event_bus is not None:
            event_bus.close()
        if log_file_handle is not None and log_file_handle is not sys.stdout:
            log_file_handle.close()


def cmd_list(core: SpecSoloistCore, arrangement_arg: str | None = None):
    """List all spec files found in the src directory."""
    arrangement = _resolve_arrangement(core, arrangement_arg)
    if arrangement:
        core.parser.src_dir = os.path.abspath(arrangement.specs_path)
    specs = core.list_specs()
    if not specs:
        path = arrangement.specs_path if arrangement else "src/"
        ui.print_warning(f"No specs found in {path}")
        ui.print_info("Create one with: sp create <name> '<description>'")
        return

    table = ui.create_table(["Name", "Type", "Status", "Description"], title="Project Specifications")

    for spec_file in specs:
        try:
            name = spec_file.replace(".spec.md", "")
            # Parse to get metadata
            parsed = core.parser.parse_spec(name)
            meta = parsed.metadata
            
            # Color code status
            status_style = "green" if meta.status == "stable" else "yellow"
            
            table.add_row(
                f"[bold]{name}[/]", 
                meta.type,
                f"[{status_style}]{meta.status}[/]",
                meta.description or ""
            )
        except Exception as e:
            # Fallback for unparseable specs
            table.add_row(spec_file, "???", "error", f"Error: {str(e)}")

    ui.console.print(table)


def cmd_create(core: SpecSoloistCore, name: str, description: str, spec_type: str):
    """Create a new spec file from the standard template."""
    ui.print_header("Creating Spec", name)
    try:
        path = core.create_spec(name, description, type=spec_type)
        ui.print_success(f"Created spec at: [bold]{path}[/]")
    except FileExistsError:
        ui.print_error(f"Spec already exists: {name}.spec.md")
        sys.exit(1)


def _check_arrangement_dependencies(arrangement) -> list[str]:
    """Return warnings for arrangement dependency configuration issues."""
    warnings = []
    if not arrangement:
        return warnings
    deps = arrangement.environment.dependencies
    if not deps:
        return warnings
    install_keywords = ("uv sync", "uv add", "pip install", "npm install", "npm ci", "yarn install", "pnpm install")
    commands = arrangement.environment.setup_commands
    has_install = any(
        any(kw in cmd for kw in install_keywords) for cmd in commands
    )
    if not has_install:
        warnings.append("dependencies declared but no install command found in setup_commands")
    return warnings


def _check_spec_quality(spec_content: str, spec_type: str) -> list[str]:
    """Return a list of quality warning strings for the given spec markdown."""
    warnings = []

    # No test scenarios section
    has_scenarios = (
        "## Test Scenarios" in spec_content
        or "```yaml:test_scenarios" in spec_content
    )
    if not has_scenarios:
        warnings.append(
            "No test scenarios found — soloists compile better with concrete examples.\n"
            "  Add a yaml:test_scenarios block, e.g.:\n"
            "  ```yaml:test_scenarios\n"
            "  - description: \"basic case\"\n"
            "    inputs: {param: \"value\"}\n"
            "    expected_output: \"result\"\n"
            "  ```"
        )

    # No schema block (only for bundle and function types)
    if spec_type in ("bundle", "function"):
        if "```yaml:schema" not in spec_content:
            warnings.append("No schema block — interface contract is underspecified")

    # Very short description — extract from metadata line "description:"
    import re
    desc_match = re.search(r'^description:\s*(.+)$', spec_content, re.MULTILINE)
    if desc_match:
        desc = desc_match.group(1).strip()
        if len(desc) < 10:
            warnings.append(f"Description is very short ({len(desc)} chars) — aim for at least 10 characters")
    else:
        warnings.append("Description is very short (0 chars) — aim for at least 10 characters")

    # Fewer than 2 rows in test scenarios table
    if "## Test Scenarios" in spec_content:
        # Find the section content after the heading
        section = spec_content.split("## Test Scenarios", 1)[1]
        # Count table rows (lines starting with | that aren't header or separator)
        table_rows = [
            line for line in section.splitlines()
            if line.strip().startswith("|")
            and not re.match(r'^\s*\|[-| ]+\|\s*$', line)
        ]
        # Subtract 1 for the header row
        data_rows = max(0, len(table_rows) - 1)
        if data_rows < 2:
            warnings.append(
                f"Only {data_rows} example(s) in test scenarios — at least 2 examples help soloists generalise"
            )

    return warnings


def cmd_validate(core: SpecSoloistCore, name: str, arrangement_arg: str | None = None,
                 json_output: bool = False):
    """Validate a spec's structure and frontmatter."""
    import json as _json

    arrangement = _resolve_arrangement(core, arrangement_arg)
    if arrangement:
        core.parser.src_dir = os.path.abspath(arrangement.specs_path)

    if not json_output:
        ui.print_header("Validating Spec", name)
    result = core.validate_spec(name)

    warnings: list[str] = []

    if result["valid"]:
        # Collect quality hints
        try:
            spec_content = core.read_spec(name)
            parsed = core.parser.parse_spec(name)
            spec_type = parsed.metadata.type
        except Exception:
            spec_content = ""
            spec_type = "bundle"
            parsed = None

        if spec_type == "reference":
            if not json_output:
                ui.print_info("type: reference — context only, no implementation will be generated")
            if parsed is not None:
                for w in core.parser.get_reference_warnings(parsed):
                    warnings.append(w)
                    if not json_output:
                        ui.console.print(f"[warning]⚠[/] {w}")
        else:
            for w in _check_spec_quality(spec_content, spec_type):
                warnings.append(w)
                if not json_output:
                    ui.console.print(f"[warning]⚠[/] {w}")

        if json_output:
            print(_json.dumps({
                "spec": name,
                "valid": True,
                "errors": [],
                "warnings": warnings,
            }))
        else:
            ui.print_success(f"{name} is VALID")
            # Warn about unset required env vars declared in arrangement
            _check_validate_env_vars(arrangement_arg, core)

    else:
        if json_output:
            print(_json.dumps({
                "spec": name,
                "valid": False,
                "errors": result["errors"],
                "warnings": [],
            }))
        else:
            ui.print_error(f"{name} is INVALID")
            for error in result["errors"]:
                ui.print_step(f"[red]{error}[/]")
        sys.exit(1)


def _check_validate_env_vars(arrangement_arg: str | None, core) -> None:
    """Warn if required env vars declared in the arrangement are unset."""
    arr_path = arrangement_arg
    if arr_path is None:
        # Auto-discover arrangement.yaml relative to cwd or core project dir
        for candidate in (
            os.path.join(os.getcwd(), "arrangement.yaml"),
            os.path.join(core.root_dir, "arrangement.yaml"),
        ):
            if os.path.exists(candidate):
                arr_path = candidate
                break

    if not arr_path or not os.path.exists(arr_path):
        return

    try:
        import yaml
        with open(arr_path) as f:
            arr_data = yaml.safe_load(f)
        from .schema import Arrangement
        arr = Arrangement(**arr_data)
        for var_name, var_info in arr.env_vars.items():
            if var_info.required and var_name not in os.environ:
                ui.console.print(
                    f"[warning]⚠[/] {var_name} is required by arrangement but not set "
                    f"— sp conduct may fail at runtime"
                )
    except Exception:
        # If arrangement can't be parsed, skip silently
        pass


def cmd_verify(core: SpecSoloistCore):
    """Verify all specs for orchestration readiness (dependency integrity, valid types)."""
    ui.print_header("Verifying Project", "Checking schemas")
    
    with ui.spinner("Verifying all specs..."):
        result = core.verify_project()
        
    table = ui.create_table(["Spec", "Status", "Schema", "Details"], title="Verification Results")
    
    for name, data in result["results"].items():
        status = data["status"]
        status_color = "green" if status == "valid" else "yellow" if status == "warning" else "red"
        
        schema_status = "[green]Yes[/]" if data.get("schema_defined") else "[dim]No[/]"
        details = data.get("message") or (", ".join(data.get("errors", [])) if "errors" in data else "")
        
        table.add_row(
            name,
            f"[{status_color}]{status.upper()}[/]",
            schema_status,
            details
        )
        
    ui.console.print(table)
    
    if result["success"]:
        ui.print_success("Project verification complete.")
    else:
        ui.print_warning("Some specs have issues or missing schemas.")
        # We don't exit(1) here because warnings shouldn't break the build pipeline necessarily,
        # unless strict mode is enabled (future feature).


def cmd_graph(core: SpecSoloistCore, arrangement_arg: str | None = None):
    """Print the spec dependency graph in Mermaid format."""
    arrangement = _resolve_arrangement(core, arrangement_arg)
    if arrangement:
        core.parser.src_dir = os.path.abspath(arrangement.specs_path)
    ui.print_header("Dependency Graph", "Mermaid format")

    graph = core.get_dependency_graph()
    
    lines = ["graph TD"]
    for spec in graph.specs:
        deps = graph.get_dependencies(spec)
        if not deps:
            lines.append(f"    {spec}")
        for dep in deps:
            lines.append(f"    {spec} --> {dep}")
            
    mermaid = "\n".join(lines)
    ui.console.print(ui.Panel(mermaid, title="Mermaid.js Output"))
    ui.print_info("Paste this into https://mermaid.live to visualize.")


def cmd_compile(core: SpecSoloistCore, name: str, model: str, generate_tests: bool,
                arrangement_arg: str | None = None, json_output: bool = False):
    """Compile a single spec to implementation code and tests."""
    import json as _json

    _check_api_key()

    if not json_output:
        ui.print_header("Compiling Spec", name)

    arrangement = _resolve_arrangement(core, arrangement_arg)
    _apply_arrangement(core, arrangement)
    model = _resolve_model(model, arrangement)

    # Validate first
    validation = core.validate_spec(name)
    if not validation["valid"]:
        if json_output:
            print(_json.dumps({
                "spec": name,
                "success": False,
                "tests_pass": False,
                "errors": validation["errors"],
            }))
        else:
            ui.print_error("Invalid spec")
            for error in validation["errors"]:
                ui.print_step(f"[red]{error}[/]")
        sys.exit(1)

    try:
        # Compile code
        with ui.spinner(f"Compiling [bold]{name}[/] implementation..."):
            result = core.compile_spec(name, model=model, arrangement=arrangement)
        if not json_output:
            ui.print_success(result)

        # Generate tests
        tests_compiled = False
        if generate_tests:
            spec = core.parser.parse_spec(name)
            if spec.metadata.type != "typedef":
                with ui.spinner(f"Generating tests for [bold]{name}[/]..."):
                    result = core.compile_tests(name, model=model, arrangement=arrangement)
                if not json_output:
                    ui.print_success(result)
                tests_compiled = True
            else:
                if not json_output:
                    ui.print_info("Skipping tests for typedef spec")

        if json_output:
            print(_json.dumps({
                "spec": name,
                "success": True,
                "tests_pass": tests_compiled,
                "errors": [],
            }))

    except Exception as e:
        if json_output:
            print(_json.dumps({
                "spec": name,
                "success": False,
                "tests_pass": False,
                "errors": [str(e)],
            }))
        else:
            ui.print_error(str(e))
        sys.exit(1)


def cmd_test(core: SpecSoloistCore, name: str):
    """Run the test suite for a compiled spec."""
    ui.print_header("Running Tests", name)

    arrangement = _resolve_arrangement(core, None)
    _apply_arrangement(core, arrangement)

    with ui.spinner(f"Running tests for [bold]{name}[/]..."):
        result = core.run_tests(name)
    
    if result["success"]:
        ui.print_success("Tests PASSED")
        # Only show output if verbose? For now, nice to see summary
        # ui.console.print(Panel(result["output"], title="Output", border_style="dim"))
    else:
        ui.print_error("Tests FAILED")
        ui.console.print(ui.Panel(result["output"], title="Failure Output", border_style="red"))
        sys.exit(1)


def cmd_test_all(core: SpecSoloistCore):
    """Run tests for every compiled spec and show a results table."""
    import time

    arrangement = _resolve_arrangement(core, None)
    _apply_arrangement(core, arrangement)

    specs = core.list_specs()
    manifest = core._get_manifest()

    if not specs:
        ui.print_warning("No specs found.")
        return

    ui.print_header("Running All Tests", f"{len(specs)} specs")

    table = ui.create_table(["Spec", "Result", "Duration"])
    passed = 0
    failed = 0
    skipped = 0

    for spec_file in specs:
        name = spec_file.replace(".spec.md", "")
        info = manifest.get_spec_info(name)

        # Check whether a non-test output file exists on disk
        if info is None or not any(
            os.path.exists(f) for f in info.output_files
            if not os.path.basename(f).startswith("test_")
        ):
            table.add_row(name, "[dim]NO BUILD[/]", "")
            skipped += 1
            continue

        t0 = time.perf_counter()
        result = core.run_tests(name)
        duration = time.perf_counter() - t0

        if result["success"]:
            table.add_row(name, "[green]PASS[/]", f"{duration:.1f}s")
            passed += 1
        else:
            table.add_row(name, "[red]FAIL[/]", f"{duration:.1f}s")
            failed += 1

    ui.console.print(table)

    summary = f"{passed} passed"
    if failed:
        summary += f", {failed} failed"
    if skipped:
        summary += f", {skipped} no build"

    if failed:
        ui.print_error(summary)
        sys.exit(1)
    elif passed == 0:
        ui.print_warning("No compiled specs to test.")
    else:
        ui.print_success(summary)


def cmd_fix(core: SpecSoloistCore, name: str, no_agent: bool, auto_accept: bool, model: str | None = None):
    """Auto-fix failing tests."""
    _check_api_key()

    ui.print_header("Auto-Fixing Spec", name)

    if no_agent:
        _fix_with_llm(core, name, model)
    else:
        _fix_with_agent(name, auto_accept, model=model)


def _fix_with_agent(name: str, auto_accept: bool, model: str | None = None):
    """Use an AI agent CLI for multi-step self-healing."""
    agent = _detect_agent_cli()
    if not agent:
        ui.print_error("No agent CLI found (claude or gemini). Install one or use --no-agent.")
        sys.exit(1)

    ui.print_info(f"Using {agent} agent with native subagent...")
    if model:
        ui.print_info(f"Model: {model}")

    # Build natural language prompt
    prompt = f"fix: Resolve failing tests for {name}"

    try:
        _run_agent_oneshot(agent, prompt, auto_accept, model=model)
    except Exception as e:
        ui.print_error(f"Agent error: {e}")
        sys.exit(1)


def _fix_with_llm(core: SpecSoloistCore, name: str, model: str | None = None):
    """Direct LLM self-healing (single-shot, no agent iteration)."""
    with ui.spinner(f"Analyzing [bold]{name}[/] failures and generating fix..."):
        try:
            result = core.attempt_fix(name, model=model)
            ui.print_success(result)
        except Exception as e:
            ui.print_error(f"Fix failed: {e}")
            sys.exit(1)


def _preflight_tui(arrangement_arg: str | None) -> None:
    """Pre-validate common error conditions before launching the TUI.

    Raises SystemExit with a clear message for problems that would otherwise
    be swallowed by the TUI's build thread.
    """
    if arrangement_arg and not os.path.exists(arrangement_arg):
        ui.print_error(f"Arrangement file not found: {arrangement_arg}")
        sys.exit(1)
    _check_api_key()


def _run_with_tui(tui_subscriber, build_fn, event_bus=None, command_description: str = ""):
    """Run a build function in a background thread with the Textual TUI in the foreground."""
    import threading
    from .events import BuildEvent, EventType
    from .tui import DashboardApp

    # Emit build.init immediately so the TUI shows something on startup
    if event_bus is not None:
        event_bus.emit(BuildEvent(
            event_type=EventType.BUILD_INIT,
            data={"command": command_description},
        ))

    app = DashboardApp()
    tui_subscriber.app = app

    build_error = None

    def _emit_error(msg: str) -> None:
        if event_bus is not None:
            event_bus.emit(BuildEvent(
                event_type=EventType.BUILD_ERROR,
                data={"error": msg},
            ))

    def _run_build():
        nonlocal build_error
        # Intercept ui.print_error calls to capture the last error message,
        # since Rich output is swallowed by Textual's screen.
        last_error_msg = []
        original_print_error = ui.print_error

        def _capture_error(msg, *a, **kw):
            last_error_msg.append(str(msg))
            original_print_error(msg, *a, **kw)

        ui.print_error = _capture_error
        try:
            build_fn()
        except SystemExit as e:
            if e.code and e.code != 0:
                msg = last_error_msg[-1] if last_error_msg else f"Build exited with code {e.code}"
                _emit_error(msg)
        except Exception as e:
            build_error = e
            _emit_error(str(e))
        finally:
            ui.print_error = original_print_error

    thread = threading.Thread(target=_run_build, daemon=True)
    thread.start()
    app.run()
    thread.join(timeout=2.0)

    if build_error:
        ui.print_error(f"Build error: {build_error}")
        sys.exit(1)


def cmd_dashboard():
    """Connect to a running build's live dashboard via SSE."""
    ui.print_info("sp dashboard connects to a running 'sp conduct --serve' instance.")
    ui.print_info("SSE server mode is not yet implemented (see task 32).")
    ui.print_info("")
    ui.print_info("For now, use 'sp conduct --no-agent --tui' to run a build with a live dashboard.")


def cmd_build(core: SpecSoloistCore, incremental: bool, parallel: bool, workers: int, model: str,
              generate_tests: bool, arrangement_arg: str | None = None):
    """Compile all specs in dependency order using direct LLM API calls (non-agent)."""
    _check_api_key()

    specs = core.list_specs()
    if not specs:
        ui.print_warning("No specs found in src/")
        sys.exit(1)

    mode_parts = []
    if incremental:
        mode_parts.append("incremental")
    if parallel:
        mode_parts.append(f"parallel-{workers}")
    mode_str = f"[{', '.join(mode_parts)}]" if mode_parts else "[full]"

    ui.print_header("Building Project", f"{len(specs)} specs {mode_str}")

    arrangement = _resolve_arrangement(core, arrangement_arg)
    _apply_arrangement(core, arrangement)
    model = _resolve_model(model, arrangement)

    with ui.spinner("Compiling project..."):
        result = core.compile_project(
            model=model,
            generate_tests=generate_tests,
            incremental=incremental,
            parallel=parallel,
            max_workers=workers,
            arrangement=arrangement,
        )

    # Summary Table
    table = ui.create_table(["Result", "Spec", "Details"], title="Build Summary")
    
    for spec in result.specs_compiled:
        table.add_row("[green]Compiled[/]", spec, "Success")
    
    for spec in result.specs_skipped:
        table.add_row("[dim]Skipped[/]", spec, "Unchanged")
        
    for spec in result.specs_failed:
        error = result.errors.get(spec, "Unknown error")
        # Truncate long errors
        if len(error) > 50:
            error = error[:47] + "..."
        table.add_row("[red]Failed[/]", spec, error)

    ui.console.print(table)

    if result.success:
        ui.print_success("Build complete.")
    else:
        ui.print_error("Build failed.")
        sys.exit(1)


def cmd_compose(core: SpecSoloistCore, request: str, no_agent: bool, auto_accept: bool,
                model: str | None = None):
    """Draft architecture and specs from natural language."""
    ui.print_header("Composing System", request[:50] + "..." if len(request) > 50 else request)

    if no_agent:
        _compose_with_llm(core, request, auto_accept)
    else:
        _compose_with_agent(request, auto_accept, model=model)


def _compose_with_agent(request: str, auto_accept: bool, model: str | None = None):
    """Use an AI agent CLI for multi-step composition."""
    agent = _detect_agent_cli()
    if not agent:
        ui.print_error("No agent CLI found (claude or gemini). Install one or use --no-agent.")
        sys.exit(1)

    ui.print_info(f"Using {agent} agent with native subagent...")
    if model:
        ui.print_info(f"Model: {model}")

    # Simple natural language prompt - the native subagent handles the rest
    prompt = f"compose: {request}"

    try:
        _run_agent_oneshot(agent, prompt, auto_accept, model=model)
    except Exception as e:
        ui.print_error(f"Agent error: {e}")
        sys.exit(1)


def _compose_with_llm(core: SpecSoloistCore, request: str, auto_accept: bool):
    """Direct LLM composition (single-shot, no agent iteration)."""
    _check_api_key()

    ui.print_info("Using direct LLM call (no agent)...")

    # Initialize Composer
    composer = SpecComposer(core.project_dir)

    with ui.spinner("Drafting architecture..."):
        architecture = composer.draft_architecture(request)

    # Interactive loop
    while True:
        # Display Architecture
        ui.print_header("Architecture Draft", architecture.description)

        arch_table = ui.create_table(["Component", "Type", "Dependencies", "Description"])
        for comp in architecture.components:
            deps = ", ".join(comp.dependencies) if comp.dependencies else "-"
            arch_table.add_row(
                f"[bold]{comp.name}[/]",
                comp.type,
                deps,
                comp.description
            )
        ui.console.print(arch_table)
        ui.console.print()

        if auto_accept:
            break

        from rich.prompt import Prompt, Confirm
        choice = Prompt.ask(
            "[bold]Action[/]",
            choices=["proceed", "edit", "cancel"],
            default="proceed"
        )

        if choice == "cancel":
            ui.print_warning("Composition cancelled.")
            return

        if choice == "edit":
            # Edit in external editor
            import tempfile
            import subprocess
            import shlex

            with tempfile.NamedTemporaryFile(suffix=".yaml", mode='w', delete=False) as tf:
                tf.write(architecture.to_yaml())
                tf_path = tf.name

            editor = os.environ.get("EDITOR", "vim")

            try:
                subprocess.call(shlex.split(editor) + [tf_path])

                # Read back
                with open(tf_path, 'r') as f:
                    new_yaml = f.read()

                # Parse
                try:
                    architecture = Architecture.from_yaml(new_yaml)
                    ui.print_success("Architecture updated from editor.")
                except Exception as e:
                    ui.print_error(f"Failed to parse updated architecture: {e}")
                    if not Confirm.ask("Retry editing?", default=True):
                        return
                    continue  # Loop back to display and prompt

            finally:
                if os.path.exists(tf_path):
                    os.remove(tf_path)
            continue  # Show updated architecture

        if choice == "proceed":
            break

    with ui.spinner("Generating specs..."):
        spec_paths = composer.generate_specs(architecture)

    ui.print_success(f"Generated {len(spec_paths)} specs:")
    for path in spec_paths:
        rel_path = os.path.relpath(path, os.getcwd())
        ui.console.print(f"  - [bold]{rel_path}[/]")

    ui.print_info("Review specs, then run 'sp conduct' to build.")


def cmd_vibe(
    core: SpecSoloistCore,
    brief: str | None,
    template: str | None,
    pause_for_review: bool,
    resume: bool,
    no_agent: bool,
    auto_accept: bool,
    model: str | None,
):
    """Single-command pipeline: compose specs from a brief, then build."""
    if brief is None:
        ui.print_error("Provide a brief as a .md file path or a plain string.")
        ui.print_info("Example: sp vibe brief.md  or  sp vibe 'Add a todo app'")
        sys.exit(1)

    # Resolve brief content
    if brief.endswith(".md") and os.path.exists(brief):
        with open(brief, "r", encoding="utf-8") as fh:
            request = fh.read().strip()
        ui.print_info(f"Reading brief from [bold]{brief}[/]")
    else:
        request = brief

    ui.print_header("SpecSoloist Vibe", request[:60] + "..." if len(request) > 60 else request)

    # Step 1: Compose specs from the brief
    ui.print_step("Step 1 / 2: Composing specs from brief...")
    cmd_compose(core, request, no_agent=no_agent, auto_accept=auto_accept or True, model=model)

    # Step 2: Optional pause for review
    if pause_for_review:
        # List specs written to the project src dir
        specs = core.list_specs()
        if specs:
            ui.print_info("Specs written:")
            for s in specs:
                ui.console.print(f"  - [bold]{s}[/]")
        try:
            input("\nEdit specs if needed, then press Enter to build: ")
        except (EOFError, KeyboardInterrupt):
            ui.print_warning("\nSkipping pause (non-interactive mode).")

    # Step 3: Build (conduct)
    ui.print_step("Step 2 / 2: Building specs...")
    cmd_conduct(
        core,
        src_dir=None,
        no_agent=no_agent,
        auto_accept=auto_accept or True,
        incremental=False,
        parallel=False,
        workers=4,
        model=model,
        arrangement_arg=None,
        resume=resume,
        force=False,
    )


def cmd_conduct(core: SpecSoloistCore, src_dir: str | None, no_agent: bool, auto_accept: bool,
                 incremental: bool, parallel: bool, workers: int, model: str | None = None,
                 arrangement_arg: str | None = None, resume: bool = False, force: bool = False):
    """Orchestrate project build."""
    ui.print_header("Conducting Build", src_dir or "project specs")

    if no_agent:
        arrangement = _resolve_arrangement(core, arrangement_arg)
        effective_model = _resolve_model(model, arrangement)
        _conduct_with_llm(core, src_dir, incremental, parallel, workers, arrangement=arrangement,
                          model=effective_model, resume=resume, force=force)
    else:
        _conduct_with_agent(src_dir, auto_accept, model=model, arrangement_arg=arrangement_arg,
                            resume=resume, force=force)


def _conduct_with_agent(src_dir: str | None, auto_accept: bool, model: str | None = None,
                        arrangement_arg: str | None = None, resume: bool = False,
                        force: bool = False):
    """Use an AI agent CLI for multi-step orchestrated build."""
    agent = _detect_agent_cli()
    if not agent:
        ui.print_error("No agent CLI found (claude or gemini). Install one or use --no-agent.")
        sys.exit(1)

    ui.print_info(f"Using {agent} agent with native subagent...")
    if model:
        ui.print_info(f"Model: {model}")

    spec_dir = src_dir or "src/"

    # Detect if this is a quine attempt (spec_dir is score/)
    is_quine = "score" in spec_dir

    if is_quine:
        # Create quine output directory
        quine_dir = "build/quine"
        os.makedirs(f"{quine_dir}/src/specsoloist", exist_ok=True)
        os.makedirs(f"{quine_dir}/src/spechestra", exist_ok=True)
        os.makedirs(f"{quine_dir}/tests", exist_ok=True)

        ui.print_info(f"🔄 Quine mode: Will regenerate code to {quine_dir}/")

        prompt = (
            f"conduct: Read all *.spec.md files in {spec_dir}, resolve their dependency order, "
            f"then compile each spec into working code by spawning soloist subagents. "
            f"\n\n**CRITICAL - Output Paths (MUST be followed exactly):**\n"
            f"- Write specsoloist implementations to: {quine_dir}/src/specsoloist/<name>.py\n"
            f"- Write spechestra implementations to: {quine_dir}/src/spechestra/<name>.py\n"
            f"- Write tests to: {quine_dir}/tests/test_<name>.py\n"
            f"- Run tests with: PYTHONPATH={quine_dir}/src uv run python -m pytest <test_path> -v\n\n"
            f"**WARNING**: Do NOT write to src/ or tests/ directly — those contain the original source. "
            f"ALL output MUST go to {quine_dir}/. "
            f"When spawning soloist subagents, include the FULL output paths in each soloist prompt.\n\n"
            f"This is a QUINE VALIDATION - you are intentionally regenerating code to verify specs are complete. "
            f"Do NOT skip compilation because code already exists elsewhere. "
            f"Run the full test suite from {quine_dir}/tests/ when done."
        )

        # If an arrangement is provided, inject per-spec overrides and static artifacts
        # into the quine prompt, with all dest paths redirected to build/quine/.
        if arrangement_arg and os.path.exists(arrangement_arg):
            try:
                import yaml as _yaml
                from .schema import Arrangement as _Arrangement
                with open(arrangement_arg) as _f:
                    _arr = _Arrangement(**_yaml.safe_load(_f))
                _project_root = os.getcwd()

                if _arr.output_paths.overrides:
                    prompt += "\n\n**Per-spec output path overrides** (use these exact paths):\n"
                    for _spec_name, _ov in _arr.output_paths.overrides.items():
                        if _ov.implementation:
                            prompt += f"- {_spec_name} implementation: {quine_dir}/{_ov.implementation}\n"
                        if _ov.tests:
                            prompt += f"- {_spec_name} tests: {quine_dir}/{_ov.tests}\n"

                if _arr.static:
                    prompt += "\n\n**After compilation, copy these static artifacts verbatim:**\n"
                    for _entry in _arr.static:
                        _src = os.path.join(_project_root, _entry.source)
                        _dst = os.path.join(quine_dir, _entry.dest)
                        prompt += f"- Copy {_src} → {_dst}\n"
            except Exception:
                pass  # arrangement loading is best-effort; quine still works without it

    else:
        prompt = (
            f"conduct: Read all *.spec.md files in {spec_dir}, resolve their dependency order, "
            f"then compile each spec into working code by spawning soloist subagents. "
        )
        
        if arrangement_arg:
            # Resolve the project base directory (parent of spec dir)
            project_dir = os.path.abspath(os.path.join(spec_dir, ".."))
            prompt += f"\n\n**Arrangement**: Read the arrangement file at '{arrangement_arg}' for build configuration. "
            prompt += f"The project base directory is '{project_dir}'. "
            prompt += "Resolve output_paths templates relative to the project base directory "
            prompt += f"(e.g., 'src/{{name}}.ts' → '{project_dir}/src/{{name}}.ts'). "
            prompt += "Write any environment.config_files to the project base directory, then run environment.setup_commands there before spawning soloists."
        else:
            prompt += "Write implementations to the appropriate src/ paths and tests to tests/. "

        prompt += "\nRun the full test suite when done."

    if force:
        prompt += (
            "\n\n**Build mode**: --force is set. Recompile ALL specs regardless of manifest state. "
            "Do not skip any spec."
        )
    elif resume:
        prompt += (
            "\n\n**Build mode**: --resume is set. Before compiling each spec, check the build "
            "manifest (.specsoloist-manifest.json) to see if it was already compiled with the same "
            "spec hash and all output files still exist on disk. Skip specs that are up-to-date; "
            "only compile specs that are missing, stale, or whose dependencies were recompiled this run."
        )

    if model:
        prompt += (
            f'\n\n**Model**: When spawning soloist subagents via the Task tool, '
            f'set model: "{model}".'
        )

    try:
        _run_agent_oneshot(agent, prompt, auto_accept, model=model)
    except Exception as e:
        ui.print_error(f"Agent error: {e}")
        sys.exit(1)


def _conduct_with_llm(core: SpecSoloistCore, src_dir: str | None, incremental: bool, parallel: bool, workers: int,
                      arrangement=None, model: str | None = None, resume: bool = False, force: bool = False):
    """Direct LLM build (single-shot compilation, no agent iteration)."""
    _check_api_key()

    ui.print_info("Using direct LLM calls (no agent)...")

    # Resolve effective incremental flag:
    # --force: always recompile (incremental=False)
    # --resume or default: use manifest staleness (incremental=True)
    # Legacy --incremental flag also maps to True
    effective_incremental = not force  # True unless --force

    # If src_dir is provided, we should use it for spec discovery
    # SpecConductor uses its internal core for compilation, but we want it
    # to find specs in src_dir if specified.

    project_base = core.root_dir
    if src_dir:
        # Resolve the absolute path to the directory containing 'src'
        # e.g. if src_dir is 'examples/ts_demo/src/', project_base is 'examples/ts_demo/'
        project_base = os.path.abspath(os.path.join(src_dir, ".."))

    conductor = SpecConductor(project_base)

    if src_dir:
        conductor.parser.src_dir = os.path.abspath(src_dir)
        conductor.resolver.parser.src_dir = os.path.abspath(src_dir)
        # Redirect the runner to write relative to the project base
        conductor._core.runner.build_dir = project_base

    # Show resume/force mode header and pre-computed skip plan
    if resume:
        ui.print_info("Resuming build from manifest...")
    elif force:
        ui.print_info("Force mode: recompiling all specs...")

    if effective_incremental and (resume or not force):
        _show_resume_plan(conductor._core, parallel)

    with ui.spinner("Orchestrating build..."):
        result = conductor.build(
            incremental=effective_incremental,
            parallel=parallel,
            max_workers=workers,
            arrangement=arrangement,
            model=model,
        )

    table = ui.create_table(["Result", "Spec", "Details"], title="Conductor Report")

    for spec in result.specs_compiled:
        table.add_row("[green]COMPILED[/]", spec, "")

    for spec in result.specs_skipped:
        table.add_row("[dim]SKIPPED[/]", spec, "[dim]cached[/]")

    for spec in result.specs_failed:
        error = result.errors.get(spec, "Unknown error")
        if len(error) > 50:
            error = error[:47] + "..."
        table.add_row("[red]FAILED[/]", spec, error)

    ui.console.print(table)

    # Summary line
    parts = []
    if result.specs_compiled:
        parts.append(f"{len(result.specs_compiled)} compiled")
    if result.specs_skipped:
        parts.append(f"{len(result.specs_skipped)} skipped")
    if result.specs_failed:
        parts.append(f"{len(result.specs_failed)} failed")
    summary = ", ".join(parts) if parts else "nothing to do"

    if result.success:
        ui.print_success(f"Conductor finished: {summary}.")
    else:
        ui.print_error(f"Conductor reported failures: {summary}.")
        sys.exit(1)


def _show_resume_plan(core: SpecSoloistCore, parallel: bool):
    """Print a pre-flight summary of which specs will be compiled vs skipped."""
    from .manifest import IncrementalBuilder, compute_file_hash

    try:
        build_order = core.resolver.resolve_build_order()
        manifest = core._get_manifest()
        builder = IncrementalBuilder(manifest, core.config.src_path)

        # Compute hashes and deps for all specs
        spec_hashes: dict[str, str] = {}
        spec_deps: dict[str, list[str]] = {}
        for name in build_order:
            spec_path = os.path.join(core.parser.src_dir, f"{name}.spec.md")
            spec_hashes[name] = compute_file_hash(spec_path)
            try:
                parsed = core.parser.parse_spec(name)
                spec_deps[name] = parsed.metadata.dependencies or []
            except Exception:
                spec_deps[name] = []

        # Compute rebuild plan (respects cascade)
        to_rebuild = set(builder.get_rebuild_plan(build_order, spec_hashes, spec_deps))

        if not to_rebuild:
            ui.print_info("All specs are up-to-date — nothing to recompile.")
            return

        for name in build_order:
            if name in to_rebuild:
                info = manifest.get_spec_info(name)
                if info is None:
                    reason = "never built"
                elif compute_file_hash(os.path.join(core.parser.src_dir, f"{name}.spec.md")) != info.spec_hash:
                    reason = "spec changed"
                elif any(not os.path.exists(f) for f in info.output_files):
                    reason = "output missing"
                else:
                    # Cascade: a dependency changed
                    changed_deps = [d for d in spec_deps.get(name, []) if d in to_rebuild]
                    reason = f"dep {changed_deps[0]} changed" if changed_deps else "stale"
                ui.print_step(f"  [bold]{name}[/]  [yellow]COMPILING[/] ({reason})")
            else:
                ui.print_step(f"  [bold]{name}[/]  [dim]SKIPPED (cached)[/]")
        ui.console.print()
    except Exception:
        # If plan computation fails, proceed silently — the build will still work
        pass


def cmd_diff(
    core: SpecSoloistCore,
    left: str,
    right: str,
    label_left: str | None,
    label_right: str | None,
    report: str,
    runs: int | None,
):
    """Compare two build output directories semantically."""
    from .build_diff import run_diff, list_build_runs

    if runs is not None:
        # Compare the last N recorded runs in build/runs/
        build_runs_dir = os.path.join(os.getcwd(), "build", "runs")
        all_runs = list_build_runs(build_runs_dir)
        if len(all_runs) < 2:
            ui.print_error(
                f"Need at least 2 recorded runs in {build_runs_dir}; "
                f"found {len(all_runs)}. Run 'sp conduct' with run archiving enabled first."
            )
            sys.exit(1)
        selected = all_runs[-runs:] if runs <= len(all_runs) else all_runs
        if len(selected) < 2:
            ui.print_error(f"Not enough runs to compare (found {len(selected)}).")
            sys.exit(1)
        left = selected[-2].path
        right = selected[-1].path
        label_left = label_left or selected[-2].run_id
        label_right = label_right or selected[-1].run_id

    left_abs = os.path.abspath(left)
    right_abs = os.path.abspath(right)
    label_left = label_left or os.path.basename(left_abs.rstrip("/"))
    label_right = label_right or os.path.basename(right_abs.rstrip("/"))

    if not os.path.isdir(left_abs):
        ui.print_error(f"Left directory not found: {left_abs}")
        sys.exit(1)
    if not os.path.isdir(right_abs):
        ui.print_error(f"Right directory not found: {right_abs}")
        sys.exit(1)

    report_abs = os.path.abspath(report)

    ui.print_header("Build Diff", f"{label_left}  →  {label_right}")

    summary = run_diff(left_abs, right_abs, report_abs, label_left, label_right)

    if summary.failed > 0 or summary.missing_right > 0:
        sys.exit(1)


def cmd_spec_diff(core: SpecSoloistCore, spec_name: str, json_output: bool = False):
    """Compare a spec against its compiled implementation and report drift."""
    from .spec_diff import diff_spec, format_result_text, format_result_json

    root_dir = core.root_dir
    result = diff_spec(spec_name, root_dir)

    if json_output:
        print(format_result_json(result))
    else:
        print(format_result_text(result))

    # Exit 1 if there are MISSING or TEST_GAP issues
    critical = [i for i in result.issues if i.kind in ("MISSING", "TEST_GAP")]
    if critical:
        sys.exit(1)


def cmd_respec(core: SpecSoloistCore, file_path: str, test_path: str, out_path: str, no_agent: bool, model: str, auto_accept: bool):
    """Reverse engineer code to spec."""
    ui.print_header("Respec: Code → Spec", file_path)

    if no_agent:
        _respec_with_llm(core, file_path, test_path, out_path, model)
    else:
        _respec_with_agent(file_path, test_path, out_path, auto_accept, model=model)


def _respec_with_agent(file_path: str, test_path: str, out_path: str, auto_accept: bool,
                       model: str | None = None):
    """Use an AI agent CLI for multi-step respec with validation."""
    agent = _detect_agent_cli()
    if not agent:
        ui.print_error("No agent CLI found (claude or gemini). Install one or use --no-agent.")
        sys.exit(1)

    ui.print_info(f"Using {agent} agent with native subagent...")
    if model:
        ui.print_info(f"Model: {model}")

    # Build natural language prompt
    prompt_parts = [f"respec {file_path}"]
    if test_path:
        prompt_parts.append(f"using tests from {test_path}")
    if out_path:
        prompt_parts.append(f"to {out_path}")
    prompt = " ".join(prompt_parts)

    try:
        _run_agent_oneshot(agent, prompt, auto_accept, model=model)
    except Exception as e:
        ui.print_error(f"Agent error: {e}")
        sys.exit(1)


def _respec_with_llm(core: SpecSoloistCore, file_path: str, test_path: str, out_path: str, model: str):
    """Direct LLM respec (single-shot, no validation loop)."""
    _check_api_key()

    ui.print_info("Using direct LLM call (no agent)...")

    respecer = Respecer(core.config)

    with ui.spinner("Analyzing code and generating spec..."):
        try:
            spec_content = respecer.respec(file_path, test_path, model)
        except Exception as e:
            ui.print_error(f"Respec failed: {e}")
            sys.exit(1)

    if out_path:
        with open(out_path, 'w') as f:
            f.write(spec_content)
        ui.print_success(f"Spec saved to: [bold]{out_path}[/]")
        ui.print_info("Run 'sp validate' to check the generated spec.")
    else:
        ui.console.print(ui.Panel(spec_content, title="Generated Spec", border_style="blue"))
        ui.print_info("Use --out <path> to save to file.")


def cmd_doctor(arrangement_arg: str | None = None):
    """Check environment health and report status for each item."""
    import shutil
    import subprocess

    ui.print_header("SpecSoloist Doctor", "Environment health check")

    critical_failure = False

    # Python version
    py = sys.version_info
    py_str = f"{py.major}.{py.minor}.{py.micro}"
    if py >= (3, 10):
        ui.console.print(f"[success]✓[/] Python {py_str} (meets >=3.10 requirement)")
    else:
        ui.console.print(f"[error]✗[/] Python {py_str} — requires Python >=3.10")
        critical_failure = True

    # API keys — check all supported providers
    _provider_keys = {
        "ANTHROPIC_API_KEY": "anthropic",
        "GEMINI_API_KEY": "gemini/google",
        "OPENAI_API_KEY": "openai",
        "OPENROUTER_API_KEY": "openrouter",
    }
    has_any_key = False
    for key_name, provider_label in _provider_keys.items():
        if key_name in os.environ:
            ui.console.print(f"[success]✓[/] {key_name} set  [dim]({provider_label})[/]")
            has_any_key = True
        else:
            ui.console.print(f"[warning]~[/] {key_name} not set  [dim]({provider_label})[/]")

    # Check Ollama
    ollama_base = os.environ.get("OLLAMA_BASE_URL", "")
    if ollama_base:
        ui.console.print(f"[success]✓[/] OLLAMA_BASE_URL set → {ollama_base}  [dim](ollama)[/]")
        has_any_key = True
    else:
        ui.console.print("[dim]~  OLLAMA_BASE_URL not set  (ollama — optional)[/]")

    if not has_any_key:
        ui.console.print("[error]✗[/] No API key set — set at least one of ANTHROPIC_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY")
        critical_failure = True

    # Agent CLIs
    claude_path = shutil.which("claude")
    gemini_path = shutil.which("gemini")

    if claude_path:
        try:
            ver = subprocess.run(
                ["claude", "--version"], capture_output=True, text=True, timeout=5
            )
            ver_str = ver.stdout.strip() or ver.stderr.strip()
            ui.console.print(f"[success]✓[/] claude CLI found ({ver_str or claude_path})")
        except Exception:
            ui.console.print(f"[success]✓[/] claude CLI found ({claude_path})")
    else:
        ui.console.print("[warning]~[/] claude CLI not found")

    if gemini_path:
        ui.console.print(f"[success]✓[/] gemini CLI found ({gemini_path})")
    else:
        ui.console.print("[warning]~[/] gemini CLI not found")

    if not claude_path and not gemini_path:
        ui.console.print("[warning]~[/] No agent CLI found — direct LLM mode still works (--no-agent)")

    # uv
    if shutil.which("uv"):
        ui.console.print("[success]✓[/] uv found")
    else:
        ui.console.print("[warning]~[/] uv not found — needed for Python test execution")

    # Docker
    if shutil.which("docker"):
        ui.console.print("[success]✓[/] Docker found")
    else:
        ui.console.print("[dim]~  Docker not found (sandbox mode unavailable)[/]")

    # Spec count
    spec_count = 0
    for search_dir in ("src", "specs"):
        abs_dir = os.path.join(os.getcwd(), search_dir)
        if os.path.isdir(abs_dir):
            for root, _dirs, files in os.walk(abs_dir):
                spec_count += sum(1 for f in files if f.endswith(".spec.md"))

    if spec_count > 0:
        ui.console.print(f"[success]✓[/] {spec_count} spec(s) found")
    else:
        ui.console.print("[dim]~  0 specs found — run 'sp init' to create a project[/]")

    # Arrangement env_vars check
    arr_path = arrangement_arg
    if arr_path is None:
        # Auto-discover arrangement.yaml in cwd
        candidate = os.path.join(os.getcwd(), "arrangement.yaml")
        if os.path.exists(candidate):
            arr_path = candidate

    if arr_path and os.path.exists(arr_path):
        try:
            import yaml
            with open(arr_path) as f:
                arr_data = yaml.safe_load(f)
            from .schema import Arrangement
            arr = Arrangement(**arr_data)
            if arr.env_vars:
                ui.console.print()
                ui.console.print(f"[dim]Arrangement env_vars ({os.path.basename(arr_path)}):[/]")
                for var_name, var_info in arr.env_vars.items():
                    is_set = var_name in os.environ
                    if is_set:
                        msg = f"[success]✓[/] {var_name} set"
                        if not var_info.required:
                            msg += " [dim](optional)[/]"
                        ui.console.print(msg)
                    elif var_info.required:
                        ui.console.print(
                            f"[error]✗[/] {var_name} not set  "
                            f"[dim](required by arrangement: {var_info.description})[/]"
                        )
                        critical_failure = True
                    else:
                        example_hint = f", default: {var_info.example}" if var_info.example else ""
                        ui.console.print(
                            f"[success]✓[/] {var_name} not set  "
                            f"[dim](optional — {var_info.description}{example_hint})[/]"
                        )
            # Static artifact source paths check
            if arr.static:
                for entry in arr.static:
                    src = os.path.join(os.getcwd(), entry.source)
                    if not os.path.exists(src):
                        ui.console.print(
                            f"[warning]⚠[/] Static artifact not found: {entry.source}  "
                            f"[dim](declared in {os.path.basename(arr_path)})[/]"
                        )
        except Exception as e:
            ui.console.print(f"[warning]~[/] Could not parse arrangement env_vars: {e}")

    # Installed skill staleness check
    _current_version = importlib.metadata.version("specsoloist")
    _skill_dirs_to_check = [".claude/agents", ".claude/skills"]
    _stale_version: str | None = None
    for _skill_dir in _skill_dirs_to_check:
        _abs_skill_dir = os.path.join(os.getcwd(), _skill_dir)
        if not os.path.isdir(_abs_skill_dir):
            continue
        for _root, _dirs, _files in os.walk(_abs_skill_dir):
            for _fname in _files:
                if not _fname.endswith(".md"):
                    continue
                _fpath = os.path.join(_root, _fname)
                try:
                    with open(_fpath) as _f:
                        _first_line = _f.readline()
                    if _first_line.startswith("<!-- sp-version:"):
                        _installed_ver = _first_line.strip().removeprefix("<!-- sp-version:").removesuffix("-->").strip()
                        if _installed_ver != _current_version:
                            _stale_version = _installed_ver
                            break
                except Exception:
                    pass
            if _stale_version:
                break
        if _stale_version:
            break

    if _stale_version:
        ui.console.print(
            f"[warning]⚠[/] Installed skills are from specsoloist {_stale_version} "
            f"— current version is {_current_version}.\n"
            "  Run: [bold]sp install-skills[/]"
        )

    ui.console.print()
    if critical_failure:
        ui.print_error("One or more critical checks failed.")
        sys.exit(1)
    else:
        ui.print_success("All critical checks passed.")


def cmd_status(core: SpecSoloistCore, arrangement_arg: str | None = None, json_output: bool = False):
    """Show compilation state of each spec from the build manifest."""
    import json as _json
    from datetime import datetime, timezone

    arrangement = _resolve_arrangement(core, arrangement_arg)
    if arrangement:
        core.parser.src_dir = os.path.abspath(arrangement.specs_path)

    manifest = core._get_manifest()
    specs = core.list_specs()

    if not specs:
        path = arrangement.specs_path if arrangement else "src/"
        if json_output:
            print(_json.dumps({"specs": []}))
        else:
            ui.print_warning(f"No specs found in {path}.")
            ui.print_info("Create one with: sp create <name> '<description>'")
        return

    now = datetime.now(timezone.utc)

    def _rel_time(iso_str: str) -> str:
        try:
            dt = datetime.fromisoformat(iso_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = now - dt
            seconds = int(delta.total_seconds())
            if seconds < 60:
                return f"{seconds}s ago"
            if seconds < 3600:
                return f"{seconds // 60}m ago"
            if seconds < 86400:
                return f"{seconds // 3600}h ago"
            return f"{seconds // 86400}d ago"
        except Exception:
            return "unknown"

    spec_records = []
    table = None if json_output else ui.create_table(
        ["Spec", "Compiled", "Tests", "Last Built"], title="Spec Status"
    )

    for spec_file in specs:
        name = spec_file.replace(".spec.md", "")

        # Reference specs: show CONTEXT instead of compilation status
        try:
            parsed = core.parser.parse_spec(name)
            if parsed.metadata.type == "reference":
                if json_output:
                    spec_records.append({
                        "name": name,
                        "type": "reference",
                        "compiled": None,
                        "tests_pass": None,
                        "last_built": None,
                    })
                else:
                    table.add_row(name, "[blue]CONTEXT[/]", "[dim]—[/]", "[dim]—[/]")
                continue
        except Exception:
            pass

        info = manifest.get_spec_info(name)

        if info is None:
            if json_output:
                spec_records.append({
                    "name": name,
                    "type": "spec",
                    "compiled": False,
                    "tests_pass": False,
                    "last_built": None,
                })
            else:
                table.add_row(name, "[red]✗[/]", "[red]✗[/]", "never")
            continue

        # Check implementation file on disk
        impl_exists = any(
            os.path.exists(f) for f in info.output_files
            if not os.path.basename(f).startswith("test_")
        )

        # Check test file on disk
        test_files = [f for f in info.output_files if os.path.basename(f).startswith("test_")]
        tests_ok = bool(test_files and os.path.exists(test_files[0]))
        has_tests = bool(test_files)

        if json_output:
            spec_records.append({
                "name": name,
                "type": "spec",
                "compiled": impl_exists,
                "tests_pass": tests_ok if has_tests else None,
                "last_built": info.built_at,
            })
        else:
            compiled_cell = "[green]✓[/]" if impl_exists else "[red]✗[/]"
            if has_tests and tests_ok:
                tests_cell = "[green]✓[/]"
            elif has_tests:
                tests_cell = "[red]FAIL[/]"
            else:
                tests_cell = "[red]✗[/]"
            last_built = _rel_time(info.built_at)
            table.add_row(name, compiled_cell, tests_cell, last_built)

    if json_output:
        print(_json.dumps({"specs": spec_records}, indent=2))
    else:
        ui.console.print(table)


_INIT_ARRANGEMENT = """\
# arrangement.yaml
#
# Bridges your specs to a concrete build environment.
# Run: sp conduct specs/ --arrangement arrangement.yaml
#
# Run `sp schema` to see all available fields.
# Run `sp help arrangement` for a full narrative reference.

target_language: python

# Directory where your .spec.md files live (default: src/).
# Change this if your specs are in a different location, e.g. specs/
# specs_path: specs/

output_paths:
  implementation: src/{path}.py     # {path} includes subdirs; {name} is the leaf
  tests: tests/test_{name}.py
  # Per-spec overrides for non-standard locations:
  # overrides:
  #   special_module:
  #     implementation: src/special/module.py

environment:
  tools:
    - uv
    - ruff
    - pytest
  setup_commands:
    - uv sync
  # dependencies:
  #   some-package: ">=1.0,<2.0"

build_commands:
  compile: ""               # Leave empty for interpreted languages
  lint: uv run ruff check .
  test: uv run pytest

constraints:
  - Must pass ruff with 0 errors
  - Must use type hints for all public function signatures

# Pin the LLM model for this project (optional).
# Overridden by --model flag. Falls back to SPECSOLOIST_LLM_MODEL env var.
# model: claude-sonnet-4-6

# Declare environment variables your project needs (sp doctor will warn if unset):
# env_vars:
#   DATABASE_URL:
#     description: "PostgreSQL connection string"
#     required: true
#     example: "postgresql://user:pass@localhost/mydb"
"""

_INIT_ARRANGEMENT_TYPESCRIPT = """\
# arrangement.yaml (TypeScript)
#
# Bridges your specs to a TypeScript/Node.js build environment.
# Run: sp conduct specs/ --arrangement arrangement.yaml
#
# Run `sp schema` to see all available fields.
# Run `sp help arrangement` for a full narrative reference.

target_language: typescript

# specs_path: specs/    # default is src/

output_paths:
  implementation: src/{path}.ts      # {path} includes subdirs; {name} is the leaf
  tests: tests/{name}.test.ts
  # overrides:
  #   chat_route:
  #     implementation: src/app/api/chat/route.ts

environment:
  tools:
    - npm
    - npx
    - tsx
    - vitest
  config_files:
    package.json: |
      {
        "name": "{project_name}",
        "version": "0.1.0",
        "scripts": {
          "test": "vitest",
          "build": "tsc --noEmit"
        },
        "devDependencies": {
          "typescript": "^5.0.0",
          "vitest": "^1.0.0",
          "tsx": "^4.0.0",
          "@types/node": "^20.0.0"
        }
      }
    tsconfig.json: |
      {
        "compilerOptions": {
          "target": "ES2020",
          "module": "ESNext",
          "moduleResolution": "node",
          "strict": true,
          "esModuleInterop": true,
          "skipLibCheck": true,
          "outDir": "./dist"
        },
        "include": ["src/**/*"],
        "exclude": ["node_modules", "tests"]
      }
  setup_commands:
    - npm install --no-package-lock

build_commands:
  compile: npx tsc --noEmit
  lint: ""
  test: npx vitest run {file}

constraints:
  - Must follow strict TypeScript mode
  - Must use ES6 modules (import/export)
  - Must include type definitions for all exports
"""

_INIT_GITIGNORE = """\
# Build artifacts
build/
dist/
*.egg-info/

# SpecSoloist
.specsoloist-manifest.json
.spechestra/

# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
.env

# Node / TypeScript
node_modules/
.npm-cache/
dist/
*.js.map

# Editor
.idea/
.vscode/
*.swp
.DS_Store
"""


def _find_arrangements_dir() -> str | None:
    """Find the bundled arrangements directory."""
    try:
        import importlib.resources as pkg_resources
        arr_ref = pkg_resources.files('specsoloist').joinpath('arrangements')
        arr_path = str(arr_ref)
        if os.path.isdir(arr_path):
            return arr_path
    except Exception:
        pass

    # Fallback: relative to this file (development installs)
    candidate = os.path.join(os.path.dirname(__file__), 'arrangements')
    abs_path = os.path.abspath(candidate)
    if os.path.isdir(abs_path):
        return abs_path

    return None


def _list_templates() -> list[dict[str, str]]:
    """Return a list of available templates as [{"name": ..., "description": ...}]."""
    arr_dir = _find_arrangements_dir()
    if not arr_dir:
        return []

    templates = []
    for filename in sorted(os.listdir(arr_dir)):
        if not filename.endswith('.yaml'):
            continue
        template_name = filename[:-5]  # strip .yaml
        filepath = os.path.join(arr_dir, filename)
        description = ""
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    # First non-empty comment line that isn't a Usage: line is the description
                    text = line.lstrip('#').strip()
                    if text and not text.startswith('Usage:') and not text.startswith('Requires:'):
                        description = text
                        break
                elif line:
                    break
        templates.append({"name": template_name, "description": description})
    return templates


def cmd_list_templates():
    """List available arrangement templates."""
    templates = _list_templates()
    if not templates:
        ui.print_warning("No templates found.")
        return

    ui.print_header("Arrangement Templates", "Available for sp init --template")
    for t in templates:
        ui.print_step(f"  [bold]{t['name']}[/]  — {t['description']}")
    ui.console.print()
    ui.print_info("Usage: sp init <project> --template <name>")


def cmd_init(name: str, arrangement: str = "python", template: str | None = None):
    """Scaffold a new SpecSoloist project directory."""
    project_dir = os.path.abspath(name)

    if os.path.exists(project_dir):
        ui.print_error(f"Directory already exists: {project_dir}")
        sys.exit(1)

    os.makedirs(os.path.join(project_dir, "specs"))

    if template is not None:
        # Load from bundled template
        arr_dir = _find_arrangements_dir()
        if not arr_dir:
            ui.print_error("Arrangements directory not found. Ensure specsoloist is properly installed.")
            sys.exit(1)
        template_path = os.path.join(arr_dir, f"{template}.yaml")
        if not os.path.exists(template_path):
            available = [t["name"] for t in _list_templates()]
            ui.print_error(f"Unknown template: {template!r}. Available: {', '.join(available)}")
            sys.exit(1)
        with open(template_path) as f:
            arrangement_content = f.read()
        label = template
    else:
        arrangement_content = (
            _INIT_ARRANGEMENT_TYPESCRIPT if arrangement == "typescript" else _INIT_ARRANGEMENT
        )
        label = arrangement

    with open(os.path.join(project_dir, "arrangement.yaml"), "w") as f:
        f.write(arrangement_content)

    with open(os.path.join(project_dir, ".gitignore"), "w") as f:
        f.write(_INIT_GITIGNORE)

    ui.print_success(f"Created project: [bold]{name}/[/]  [{label}]")
    ui.print_step("  specs/            ← put your .spec.md files here")
    ui.print_step("  arrangement.yaml  ← build configuration")
    ui.print_step("  .gitignore")
    ui.console.print()
    ui.print_info("Next steps:")
    ui.print_step(f"  cd {name}")
    if template == "python-fasthtml":
        ui.print_step("  uv init && uv add python-fasthtml pytest httpx  # set up Python project")
    elif template == "nextjs-vitest":
        ui.print_step("  npm init next-app@latest . -- --typescript       # set up Next.js project")
    elif template == "nextjs-playwright":
        ui.print_step("  npm init next-app@latest . -- --typescript       # set up Next.js project")
        ui.print_step("  npx playwright install --with-deps               # install Playwright browsers")
    ui.print_step("  sp compose 'describe your project'   # draft specs")
    ui.print_step("  sp conduct specs/                    # build")


def cmd_install_skills(target: str):
    """Install SpecSoloist agent skills to a target directory."""
    import shutil

    skills_src = _find_skills_dir()
    if not skills_src:
        ui.print_error("Skills directory not found. Ensure specsoloist is properly installed.")
        sys.exit(1)

    target_abs = os.path.abspath(target)
    os.makedirs(target_abs, exist_ok=True)

    _pkg_version = importlib.metadata.version("specsoloist")
    version_marker = f"<!-- sp-version: {_pkg_version} -->\n"

    installed = []
    for entry in os.listdir(skills_src):
        src = os.path.join(skills_src, entry)
        dst = os.path.join(target_abs, entry)
        if os.path.isdir(src) and os.path.exists(os.path.join(src, "SKILL.md")):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            # Prepend version marker to installed SKILL.md
            skill_dst = os.path.join(dst, "SKILL.md")
            with open(skill_dst) as f:
                original = f.read()
            with open(skill_dst, "w") as f:
                f.write(version_marker + original)
            installed.append(entry)
            ui.print_success(f"Installed: [bold]{entry}[/]")

    if not installed:
        ui.print_warning("No skills found to install.")
        return

    ui.print_success(f"Installed {len(installed)} skills to: [bold]{target_abs}[/]")
    ui.print_info("Skills are now available in your agent's skills directory.")


def _find_skills_dir() -> str | None:
    """Find the bundled skills directory."""
    # Try importlib.resources (works for both installed and editable installs)
    try:
        import importlib.resources as pkg_resources
        skills_ref = pkg_resources.files('specsoloist').joinpath('skills')
        skills_path = str(skills_ref)
        if os.path.isdir(skills_path):
            return skills_path
    except Exception:
        pass

    # Fallback: relative to this file (development installs without importlib support)
    candidates = [
        os.path.join(os.path.dirname(__file__), 'skills'),           # src/specsoloist/skills/
        os.path.join(os.path.dirname(__file__), '..', '..', 'skills'),  # repo root skills/
    ]
    for candidate in candidates:
        abs_path = os.path.abspath(candidate)
        if os.path.isdir(abs_path):
            return abs_path

    return None


def _detect_agent_cli() -> str | None:
    """Detect which agent CLI is available (claude preferred over gemini)."""
    import shutil
    
    # Check for override
    override = os.environ.get("SPECSOLOIST_AGENT")
    if override in ["claude", "gemini"]:
        if shutil.which(override):
            return override
        ui.print_warning(f"Requested agent '{override}' not found on PATH. Falling back to detection.")

    if shutil.which("claude"):
        return "claude"
    if shutil.which("gemini"):
        return "gemini"
    return None


def _detect_nested_session(agent: str) -> bool:
    """Return True if we appear to be running inside an active agent session.

    Claude Code sets CLAUDECODE and CLAUDE_CODE_ENTRYPOINT in its terminal environment.
    Gemini CLI does not currently set a reliable indicator; fall back to parent process check.
    """
    if agent == "claude":
        # Reliable: Claude Code sets CLAUDECODE in its spawned terminals
        if "CLAUDECODE" in os.environ or "CLAUDE_CODE_ENTRYPOINT" in os.environ:
            return True
    elif agent == "gemini":
        if "GEMINI_CLI_SESSION" in os.environ or "GEMINI_TERMINAL" in os.environ:
            return True

    # Optional: check parent process name (requires psutil, gracefully degraded)
    try:
        import psutil
        parent = psutil.Process().parent()
        if parent and agent in (parent.name() or "").lower():
            return True
    except Exception:
        pass

    return False


def _warn_nested_session(agent: str) -> None:
    """Print a friendly warning when running inside an active agent session."""
    from rich.panel import Panel
    from rich.text import Text

    msg = Text()
    msg.append("You appear to be running inside ")
    msg.append(agent.capitalize() + " Code", style="bold")
    msg.append(".\n\n")
    msg.append(f"sp conduct spawns a {agent} subprocess, which may be blocked\n")
    msg.append("inside an active session.\n\n")
    msg.append("Options:\n", style="bold")
    msg.append("  1. Open a separate terminal outside ")
    msg.append(agent.capitalize() + " Code\n", style="bold")
    msg.append("  2. Use ")
    msg.append("--no-agent", style="bold cyan")
    msg.append(" to compile without an agent\n")
    msg.append("  3. If you are Claude Code: use the ")
    msg.append("Agent tool", style="bold cyan")
    msg.append(" to spawn\n     the conductor agent directly (no subprocess needed)")

    panel = Panel(msg, title="[yellow]Heads Up[/yellow]", border_style="yellow", padding=(0, 1))
    ui.console.print(panel)


def _run_agent_oneshot(agent: str, prompt: str, auto_accept: bool, model: str | None = None):
    """Run an agent CLI in one-shot mode."""
    import subprocess

    # Warn if running inside an active agent session
    if _detect_nested_session(agent):
        _warn_nested_session(agent)

    if agent == "claude":
        # Claude Code: claude -p "prompt" --verbose for progress visibility
        cmd = ["claude", "-p", prompt, "--verbose"]
        if model:
            cmd.extend(["--model", model])
        if auto_accept:
            cmd.append("--dangerously-skip-permissions")
        result = subprocess.run(cmd, capture_output=False, text=True)
    elif agent == "gemini":
        # Gemini CLI: gemini -p "prompt"
        cmd = ["gemini", "-p", prompt]
        if model:
            cmd.extend(["--model", model])
        if auto_accept:
            cmd.append("-y")
        result = subprocess.run(cmd, capture_output=False, text=True)
    else:
        raise ValueError(f"Unknown agent: {agent}")

    if result.returncode != 0:
        # Give a friendly message if we detected a nested session
        if _detect_nested_session(agent):
            raise RuntimeError(
                f"The conductor agent failed to start.\n"
                f"  This often happens when running sp conduct inside {agent.capitalize()} Code.\n"
                f"  Try running from a separate terminal, or use --no-agent."
            )
        raise RuntimeError(f"Agent exited with code {result.returncode}")


def _load_arrangement(path: str):
    """Load and parse an Arrangement from a YAML file."""
    try:
        with open(path) as f:
            content = f.read()
        from .parser import SpecParser
        parser = SpecParser(os.getcwd())
        return parser.parse_arrangement(content)
    except FileNotFoundError:
        ui.print_error(f"Arrangement file not found: {path}")
        sys.exit(1)
    except Exception as e:
        ui.print_error(f"Failed to load arrangement: {e}")
        sys.exit(1)


def _discover_arrangement(core):
    """Auto-discover arrangement.yaml in the current working directory."""
    path = os.path.join(os.getcwd(), "arrangement.yaml")
    if os.path.exists(path):
        from .parser import SpecParser
        parser = SpecParser(os.getcwd())
        try:
            with open(path) as f:
                content = f.read()
            return parser.parse_arrangement(content)
        except Exception as e:
            ui.print_warning(f"Could not parse arrangement.yaml: {e}")
            return None
    return None


def _apply_arrangement(core, arrangement):
    """Apply arrangement settings to core (e.g. setup_commands)."""
    if arrangement and arrangement.environment.setup_commands:
        core.runner.setup_commands = arrangement.environment.setup_commands


def _resolve_arrangement(core, arrangement_arg):
    """Resolve arrangement: explicit file > auto-discovered > None."""
    if arrangement_arg:
        arr = _load_arrangement(arrangement_arg)
        ui.print_info(f"Using arrangement: [bold]{arrangement_arg}[/]")
    else:
        arr = _discover_arrangement(core)
        if arr:
            ui.print_info("Using auto-discovered [bold]arrangement.yaml[/]")
    for warning in _check_arrangement_dependencies(arr):
        ui.console.print(f"[warning]⚠[/] {warning}")
    return arr


def _resolve_model(cli_model: str | None, arrangement) -> str | None:
    """Resolve the LLM model to use, applying CLI > arrangement > env var precedence.

      1. --model CLI flag  (cli_model)
      2. model field in arrangement
      3. SPECSOLOIST_LLM_MODEL env var  (handled by providers / config layer)
      4. Provider default

    Returns the model string or None (which lets the provider use its default).
    """
    if cli_model:
        return cli_model
    if arrangement and getattr(arrangement, "model", None):
        return arrangement.model
    return None


def _check_api_key():
    """Check that an API key is configured."""
    provider = os.environ.get("SPECSOLOIST_LLM_PROVIDER", "gemini")
    _KEY_REQS = {
        "gemini": ("GEMINI_API_KEY", "export GEMINI_API_KEY='your-key-here'"),
        "google": ("GEMINI_API_KEY", "export GEMINI_API_KEY='your-key-here'"),
        "anthropic": ("ANTHROPIC_API_KEY", "export ANTHROPIC_API_KEY='your-key-here'"),
        "openai": ("OPENAI_API_KEY", "export OPENAI_API_KEY='your-key-here'"),
        "openrouter": ("OPENROUTER_API_KEY", "export OPENROUTER_API_KEY='your-key-here'"),
        # ollama: no key needed
    }
    if provider in _KEY_REQS:
        key_name, hint = _KEY_REQS[provider]
        if key_name not in os.environ:
            ui.print_error(f"{key_name} not set")
            ui.print_info(f"Run: {hint}")
            sys.exit(1)


# ---------------------------------------------------------------------------
# sp help helpers
# ---------------------------------------------------------------------------

_HELP_TOPICS = {
    "arrangement": "Full arrangement.yaml reference (all fields, examples)",
    "spec-format": "Spec file format (.spec.md structure, types, blocks)",
    "conduct": "Running sp conduct: arguments, arrangement, agent mode",
    "overrides": "Per-spec output path overrides (output_paths.overrides)",
    "specs-path": "Configuring the spec discovery directory (specs_path)",
}


def _read_help_file(topic: str) -> str | None:
    """Return the content of a bundled help file, or None if not found."""
    import importlib.resources as pkg_resources
    try:
        ref = pkg_resources.files("specsoloist.help").joinpath(f"{topic}.md")
        return ref.read_text(encoding="utf-8")
    except (FileNotFoundError, TypeError, ModuleNotFoundError):
        return None


def cmd_help(topic: str | None = None) -> None:
    """Print a reference guide for a specific topic."""
    if topic is None:
        ui.console.print("\n[bold]Available help topics:[/]\n")
        for name, desc in _HELP_TOPICS.items():
            ui.console.print(f"  [bold]{name:<14}[/]  {desc}")
        ui.console.print("\nRun: [bold]sp help <topic>[/]\n")
        return

    content = _read_help_file(topic)
    if content is None:
        valid = ", ".join(_HELP_TOPICS.keys())
        ui.print_error(f"Unknown topic '{topic}'. Available topics: {valid}")
        sys.exit(1)

    print(content)


# ---------------------------------------------------------------------------
# sp schema helpers
# ---------------------------------------------------------------------------

def _classify_annotation(annotation) -> tuple[str, type | None, bool]:
    """Return (type_str, sub_model_class_or_None, is_dict_of_model).

    Handles Optional[X], List[X], Dict[K, V], BaseModel subclasses, and primitives.
    """
    import typing
    from pydantic import BaseModel as _BaseModel

    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    # Optional[X] == Union[X, None]
    if origin is typing.Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _classify_annotation(non_none[0])
        return str(annotation), None, False

    # List[X]
    if origin is list:
        inner = args[0].__name__ if args and hasattr(args[0], "__name__") else "Any"
        return f"list[{inner}]", None, False

    # Dict[K, V]
    if origin is dict:
        v = args[1] if len(args) > 1 else None
        if v and isinstance(v, type) and issubclass(v, _BaseModel):
            return f"dict[str, {v.__name__}]", v, True
        k_name = args[0].__name__ if args and hasattr(args[0], "__name__") else "str"
        v_name = args[1].__name__ if len(args) > 1 and hasattr(args[1], "__name__") else "Any"
        return f"dict[{k_name}, {v_name}]", None, False

    # BaseModel subclass
    if isinstance(annotation, type):
        from pydantic import BaseModel as _BM
        if issubclass(annotation, _BM):
            return annotation.__name__, annotation, False

    # Primitive
    if hasattr(annotation, "__name__"):
        return annotation.__name__, None, False

    return str(annotation), None, False


def _repr_default(val) -> str:
    """Return a compact string for a field default value."""
    if isinstance(val, str):
        return f'"{val}"'
    if val in ({}, []):
        return repr(val)
    return repr(val)


def _format_schema_text(model: type, indent: int = 0) -> str:
    """Render a Pydantic model as an annotated text schema (recursive)."""
    lines = []
    pad = "  " * indent

    for name, field_info in model.model_fields.items():
        type_str, sub_model, is_dict_of_model = _classify_annotation(field_info.annotation)

        # Qualifier: required / optional / default value
        if field_info.is_required():
            qualifier = "(required)"
        elif field_info.default is None:
            qualifier = "(optional)"
        elif field_info.default_factory is not None:
            try:
                qualifier = f"[default: {_repr_default(field_info.default_factory())}]"
            except Exception:
                qualifier = ""
        else:
            qualifier = f"[default: {_repr_default(field_info.default)}]"

        desc = field_info.description or ""

        if sub_model and not is_dict_of_model:
            # Nested model — recurse; suppress verbose default repr (fields show their own defaults)
            nested_qualifier = "(required)" if field_info.is_required() else "(optional)"
            qualifier = nested_qualifier
            lines.append(f"{pad}{name}:  {qualifier}")
            if desc:
                lines.append(f"{pad}  {desc}")
            lines.append(_format_schema_text(sub_model, indent + 1))
        elif sub_model and is_dict_of_model:
            # Dict[str, SomeModel] — show with <key>: placeholder
            lines.append(f"{pad}{name}:  {qualifier}")
            if desc:
                lines.append(f"{pad}  {desc}")
            lines.append(f"{pad}  <key>:")
            lines.append(_format_schema_text(sub_model, indent + 2))
        else:
            lines.append(f"{pad}{name}: {type_str}  {qualifier}")
            if desc:
                lines.append(f"{pad}  {desc}")
        lines.append("")

    return "\n".join(lines)


def cmd_schema(topic: str | None = None, json_output: bool = False) -> None:
    """Print the annotated arrangement.yaml schema, optionally filtered to a topic."""
    import json as _json
    from specsoloist.schema import Arrangement

    if json_output:
        if topic:
            # Zoom into a sub-model's JSON schema
            field = Arrangement.model_fields.get(topic)
            if field is None:
                valid = ", ".join(Arrangement.model_fields.keys())
                ui.print_error(f"Unknown topic '{topic}'. Valid topics: {valid}")
                sys.exit(1)
            _, sub_model, _ = _classify_annotation(field.annotation)
            schema = sub_model.model_json_schema() if sub_model else {}
        else:
            schema = Arrangement.model_json_schema()
        print(_json.dumps(schema, indent=2))
        return

    # Annotated text format
    version = importlib.metadata.version("specsoloist")
    if topic:
        field = Arrangement.model_fields.get(topic)
        if field is None:
            valid = ", ".join(Arrangement.model_fields.keys())
            ui.print_error(f"Unknown topic '{topic}'. Valid topics: {valid}")
            sys.exit(1)
        _, sub_model, is_dict = _classify_annotation(field.annotation)
        header = f"arrangement.yaml → {topic}  (specsoloist {version})"
        ui.console.print(f"\n[bold]{header}[/]\n")
        if sub_model:
            print(_format_schema_text(sub_model))
        else:
            type_str, _, _ = _classify_annotation(field.annotation)
            desc = field.description or ""
            print(f"{topic}: {type_str}")
            if desc:
                print(f"  {desc}")
    else:
        header = f"arrangement.yaml schema  (specsoloist {version})"
        ui.console.print(f"\n[bold]{header}[/]\n")
        print(_format_schema_text(Arrangement))


if __name__ == "__main__":
    main()