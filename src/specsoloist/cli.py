"""
Command-line interface for SpecSoloist.

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
import sys
import os

from .core import SpecSoloistCore
from .resolver import CircularDependencyError, MissingDependencyError
from spechestra.composer import SpecComposer, Architecture
from spechestra.conductor import SpecConductor
from .respec import Respecer
from . import ui


def main():
    parser = argparse.ArgumentParser(
        prog="sp",
        description="Spec-as-Source AI coding framework"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list
    subparsers.add_parser("list", help="List all specification files")

    # create
    create_parser = subparsers.add_parser("create", help="Create a new spec from template")
    create_parser.add_argument("name", help="Spec name (e.g., 'auth' creates auth.spec.md)")
    create_parser.add_argument("description", help="Brief description of the component")
    create_parser.add_argument("--type", default="function", help="Type: function, class, module, typedef")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate a spec's structure")
    validate_parser.add_argument("name", help="Spec name to validate")
    validate_parser.add_argument("--arrangement", metavar="FILE", help="Path to arrangement YAML file")

    # verify
    subparsers.add_parser("verify", help="Verify all specs for orchestration readiness")

    # graph
    subparsers.add_parser("graph", help="Export dependency graph as Mermaid")

    # compile
    compile_parser = subparsers.add_parser("compile", help="Compile a spec to code")
    compile_parser.add_argument("name", help="Spec name to compile")
    compile_parser.add_argument("--model", help="Override LLM model")
    compile_parser.add_argument("--no-tests", action="store_true", help="Skip test generation")
    compile_parser.add_argument("--arrangement", metavar="FILE", help="Path to arrangement YAML file")

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

    # diff
    diff_parser = subparsers.add_parser(
        "diff",
        help="Compare two build output directories semantically"
    )
    diff_parser.add_argument("left", help="Left directory (e.g. src/ or build/run1/)")
    diff_parser.add_argument("right", help="Right directory (e.g. build/quine/src/ or build/run2/)")
    diff_parser.add_argument(
        "--label-left", default=None, metavar="LABEL",
        help="Human-readable label for the left directory (default: directory name)"
    )
    diff_parser.add_argument(
        "--label-right", default=None, metavar="LABEL",
        help="Human-readable label for the right directory (default: directory name)"
    )
    diff_parser.add_argument(
        "--report", default="build/diff-report.json", metavar="PATH",
        help="Path to write the JSON diff report (default: build/diff-report.json)"
    )
    diff_parser.add_argument(
        "--runs", type=int, default=None, metavar="N",
        help="Compare the last N build runs recorded in build/runs/ (overrides left/right)"
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

    # doctor
    subparsers.add_parser("doctor", help="Check environment health (API keys, CLIs, tools)")

    # status
    subparsers.add_parser("status", help="Show compilation state of each spec")

    args = parser.parse_args()

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
    if args.command == "doctor":
        cmd_doctor()
        return

    # Initialize core
    try:
        core = SpecSoloistCore(os.getcwd())
    except Exception as e:
        ui.print_error(f"Failed to initialize SpecSoloist: {e}")
        sys.exit(1)

    try:
        if args.command == "list":
            cmd_list(core)
        elif args.command == "create":
            cmd_create(core, args.name, args.description, args.type)
        elif args.command == "validate":
            cmd_validate(core, args.name, getattr(args, "arrangement", None))
        elif args.command == "verify":
            cmd_verify(core)
        elif args.command == "graph":
            cmd_graph(core)
        elif args.command == "compile":
            cmd_compile(core, args.name, args.model, not args.no_tests, args.arrangement)
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
            cmd_build(core, args.incremental, args.parallel, args.workers, args.model, not args.no_tests, args.arrangement)
        elif args.command == "compose":
            cmd_compose(core, args.request, args.no_agent, args.auto_accept, args.model)
        elif args.command == "conduct":
            cmd_conduct(core, args.src_dir, args.no_agent, args.auto_accept,
                        args.incremental, args.parallel, args.workers, args.model, args.arrangement)
        elif args.command == "diff":
            cmd_diff(core, args.left, args.right, args.label_left, args.label_right,
                     args.report, args.runs)
        elif args.command == "respec":
            cmd_respec(core, args.file, args.test, args.out, args.no_agent, args.model, args.auto_accept)
        elif args.command == "status":
            cmd_status(core)
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


def cmd_list(core: SpecSoloistCore):
    specs = core.list_specs()
    if not specs:
        ui.print_warning("No specs found in src/")
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
    if "## Test Scenarios" not in spec_content:
        warnings.append("No test scenarios found — soloists compile better with concrete examples")

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


def cmd_validate(core: SpecSoloistCore, name: str, arrangement_arg: str | None = None):
    ui.print_header("Validating Spec", name)
    result = core.validate_spec(name)

    if result["valid"]:
        ui.print_success(f"{name} is VALID")
        # Emit quality hints
        try:
            spec_content = core.read_spec(name)
            parsed = core.parser.parse_spec(name)
            spec_type = parsed.metadata.type
        except Exception:
            spec_content = ""
            spec_type = "bundle"
            parsed = None

        if spec_type == "reference":
            ui.print_info("type: reference — context only, no implementation will be generated")
            # For reference specs, show reference-specific warnings (not standard quality warnings)
            if parsed is not None:
                for warning in core.parser.get_reference_warnings(parsed):
                    ui.console.print(f"[warning]⚠[/] {warning}")
        else:
            for warning in _check_spec_quality(spec_content, spec_type):
                ui.console.print(f"[warning]⚠[/] {warning}")

    else:
        ui.print_error(f"{name} is INVALID")
        for error in result["errors"]:
            ui.print_step(f"[red]{error}[/]")
        sys.exit(1)


def cmd_verify(core: SpecSoloistCore):
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


def cmd_graph(core: SpecSoloistCore):
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
                arrangement_arg: str | None = None):
    _check_api_key()

    ui.print_header("Compiling Spec", name)

    arrangement = _resolve_arrangement(core, arrangement_arg)
    _apply_arrangement(core, arrangement)

    # Validate first
    validation = core.validate_spec(name)
    if not validation["valid"]:
        ui.print_error("Invalid spec")
        for error in validation["errors"]:
            ui.print_step(f"[red]{error}[/]")
        sys.exit(1)

    try:
        # Compile code
        with ui.spinner(f"Compiling [bold]{name}[/] implementation..."):
            result = core.compile_spec(name, model=model, arrangement=arrangement)
        ui.print_success(result)

        # Generate tests
        if generate_tests:
            spec = core.parser.parse_spec(name)
            if spec.metadata.type != "typedef":
                with ui.spinner(f"Generating tests for [bold]{name}[/]..."):
                    result = core.compile_tests(name, model=model, arrangement=arrangement)
                ui.print_success(result)
            else:
                ui.print_info("Skipping tests for typedef spec")

    except Exception as e:
        ui.print_error(str(e))
        sys.exit(1)


def cmd_test(core: SpecSoloistCore, name: str):
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


def cmd_build(core: SpecSoloistCore, incremental: bool, parallel: bool, workers: int, model: str,
              generate_tests: bool, arrangement_arg: str | None = None):
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


def cmd_conduct(core: SpecSoloistCore, src_dir: str | None, no_agent: bool, auto_accept: bool,
                 incremental: bool, parallel: bool, workers: int, model: str | None = None,
                 arrangement_arg: str | None = None):
    """Orchestrate project build."""

    ui.print_header("Conducting Build", src_dir or "project specs")

    if no_agent:
        arrangement = _resolve_arrangement(core, arrangement_arg)
        _conduct_with_llm(core, src_dir, incremental, parallel, workers, arrangement=arrangement)
    else:
        _conduct_with_agent(src_dir, auto_accept, model=model, arrangement_arg=arrangement_arg)


def _conduct_with_agent(src_dir: str | None, auto_accept: bool, model: str | None = None,
                        arrangement_arg: str | None = None):
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
                      arrangement=None):
    """Direct LLM build (single-shot compilation, no agent iteration)."""
    _check_api_key()

    ui.print_info("Using direct LLM calls (no agent)...")

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

    with ui.spinner("Orchestrating build..."):
        result = conductor.build(
            incremental=incremental,
            parallel=parallel,
            max_workers=workers,
            arrangement=arrangement,
        )

    table = ui.create_table(["Result", "Spec", "Details"], title="Conductor Report")

    for spec in result.specs_compiled:
        table.add_row("[green]Compiled[/]", spec, "Success")

    for spec in result.specs_skipped:
        table.add_row("[dim]Skipped[/]", spec, "Unchanged")

    for spec in result.specs_failed:
        error = result.errors.get(spec, "Unknown error")
        if len(error) > 50:
            error = error[:47] + "..."
        table.add_row("[red]Failed[/]", spec, error)

    ui.console.print(table)

    if result.success:
        ui.print_success("Conductor finished successfully.")
    else:
        ui.print_error("Conductor reported failures.")
        sys.exit(1)


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


def cmd_doctor():
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

    # API keys
    has_anthropic = "ANTHROPIC_API_KEY" in os.environ
    has_gemini = "GEMINI_API_KEY" in os.environ

    if has_anthropic:
        ui.console.print("[success]✓[/] ANTHROPIC_API_KEY set")
    else:
        ui.console.print("[warning]~[/] ANTHROPIC_API_KEY not set")

    if has_gemini:
        ui.console.print("[success]✓[/] GEMINI_API_KEY set")
    else:
        ui.console.print("[warning]~[/] GEMINI_API_KEY not set")

    if not has_anthropic and not has_gemini:
        ui.console.print("[error]✗[/] No API key set — at least one of ANTHROPIC_API_KEY or GEMINI_API_KEY is required")
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

    ui.console.print()
    if critical_failure:
        ui.print_error("One or more critical checks failed.")
        sys.exit(1)
    else:
        ui.print_success("All critical checks passed.")


def cmd_status(core: SpecSoloistCore):
    """Show compilation state of each spec from the build manifest."""
    from datetime import datetime, timezone

    manifest = core._get_manifest()
    specs = core.list_specs()

    if not specs:
        ui.print_warning("No specs found.")
        ui.print_info("Create one with: sp create <name> '<description>'")
        return

    table = ui.create_table(["Spec", "Compiled", "Tests", "Last Built"], title="Spec Status")

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

    for spec_file in specs:
        name = spec_file.replace(".spec.md", "")

        # Reference specs: show CONTEXT instead of compilation status
        try:
            parsed = core.parser.parse_spec(name)
            if parsed.metadata.type == "reference":
                table.add_row(name, "[blue]CONTEXT[/]", "[dim]—[/]", "[dim]—[/]")
                continue
        except Exception:
            pass

        info = manifest.get_spec_info(name)

        if info is None:
            table.add_row(name, "[red]✗[/]", "[red]✗[/]", "never")
            continue

        # Check implementation file on disk
        impl_exists = any(
            os.path.exists(f) for f in info.output_files
            if not os.path.basename(f).startswith("test_")
        )
        compiled_cell = "[green]✓[/]" if impl_exists else "[red]✗[/]"

        # Check test file on disk
        test_files = [f for f in info.output_files if os.path.basename(f).startswith("test_")]
        if test_files and os.path.exists(test_files[0]):
            tests_cell = "[green]✓[/]"
        elif test_files:
            tests_cell = "[red]FAIL[/]"
        else:
            tests_cell = "[red]✗[/]"

        last_built = _rel_time(info.built_at)
        table.add_row(name, compiled_cell, tests_cell, last_built)

    ui.console.print(table)


_INIT_ARRANGEMENT = """\
# arrangement.yaml
#
# Bridges your specs to a concrete build environment.
# Run: sp conduct specs/ --arrangement arrangement.yaml
#
# See: https://github.com/symbolfarm/specsoloist

target_language: python

output_paths:
  implementation: src/{name}.py
  tests: tests/test_{name}.py

environment:
  tools:
    - uv
    - ruff
    - pytest
  setup_commands:
    - uv sync

build_commands:
  compile: ""               # Leave empty for interpreted languages
  lint: uv run ruff check .
  test: uv run pytest

constraints:
  - Must pass ruff with 0 errors
  - Must use type hints for all public function signatures
"""

_INIT_ARRANGEMENT_TYPESCRIPT = """\
# arrangement.yaml (TypeScript)
#
# Bridges your specs to a TypeScript/Node.js build environment.
# Run: sp conduct specs/ --arrangement arrangement.yaml
#
# See: https://github.com/symbolfarm/specsoloist

target_language: typescript

output_paths:
  implementation: src/{name}.ts
  tests: tests/{name}.test.ts

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

    installed = []
    for entry in os.listdir(skills_src):
        src = os.path.join(skills_src, entry)
        dst = os.path.join(target_abs, entry)
        if os.path.isdir(src) and os.path.exists(os.path.join(src, "SKILL.md")):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
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


def _run_agent_oneshot(agent: str, prompt: str, auto_accept: bool, model: str | None = None):
    """Run an agent CLI in one-shot mode."""
    import subprocess

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


def _check_api_key():
    """Check that an API key is configured."""
    provider = os.environ.get("SPECSOLOIST_LLM_PROVIDER", "gemini")
    if provider == "gemini" and "GEMINI_API_KEY" not in os.environ:
        ui.print_error("GEMINI_API_KEY not set")
        ui.print_info("Run: export GEMINI_API_KEY='your-key-here'")
        sys.exit(1)
    elif provider == "anthropic" and "ANTHROPIC_API_KEY" not in os.environ:
        ui.print_error("ANTHROPIC_API_KEY not set")
        ui.print_info("Run: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)


if __name__ == "__main__":
    main()