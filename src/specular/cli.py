"""
Command-line interface for Specular.

Usage:
    specular list                     List all specs
    specular create <name> <desc>     Create a new spec
    specular validate <name>          Validate a spec
    specular compile <name>           Compile a spec to code
    specular test <name>              Run tests for a spec
    specular fix <name>               Auto-fix failing tests
    specular build                    Compile all specs
"""

import argparse
import sys
import os

from .core import SpecularCore


def main():
    parser = argparse.ArgumentParser(
        prog="specular",
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
    core = SpecularCore(os.getcwd())

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


def cmd_list(core: SpecularCore):
    specs = core.list_specs()
    if not specs:
        print("No specs found in src/")
        print("Create one with: specular create <name> '<description>'")
        return
    print(f"Found {len(specs)} spec(s):")
    for spec in specs:
        print(f"  - {spec}")


def cmd_create(core: SpecularCore, name: str, description: str, spec_type: str):
    try:
        result = core.create_spec(name, description, type=spec_type)
        print(result)
    except FileExistsError:
        print(f"Error: {name}.spec.md already exists")
        sys.exit(1)


def cmd_validate(core: SpecularCore, name: str):
    result = core.validate_spec(name)
    if result["valid"]:
        print(f"{name}: VALID")
    else:
        print(f"{name}: INVALID")
        for error in result["errors"]:
            print(f"  - {error}")
        sys.exit(1)


def cmd_compile(core: SpecularCore, name: str, model: str, generate_tests: bool):
    _check_api_key()

    try:
        # Validate first
        validation = core.validate_spec(name)
        if not validation["valid"]:
            print("Error: Invalid spec")
            for error in validation["errors"]:
                print(f"  - {error}")
            sys.exit(1)

        # Compile code
        print(f"Compiling {name}...")
        result = core.compile_spec(name, model=model)
        print(result)

        # Generate tests
        if generate_tests:
            spec = core.parser.parse_spec(name)
            if spec.metadata.type != "typedef":
                print("Generating tests...")
                result = core.compile_tests(name, model=model)
                print(result)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_test(core: SpecularCore, name: str):
    result = core.run_tests(name)
    print(result["output"])
    if not result["success"]:
        sys.exit(1)


def cmd_fix(core: SpecularCore, name: str, model: str):
    _check_api_key()

    print(f"Analyzing failures and generating fix for {name}...")
    result = core.attempt_fix(name, model=model)
    print(result)


def cmd_build(core: SpecularCore, incremental: bool, parallel: bool, workers: int, model: str, generate_tests: bool):
    _check_api_key()

    specs = core.list_specs()
    if not specs:
        print("No specs found in src/")
        sys.exit(1)

    mode = []
    if incremental:
        mode.append("incremental")
    if parallel:
        mode.append("parallel")
    mode_str = f" ({', '.join(mode)})" if mode else ""

    print(f"Building {len(specs)} spec(s){mode_str}...")

    result = core.compile_project(
        model=model,
        generate_tests=generate_tests,
        incremental=incremental,
        parallel=parallel,
        max_workers=workers
    )

    if result.specs_compiled:
        print(f"Compiled: {', '.join(result.specs_compiled)}")
    if result.specs_skipped:
        print(f"Skipped (unchanged): {', '.join(result.specs_skipped)}")
    if result.specs_failed:
        print(f"Failed: {', '.join(result.specs_failed)}")
        for name, error in result.errors.items():
            print(f"  {name}: {error}")

    if result.success:
        print("Build complete.")
    else:
        print("Build failed.")
        sys.exit(1)


def cmd_mcp():
    """Start the MCP server."""
    from .server import main as mcp_main
    mcp_main()


def _check_api_key():
    """Check that an API key is configured."""
    provider = os.environ.get("SPECULAR_LLM_PROVIDER", "gemini")
    if provider == "gemini" and "GEMINI_API_KEY" not in os.environ:
        print("Error: GEMINI_API_KEY not set")
        print("Run: export GEMINI_API_KEY='your-key-here'")
        sys.exit(1)
    elif provider == "anthropic" and "ANTHROPIC_API_KEY" not in os.environ:
        print("Error: ANTHROPIC_API_KEY not set")
        print("Run: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)


if __name__ == "__main__":
    main()
