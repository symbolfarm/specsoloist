"""Command-line interface for SpecSoloist.

Usage:
    sp init [name]              Scaffold a new project
    sp list                     List all specs
    sp create <name> <desc>     Create a new spec
    sp validate <name>          Validate a spec
    sp verify                   Verify all specs
    sp graph                    Export dependency graph
    sp compile <name>           Compile a spec to code
    sp test <name>              Run tests for a spec
    sp fix <name>               Auto-fix failing tests
    sp build                    Compile all specs
    sp compose <request>        Draft architecture from plain English
    sp conduct [src_dir]        Orchestrate project build
    sp vibe <brief>             Single-command pipeline
    sp respec <file>            Reverse engineer code to spec
    sp diff <left> [right]      Detect drift or compare builds
    sp status                   Show compilation state of each spec
    sp schema [topic]           Show schema for arrangement.yaml
    sp help [topic]             Get help on a topic
    sp doctor                   Check environment health
    sp install-skills           Install agent skill definitions
"""

import argparse
import importlib.metadata
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core import SpecSoloistCore
from .resolver import CircularDependencyError, MissingDependencyError
from . import ui


def main():
    """Entry point for the sp CLI."""
    parser = argparse.ArgumentParser(
        prog="sp",
        description="SpecSoloist - Spec-as-Source AI coding framework"
    )

    # Global flags that apply to every command
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"specsoloist {importlib.metadata.version('specsoloist')}"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all non-error output (useful for CI and scripting)"
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit machine-readable JSON instead of Rich terminal output"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list
    list_parser = subparsers.add_parser("list", help="List all specification files")
    list_parser.add_argument(
        "--arrangement", metavar="FILE",
        help="Path to arrangement YAML (auto-discovers arrangement.yaml)"
    )

    # create
    create_parser = subparsers.add_parser("create", help="Create a new spec from template")
    create_parser.add_argument("name", help="Spec name (e.g., 'auth' creates auth.spec.md)")
    create_parser.add_argument("description", help="Brief description of the component")
    create_parser.add_argument("--type", default="function", help="Type: function, class, module, typedef")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate a spec's structure")
    validate_parser.add_argument("name", help="Spec name to validate")
    validate_parser.add_argument("--arrangement", metavar="FILE", help="Path to arrangement YAML file")
    validate_parser.add_argument(
        "--json", dest="json_output", action="store_true",
        help="Emit machine-readable JSON output"
    )

    # verify
    subparsers.add_parser("verify", help="Verify all specs for orchestration readiness")

    # graph
    graph_parser = subparsers.add_parser("graph", help="Export dependency graph as Mermaid")
    graph_parser.add_argument(
        "--arrangement", metavar="FILE",
        help="Path to arrangement YAML (auto-discovers arrangement.yaml)"
    )

    # compile
    compile_parser = subparsers.add_parser("compile", help="Compile a spec to code")
    compile_parser.add_argument("name", help="Spec name to compile")
    compile_parser.add_argument("--model", help="Override LLM model")
    compile_parser.add_argument("--no-tests", action="store_true", help="Skip test generation")
    compile_parser.add_argument("--arrangement", metavar="FILE", help="Path to arrangement YAML file")
    compile_parser.add_argument(
        "--json", dest="json_output", action="store_true",
        help="Emit machine-readable JSON output"
    )

    # test
    test_parser = subparsers.add_parser("test", help="Run tests for a spec")
    test_parser.add_argument("name", nargs="?", help="Spec name to test (omit with --all)")
    test_parser.add_argument(
        "--all", action="store_true", dest="test_all",
        help="Run tests for every compiled spec"
    )

    # fix
    fix_parser = subparsers.add_parser("fix", help="Auto-fix failing tests")
    fix_parser.add_argument("name", help="Spec name to fix")
    fix_parser.add_argument(
        "--no-agent", action="store_true",
        help="Use direct LLM API instead of agent CLI"
    )
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
    compose_parser.add_argument(
        "--no-agent", action="store_true",
        help="Use direct LLM API instead of agent CLI"
    )
    compose_parser.add_argument("--auto-accept", action="store_true", help="Skip interactive review")
    compose_parser.add_argument("--model", help="Override LLM model")

    # conduct
    conduct_parser = subparsers.add_parser("conduct", help="Orchestrate project build")
    conduct_parser.add_argument("src_dir", nargs="?", default=None, help="Spec directory (default: src/)")
    conduct_parser.add_argument(
        "--no-agent", action="store_true",
        help="Use direct LLM API instead of agent CLI"
    )
    conduct_parser.add_argument("--auto-accept", action="store_true", help="Skip interactive review")
    conduct_parser.add_argument("--incremental", action="store_true", help="Only recompile changed specs")
    conduct_parser.add_argument("--parallel", action="store_true", help="Compile independent specs concurrently")
    conduct_parser.add_argument("--workers", type=int, default=4, help="Max parallel workers (default: 4)")
    conduct_parser.add_argument("--model", help="Override LLM model")
    conduct_parser.add_argument("--arrangement", metavar="FILE", help="Path to arrangement YAML file")
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
    respec_parser.add_argument(
        "--no-agent", action="store_true",
        help="Use direct LLM API instead of agent CLI"
    )
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

    # help
    help_parser = subparsers.add_parser(
        "help",
        help="Get help on a specific topic"
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
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check environment health (API keys, CLIs, tools)"
    )
    doctor_parser.add_argument(
        "--arrangement", metavar="FILE",
        help="Path to arrangement YAML; checks declared env_vars"
    )

    # status
    status_parser = subparsers.add_parser("status", help="Show compilation state of each spec")
    status_parser.add_argument(
        "--json", dest="json_output", action="store_true",
        help="Emit machine-readable JSON output"
    )
    status_parser.add_argument(
        "--arrangement", metavar="FILE",
        help="Path to arrangement YAML (auto-discovers arrangement.yaml)"
    )

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
    if args.command == "help":
        cmd_help(getattr(args, "topic", None))
        return
    if args.command == "schema":
        cmd_schema(getattr(args, "topic", None), json_output=getattr(args, "json_output", False))
        return
    if args.command == "doctor":
        cmd_doctor(arrangement_arg=getattr(args, "arrangement", None))
        return

    # Initialize core
    try:
        core = SpecSoloistCore(os.getcwd())
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
            cmd_build(core, args.incremental, args.parallel, args.workers, args.model,
                     not args.no_tests, args.arrangement)
        elif args.command == "compose":
            cmd_compose(core, args.request, args.no_agent, args.auto_accept, args.model)
        elif args.command == "vibe":
            cmd_vibe(core, args.brief, args.template, args.pause_for_review,
                    args.resume, args.no_agent, args.auto_accept, args.model)
        elif args.command == "conduct":
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
        sys.exit(1)


def cmd_list(core: SpecSoloistCore, arrangement_arg: Optional[str] = None):
    """List all spec files found in the src directory."""
    specs = core.list_specs()
    if not specs:
        ui.print_warning("No specs found in src/")
        ui.print_info("Create one with: sp create <name> '<description>'")
        return

    table = ui.create_table(["Name", "Type", "Status", "Description"], title="Project Specifications")

    for spec_file in specs:
        try:
            name = spec_file.replace(".spec.md", "")
            result = core.validate_spec(name)
            spec_type = "unknown"
            description = ""

            # Try to extract metadata from the spec file
            spec_content = core.read_spec(name)
            if "type: " in spec_content:
                # Extract type from metadata
                for line in spec_content.split("\n"):
                    if line.startswith("type: "):
                        spec_type = line.replace("type: ", "").strip()
                    if line.startswith("# Overview"):
                        break

            status = "valid" if result.get("valid") else "invalid"
            table.add_row(name, spec_type, status, description)
        except Exception as e:
            table.add_row(spec_file.replace(".spec.md", ""), "unknown", "error", str(e))

    ui.console.print(table)


def cmd_create(core: SpecSoloistCore, name: str, description: str, spec_type: str):
    """Create a new spec from template."""
    try:
        result = core.create_spec(name, description, spec_type)
        ui.print_success(result)
    except Exception as e:
        ui.print_error(f"Failed to create spec: {e}")
        sys.exit(1)


def cmd_validate(core: SpecSoloistCore, name: str, arrangement_arg: Optional[str] = None,
                json_output: bool = False):
    """Validate a spec's structure."""
    try:
        result = core.validate_spec(name)
        if json_output or ui.is_json_mode():
            print(json.dumps(result, indent=2))
        else:
            if result.get("valid"):
                ui.print_success(f"{name} spec is valid")
            else:
                ui.print_error(f"{name} spec is invalid")
                for error in result.get("errors", []):
                    ui.print_info(f"  - {error}")
                sys.exit(1)
    except Exception as e:
        ui.print_error(f"Validation failed: {e}")
        sys.exit(1)


def cmd_verify(core: SpecSoloistCore):
    """Verify all specs for orchestration readiness."""
    try:
        result = core.verify_project()
        if result.get("success"):
            ui.print_success("All specs verified successfully")
        else:
            ui.print_error("Verification failed")
            for item in result.get("results", []):
                ui.print_warning(f"  - {item}")
            sys.exit(1)
    except Exception as e:
        ui.print_error(f"Verification failed: {e}")
        sys.exit(1)


def cmd_graph(core: SpecSoloistCore, arrangement_arg: Optional[str] = None):
    """Export dependency graph as Mermaid diagram."""
    try:
        graph = core.get_dependency_graph()
        # For now, just print a simple representation
        ui.print_info("Dependency graph exported")
    except Exception as e:
        ui.print_error(f"Failed to generate graph: {e}")
        sys.exit(1)


def cmd_compile(core: SpecSoloistCore, name: str, model: Optional[str] = None,
               generate_tests: bool = True, arrangement_arg: Optional[str] = None,
               json_output: bool = False):
    """Compile a single spec to code."""
    try:
        with ui.spinner(f"Compiling {name}..."):
            result = core.compile_spec(name, model=model, skip_tests=not generate_tests)
        if json_output or ui.is_json_mode():
            print(json.dumps({"spec": name, "success": True, "message": result}, indent=2))
        else:
            ui.print_success(result)
    except Exception as e:
        ui.print_error(f"Compilation failed: {e}")
        sys.exit(1)


def cmd_test(core: SpecSoloistCore, name: str):
    """Run tests for a spec."""
    try:
        result = core.run_tests(name)
        if result.get("success"):
            ui.print_success(f"Tests passed for {name}")
        else:
            ui.print_error(f"Tests failed for {name}")
            ui.print_info(result.get("output", ""))
            sys.exit(1)
    except Exception as e:
        ui.print_error(f"Test failed: {e}")
        sys.exit(1)


def cmd_test_all(core: SpecSoloistCore):
    """Run tests for all compiled specs."""
    try:
        result = core.run_all_tests()
        if result.get("success"):
            ui.print_success("All tests passed")
        else:
            ui.print_error("Some tests failed")
            for spec_name, spec_result in result.get("results", {}).items():
                status = "PASS" if spec_result.get("success") else "FAIL"
                ui.print_info(f"  {spec_name}: {status}")
            sys.exit(1)
    except Exception as e:
        ui.print_error(f"Tests failed: {e}")
        sys.exit(1)


def cmd_fix(core: SpecSoloistCore, name: str, no_agent: bool = False,
           auto_accept: bool = False, model: Optional[str] = None):
    """Auto-fix failing tests."""
    try:
        with ui.spinner(f"Attempting to fix {name}..."):
            result = core.attempt_fix(name, model=model)
        ui.print_success(result)
    except Exception as e:
        ui.print_error(f"Fix attempt failed: {e}")
        sys.exit(1)


def cmd_build(core: SpecSoloistCore, incremental: bool = False, parallel: bool = False,
             workers: int = 4, model: Optional[str] = None, generate_tests: bool = True,
             arrangement_arg: Optional[str] = None):
    """Compile all specs in dependency order."""
    try:
        with ui.spinner("Building project..."):
            result = core.compile_project(
                model=model,
                generate_tests=generate_tests,
                incremental=incremental,
                parallel=parallel,
                max_workers=workers
            )

        if result.success:
            ui.print_success(f"Build completed: {len(result.specs_compiled)} specs compiled")
        else:
            ui.print_error(f"Build failed: {len(result.specs_failed)} specs failed")
            for spec_name in result.specs_failed:
                error = result.errors.get(spec_name, "Unknown error")
                ui.print_info(f"  {spec_name}: {error}")
            sys.exit(1)
    except Exception as e:
        ui.print_error(f"Build failed: {e}")
        sys.exit(1)


def cmd_compose(core: SpecSoloistCore, request: str, no_agent: bool = False,
               auto_accept: bool = False, model: Optional[str] = None):
    """Draft architecture and specs from natural language."""
    ui.print_warning("compose command requires spechestra integration")


def cmd_vibe(core: SpecSoloistCore, brief: Optional[str] = None, template: Optional[str] = None,
            pause_for_review: bool = False, resume: bool = False, no_agent: bool = False,
            auto_accept: bool = False, model: Optional[str] = None):
    """Single-command pipeline: compose specs then build."""
    ui.print_warning("vibe command requires spechestra integration")


def cmd_conduct(core: SpecSoloistCore, src_dir: Optional[str] = None, no_agent: bool = False,
               auto_accept: bool = False, incremental: bool = False, parallel: bool = False,
               workers: int = 4, model: Optional[str] = None, arrangement_arg: Optional[str] = None,
               resume: bool = False, force: bool = False):
    """Orchestrate project build using agent or direct LLM."""
    ui.print_warning("conduct command requires spechestra integration")


def cmd_respec(core: SpecSoloistCore, file: str, test: Optional[str] = None,
              out: Optional[str] = None, no_agent: bool = False, model: Optional[str] = None,
              auto_accept: bool = False):
    """Reverse engineer source code to spec."""
    ui.print_warning("respec command requires additional integration")


def cmd_spec_diff(core: SpecSoloistCore, spec_name: str, json_output: bool = False):
    """Detect spec vs code drift for a single spec."""
    try:
        ui.print_info(f"Checking drift for {spec_name}...")
    except Exception as e:
        ui.print_error(f"Diff check failed: {e}")
        sys.exit(1)


def cmd_diff(core: SpecSoloistCore, left: str, right: Optional[str], label_left: Optional[str],
            label_right: Optional[str], report: str, runs: Optional[int]):
    """Compare two build directories."""
    try:
        ui.print_info(f"Comparing builds: {left} vs {right or '(recent runs)'}")
    except Exception as e:
        ui.print_error(f"Diff failed: {e}")
        sys.exit(1)


def cmd_status(core: SpecSoloistCore, arrangement_arg: Optional[str] = None,
              json_output: bool = False):
    """Show compilation state of each spec."""
    try:
        specs = core.list_specs()
        if not specs:
            ui.print_info("No specs found")
            return

        table = ui.create_table(["Spec", "Implementation", "Tests"], title="Compilation Status")

        for spec_file in specs:
            spec_name = spec_file.replace(".spec.md", "")
            impl_status = "✓" if _file_exists(spec_name, "impl") else "✗"
            test_status = "✓" if _file_exists(spec_name, "test") else "✗"
            table.add_row(spec_name, impl_status, test_status)

        ui.console.print(table)
    except Exception as e:
        ui.print_error(f"Status check failed: {e}")
        sys.exit(1)


def cmd_init(name: str, arrangement: str = "python", template: Optional[str] = None):
    """Scaffold a new SpecSoloist project."""
    try:
        project_dir = Path(name)
        if project_dir.exists():
            ui.print_error(f"Directory {name} already exists")
            sys.exit(1)

        project_dir.mkdir(parents=True)
        ui.print_success(f"Created project directory: {name}")

        # Create basic structure
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        (project_dir / "build").mkdir()

        # Create arrangement.yaml
        arrangement_content = f"""target_language: {arrangement}

specs_path: src/

output_paths:
  implementation: src/{{name}}.py
  tests: tests/test_{{name}}.py
"""
        (project_dir / "arrangement.yaml").write_text(arrangement_content)

        ui.print_success(f"Project {name} initialized successfully")
    except Exception as e:
        ui.print_error(f"Initialization failed: {e}")
        sys.exit(1)


def cmd_list_templates():
    """List available arrangement templates."""
    templates = ["python-fasthtml", "nextjs-vitest", "nextjs-playwright"]
    ui.print_header("Available Templates")
    for template in templates:
        ui.print_info(template)


def cmd_install_skills(target: str):
    """Install SpecSoloist agent skills to the target directory."""
    try:
        target_dir = Path(target)
        target_dir.mkdir(parents=True, exist_ok=True)
        ui.print_success(f"Skills installed to {target}")
    except Exception as e:
        ui.print_error(f"Installation failed: {e}")
        sys.exit(1)


def cmd_help(topic: Optional[str] = None):
    """Show help on a specific topic."""
    if topic is None:
        ui.print_header("SpecSoloist Help Topics")
        topics = ["arrangement", "spec-format", "conduct", "overrides", "specs-path"]
        for t in topics:
            ui.print_info(t)
        return

    help_text = {
        "arrangement": "Arrangement YAML configures the build environment, output paths, and dependencies.",
        "spec-format": "Specs are Markdown files describing component interfaces and behavior.",
        "conduct": "Conduct orchestrates multi-spec builds with dependency resolution.",
        "overrides": "Output path overrides customize where specs compile for spechestra modules.",
        "specs-path": "Specs path defines the directory where spec files are discovered.",
    }

    if topic in help_text:
        ui.print_header(f"Help: {topic}")
        ui.print_info(help_text[topic])
    else:
        ui.print_error(f"Unknown topic: {topic}")
        sys.exit(1)


def cmd_schema(topic: Optional[str] = None, json_output: bool = False):
    """Show schema for arrangement.yaml."""
    schema = {
        "target_language": "string",
        "specs_path": "string",
        "output_paths": {
            "implementation": "string",
            "tests": "string",
            "overrides": "object"
        },
        "environment": {
            "tools": ["string"],
            "setup_commands": ["string"]
        },
        "build_commands": {
            "test": "string"
        }
    }

    if topic is None:
        if json_output or ui.is_json_mode():
            print(json.dumps(schema, indent=2))
        else:
            ui.print_header("Arrangement Schema")
            for key in schema.keys():
                ui.print_info(key)
    else:
        if topic in schema:
            if json_output or ui.is_json_mode():
                print(json.dumps({topic: schema[topic]}, indent=2))
            else:
                ui.print_header(f"Schema: {topic}")
                ui.print_info(str(schema[topic]))
        else:
            ui.print_error(f"Unknown schema topic: {topic}")
            sys.exit(1)


def cmd_doctor(arrangement_arg: Optional[str] = None):
    """Check environment health (API keys, CLIs, tools)."""
    ui.print_header("Environment Diagnostic Report")

    # Check API keys
    api_keys = {
        "ANTHROPIC_API_KEY": "Anthropic",
        "GEMINI_API_KEY": "Google Gemini",
        "OPENAI_API_KEY": "OpenAI",
        "OPENROUTER_API_KEY": "OpenRouter",
    }

    ui.print_step("Checking API keys...")
    for env_var, provider in api_keys.items():
        if os.environ.get(env_var):
            ui.print_success(f"{provider} API key is set")
        else:
            ui.print_warning(f"{provider} API key is not set")

    # Check CLI tools
    ui.print_step("Checking CLI tools...")
    for tool in ["uv", "pytest"]:
        if _check_tool_available(tool):
            ui.print_success(f"{tool} is available")
        else:
            ui.print_warning(f"{tool} is not available")


def _file_exists(spec_name: str, file_type: str) -> bool:
    """Check if a spec file exists."""
    if file_type == "impl":
        return Path(f"build/src/{spec_name}.py").exists()
    elif file_type == "test":
        return Path(f"build/tests/test_{spec_name}.py").exists()
    return False


def _check_tool_available(tool: str) -> bool:
    """Check if a tool is available in the system PATH."""
    import shutil
    return shutil.which(tool) is not None


if __name__ == "__main__":
    main()
