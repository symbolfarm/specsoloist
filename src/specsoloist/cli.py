"""
Command-line interface for SpecSoloist.

Usage:
    sp list                     List all specs
    sp create <name> <desc>     Create a new spec
    sp validate <name>          Validate a spec
    sp compile <name>           Compile a spec to code
    sp test <name>              Run tests for a spec
    sp fix <name>               Auto-fix failing tests
    sp build                    Compile all specs
"""

import argparse
import sys
import os

from .core import SpecSoloistCore
from .resolver import CircularDependencyError, MissingDependencyError
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

    # compile
    compile_parser = subparsers.add_parser("compile", help="Compile a spec to code")
    compile_parser.add_argument("name", help="Spec name to compile")
    compile_parser.add_argument("--model", help="Override LLM model")
    compile_parser.add_argument("--no-tests", action="store_true", help="Skip test generation")

    # test
    test_parser = subparsers.add_parser("test", help="Run tests for a spec")
    test_parser.add_argument("name", help="Spec name to test")

    # fix
    fix_parser = subparsers.add_parser("fix", help="Auto-fix failing tests")
    fix_parser.add_argument("name", help="Spec name to fix")
    fix_parser.add_argument("--model", help="Override LLM model")

    # build
    build_parser = subparsers.add_parser("build", help="Compile all specs in dependency order")
    build_parser.add_argument("--incremental", action="store_true", help="Only recompile changed specs")
    build_parser.add_argument("--parallel", action="store_true", help="Compile independent specs concurrently")
    build_parser.add_argument("--workers", type=int, default=4, help="Max parallel workers (default: 4)")
    build_parser.add_argument("--model", help="Override LLM model")
    build_parser.add_argument("--no-tests", action="store_true", help="Skip test generation")

    # mcp (hidden, for backwards compatibility)
    subparsers.add_parser("mcp", help="Start MCP server (for AI agents)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

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
            cmd_validate(core, args.name)
        elif args.command == "compile":
            cmd_compile(core, args.name, args.model, not args.no_tests)
        elif args.command == "test":
            cmd_test(core, args.name)
        elif args.command == "fix":
            cmd_fix(core, args.name, args.model)
        elif args.command == "build":
            cmd_build(core, args.incremental, args.parallel, args.workers, args.model, not args.no_tests)
        elif args.command == "mcp":
            cmd_mcp()
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


def cmd_validate(core: SpecSoloistCore, name: str):
    ui.print_header("Validating Spec", name)
    result = core.validate_spec(name)
    
    if result["valid"]:
        ui.print_success(f"{name} is VALID")
    else:
        ui.print_error(f"{name} is INVALID")
        for error in result["errors"]:
            ui.print_step(f"[red]{error}[/]")
        sys.exit(1)


def cmd_compile(core: SpecSoloistCore, name: str, model: str, generate_tests: bool):
    _check_api_key()
    
    ui.print_header("Compiling Spec", name)

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
            result = core.compile_spec(name, model=model)
        ui.print_success(result)

        # Generate tests
        if generate_tests:
            spec = core.parser.parse_spec(name)
            if spec.metadata.type != "typedef":
                with ui.spinner(f"Generating tests for [bold]{name}[/]..."):
                    result = core.compile_tests(name, model=model)
                ui.print_success(result)
            else:
                ui.print_info("Skipping tests for typedef spec")

    except Exception as e:
        ui.print_error(str(e))
        sys.exit(1)


def cmd_test(core: SpecSoloistCore, name: str):
    ui.print_header("Running Tests", name)
    
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


def cmd_fix(core: SpecSoloistCore, name: str, model: str):
    _check_api_key()

    ui.print_header("Auto-Fixing Spec", name)
    
    with ui.spinner(f"Analyzing [bold]{name}[/] failures and generating fix..."):
        result = core.attempt_fix(name, model=model)
    
    ui.print_success(result)


def cmd_build(core: SpecSoloistCore, incremental: bool, parallel: bool, workers: int, model: str, generate_tests: bool):
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

    with ui.spinner("Compiling project..."):
        result = core.compile_project(
            model=model,
            generate_tests=generate_tests,
            incremental=incremental,
            parallel=parallel,
            max_workers=workers
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


def cmd_mcp():
    """Start the MCP server."""
    from .server import main as mcp_main
    mcp_main()


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