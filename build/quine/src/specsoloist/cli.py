"""
Command-line interface for SpecSoloist.

Provides the `sp` command with subcommands for managing, compiling, testing, and building specs.
Supports both direct LLM API calls and agent-based workflows (via Claude or Gemini CLI).
"""

import argparse
import sys
import os
import subprocess
import shutil
import json
import tempfile

from .core import SpecSoloistCore
from .resolver import CircularDependencyError, MissingDependencyError
from . import ui


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="sp",
        description="Spec-as-Source AI coding framework"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Spec Management
    subparsers.add_parser("list", help="List all specification files")

    create_parser = subparsers.add_parser("create", help="Create a new spec from template")
    create_parser.add_argument("name", help="Spec name (e.g., 'auth' creates auth.spec.md)")
    create_parser.add_argument("description", help="Brief description of the component")
    create_parser.add_argument("--type", default="bundle", help="Spec type: bundle, function, type, module, workflow")

    validate_parser = subparsers.add_parser("validate", help="Validate a spec's structure")
    validate_parser.add_argument("name", help="Spec name to validate")

    subparsers.add_parser("verify", help="Verify all specs for orchestration readiness")

    subparsers.add_parser("graph", help="Export dependency graph as Mermaid")

    # Compilation
    compile_parser = subparsers.add_parser("compile", help="Compile a spec to code")
    compile_parser.add_argument("name", help="Spec name to compile")
    compile_parser.add_argument("--model", help="Override LLM model")
    compile_parser.add_argument("--no-tests", action="store_true", help="Skip test generation")

    # Testing & Fixing
    test_parser = subparsers.add_parser("test", help="Run tests for a spec")
    test_parser.add_argument("name", help="Spec name to test")

    fix_parser = subparsers.add_parser("fix", help="Auto-fix failing tests")
    fix_parser.add_argument("name", help="Spec name to fix")
    fix_parser.add_argument("--model", help="Override LLM model")

    # Build
    build_parser = subparsers.add_parser("build", help="Compile all specs in dependency order")
    build_parser.add_argument("--incremental", action="store_true", help="Only recompile changed specs")
    build_parser.add_argument("--parallel", action="store_true", help="Compile independent specs concurrently")
    build_parser.add_argument("--workers", type=int, default=4, help="Max parallel workers (default: 4)")
    build_parser.add_argument("--model", help="Override LLM model")
    build_parser.add_argument("--no-tests", action="store_true", help="Skip test generation")

    # Orchestration
    compose_parser = subparsers.add_parser("compose", help="Draft architecture and specs from natural language")
    compose_parser.add_argument("request", help="Description of the system you want to build")
    compose_parser.add_argument("--no-agent", action="store_true", help="Use direct LLM API instead of agent CLI")
    compose_parser.add_argument("--auto-accept", action="store_true", help="Skip interactive review")
    compose_parser.add_argument("--model", help="Override LLM model")

    conduct_parser = subparsers.add_parser("conduct", help="Orchestrate project build")
    conduct_parser.add_argument("src_dir", nargs="?", default=None, help="Spec directory (default: src/)")
    conduct_parser.add_argument("--no-agent", action="store_true", help="Use direct LLM API instead of agent CLI")
    conduct_parser.add_argument("--auto-accept", action="store_true", help="Skip interactive review")
    conduct_parser.add_argument("--incremental", action="store_true", help="Only recompile changed specs")
    conduct_parser.add_argument("--parallel", action="store_true", help="Compile independent specs concurrently")
    conduct_parser.add_argument("--workers", type=int, default=4, help="Max parallel workers (default: 4)")
    conduct_parser.add_argument("--model", help="Override LLM model")

    perform_parser = subparsers.add_parser("perform", help="Execute an orchestration workflow")
    perform_parser.add_argument("workflow", help="Workflow spec name")
    perform_parser.add_argument("inputs", help="JSON inputs for the workflow")

    # Reverse Engineering
    respec_parser = subparsers.add_parser("respec", help="Reverse engineer code to spec")
    respec_parser.add_argument("file", help="Path to source file")
    respec_parser.add_argument("--test", help="Path to test file (optional)")
    respec_parser.add_argument("--out", help="Output path (optional)")
    respec_parser.add_argument("--no-agent", action="store_true", help="Use direct LLM API instead of agent CLI")
    respec_parser.add_argument("--model", help="LLM model override")
    respec_parser.add_argument("--auto-accept", action="store_true", help="Skip interactive review")

    # MCP (hidden for backwards compatibility)
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
        elif args.command == "verify":
            cmd_verify(core)
        elif args.command == "graph":
            cmd_graph(core)
        elif args.command == "compile":
            cmd_compile(core, args.name, args.model, not args.no_tests)
        elif args.command == "test":
            cmd_test(core, args.name)
        elif args.command == "fix":
            cmd_fix(core, args.name, args.model)
        elif args.command == "build":
            cmd_build(core, args.incremental, args.parallel, args.workers, args.model, not args.no_tests)
        elif args.command == "compose":
            cmd_compose(core, args.request, args.no_agent, args.auto_accept, args.model)
        elif args.command == "conduct":
            cmd_conduct(core, args.src_dir, args.no_agent, args.auto_accept, args.incremental, args.parallel, args.workers, args.model)
        elif args.command == "perform":
            cmd_perform(core, args.workflow, args.inputs)
        elif args.command == "respec":
            cmd_respec(core, args.file, args.test, args.out, args.no_agent, args.model, args.auto_accept)
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
        sys.exit(1)


def cmd_list(core: SpecSoloistCore):
    """List all specs with name, type, status, and description."""
    specs = core.list_specs()
    if not specs:
        ui.print_warning("No specs found in src/")
        ui.print_info("Create one with: sp create <name> '<description>'")
        return

    table = ui.create_table(["Name", "Type", "Status", "Description"], title="Project Specifications")

    for spec_file in specs:
        try:
            name = spec_file.replace(".spec.md", "")
            parsed = core.parser.parse_spec(name)
            meta = parsed.metadata

            status_style = "green" if meta.status == "stable" else "yellow"

            table.add_row(
                f"[bold]{name}[/]",
                meta.type,
                f"[{status_style}]{meta.status}[/]",
                meta.description or ""
            )
        except Exception as e:
            table.add_row(spec_file, "???", "error", f"Error: {str(e)}")

    ui.console.print(table)


def cmd_create(core: SpecSoloistCore, name: str, description: str, spec_type: str):
    """Create a new spec from template."""
    ui.print_header("Creating Spec", name)
    try:
        path = core.create_spec(name, description, type=spec_type)
        ui.print_success(f"Created spec at: [bold]{path}[/]")
    except FileExistsError:
        ui.print_error(f"Spec already exists: {name}.spec.md")
        sys.exit(1)


def cmd_validate(core: SpecSoloistCore, name: str):
    """Validate a spec's structure; exit 1 if invalid."""
    ui.print_header("Validating Spec", name)
    result = core.validate_spec(name)

    if result["valid"]:
        ui.print_success(f"{name} is VALID")
    else:
        ui.print_error(f"{name} is INVALID")
        for error in result["errors"]:
            ui.print_step(f"[red]{error}[/]")
        sys.exit(1)


def cmd_verify(core: SpecSoloistCore):
    """Verify all specs for orchestration readiness."""
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


def cmd_graph(core: SpecSoloistCore):
    """Export dependency graph as Mermaid diagram."""
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


def cmd_compile(core: SpecSoloistCore, name: str, model: str, generate_tests: bool):
    """Compile a single spec to code."""
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
    """Run tests for a spec; exit 1 if tests fail."""
    ui.print_header("Running Tests", name)

    with ui.spinner(f"Running tests for [bold]{name}[/]..."):
        result = core.run_tests(name)

    if result["success"]:
        ui.print_success("Tests PASSED")
    else:
        ui.print_error("Tests FAILED")
        ui.console.print(ui.Panel(result["output"], title="Failure Output", border_style="red"))
        sys.exit(1)


def cmd_fix(core: SpecSoloistCore, name: str, model: str):
    """Auto-fix failing tests using LLM analysis."""
    _check_api_key()

    ui.print_header("Auto-Fixing Spec", name)

    with ui.spinner(f"Analyzing [bold]{name}[/] failures and generating fix..."):
        result = core.attempt_fix(name, model=model)

    ui.print_success(result)


def cmd_build(core: SpecSoloistCore, incremental: bool, parallel: bool, workers: int, model: str, generate_tests: bool):
    """Compile all specs in dependency order."""
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
        if len(error) > 50:
            error = error[:47] + "..."
        table.add_row("[red]Failed[/]", spec, error)

    ui.console.print(table)

    if result.success:
        ui.print_success("Build complete.")
    else:
        ui.print_error("Build failed.")
        sys.exit(1)


def cmd_compose(core: SpecSoloistCore, request: str, no_agent: bool, auto_accept: bool, model: str = None):
    """Draft architecture and specs from natural language description."""
    ui.print_header("Composing System", request[:50] + "..." if len(request) > 50 else request)

    if no_agent:
        ui.print_error("Compose with --no-agent requires SpecComposer (spechestra module)")
        ui.print_info("Install spechestra or use agent mode (default)")
        sys.exit(1)
    else:
        _compose_with_agent(request, auto_accept, model=model)


def _compose_with_agent(request: str, auto_accept: bool, model: str = None):
    """Use an AI agent CLI for multi-step composition."""
    agent = _detect_agent_cli()
    if not agent:
        ui.print_error("No agent CLI found (claude or gemini). Install one or use --no-agent.")
        sys.exit(1)

    ui.print_info(f"Using {agent} agent with native subagent...")
    if model:
        ui.print_info(f"Model: {model}")

    prompt = f"compose: {request}"

    try:
        _run_agent_oneshot(agent, prompt, auto_accept, model=model)
    except Exception as e:
        ui.print_error(f"Agent error: {e}")
        sys.exit(1)


def cmd_conduct(core: SpecSoloistCore, src_dir: str, no_agent: bool, auto_accept: bool,
                incremental: bool, parallel: bool, workers: int, model: str = None):
    """Orchestrate project build using SpecConductor."""
    ui.print_header("Conducting Build", src_dir or "project specs")

    if no_agent:
        ui.print_error("Conduct with --no-agent requires SpecConductor (spechestra module)")
        ui.print_info("Install spechestra or use agent mode (default)")
        sys.exit(1)
    else:
        _conduct_with_agent(src_dir, auto_accept, model=model)


def _conduct_with_agent(src_dir: str, auto_accept: bool, model: str = None):
    """Use an AI agent CLI for multi-step orchestrated build."""
    agent = _detect_agent_cli()
    if not agent:
        ui.print_error("No agent CLI found (claude or gemini). Install one or use --no-agent.")
        sys.exit(1)

    ui.print_info(f"Using {agent} agent with native subagent...")
    if model:
        ui.print_info(f"Model: {model}")

    spec_dir = src_dir or "src/"

    # Detect if this is a quine attempt
    is_quine = "score" in spec_dir

    if is_quine:
        quine_dir = "build/quine"
        os.makedirs(f"{quine_dir}/src/specsoloist", exist_ok=True)
        os.makedirs(f"{quine_dir}/src/spechestra", exist_ok=True)
        os.makedirs(f"{quine_dir}/tests", exist_ok=True)

        ui.print_info(f"Quine mode: Will regenerate code to {quine_dir}/")

        prompt = (
            f"conduct: Read all *.spec.md files in {spec_dir}, resolve their dependency order, "
            f"then compile each spec into working code by spawning soloist subagents. "
            f"\n\n**Output Paths:**\n"
            f"- Write specsoloist implementations to: {quine_dir}/src/specsoloist/<name>.py\n"
            f"- Write spechestra implementations to: {quine_dir}/src/spechestra/<name>.py\n"
            f"- Write tests to: {quine_dir}/tests/test_<name>.py\n\n"
            f"This is a QUINE VALIDATION - you are intentionally regenerating code to verify specs are complete. "
            f"Do NOT skip compilation because code already exists elsewhere. "
            f"Run the full test suite from {quine_dir}/tests/ when done."
        )
    else:
        prompt = (
            f"conduct: Read all *.spec.md files in {spec_dir}, resolve their dependency order, "
            f"then compile each spec into working code by spawning soloist subagents. "
            f"Write implementations to the appropriate src/ paths and tests to tests/. "
            f"Run the full test suite when done."
        )

    if model:
        prompt += f'\n\n**Model**: When spawning soloist subagents via the Task tool, set model: "{model}".'

    try:
        _run_agent_oneshot(agent, prompt, auto_accept, model=model)
    except Exception as e:
        ui.print_error(f"Agent error: {e}")
        sys.exit(1)


def cmd_perform(core: SpecSoloistCore, workflow: str, inputs_json: str):
    """Execute a workflow spec with JSON inputs."""
    ui.print_header("Performing Workflow", workflow)

    try:
        inputs = json.loads(inputs_json)
    except json.JSONDecodeError:
        ui.print_error("Invalid JSON inputs")
        sys.exit(1)

    # Perform requires SpecConductor which is not available in this build
    ui.print_error("Perform requires SpecConductor (spechestra module)")
    ui.print_info("Install spechestra to use workflow orchestration")
    sys.exit(1)


def cmd_respec(core: SpecSoloistCore, file_path: str, test_path: str, out_path: str, no_agent: bool, model: str, auto_accept: bool):
    """Reverse engineer source code to spec."""
    ui.print_header("Respec: Code → Spec", file_path)

    if no_agent:
        ui.print_error("Respec with --no-agent requires Respecer module")
        ui.print_info("Use agent mode (default) or implement Respecer")
        sys.exit(1)
    else:
        _respec_with_agent(file_path, test_path, out_path, auto_accept, model=model)


def _respec_with_agent(file_path: str, test_path: str, out_path: str, auto_accept: bool, model: str = None):
    """Use an AI agent CLI for multi-step respec with validation."""
    agent = _detect_agent_cli()
    if not agent:
        ui.print_error("No agent CLI found (claude or gemini). Install one or use --no-agent.")
        sys.exit(1)

    ui.print_info(f"Using {agent} agent with native subagent...")
    if model:
        ui.print_info(f"Model: {model}")

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


def cmd_mcp():
    """Start the MCP server for AI agent integration."""
    ui.print_error("MCP server requires server module")
    ui.print_info("MCP integration not available in this build")
    sys.exit(1)


def _detect_agent_cli() -> str:
    """Detect which agent CLI is available (claude preferred over gemini)."""
    if shutil.which("claude"):
        return "claude"
    if shutil.which("gemini"):
        return "gemini"
    return None


def _run_agent_oneshot(agent: str, prompt: str, auto_accept: bool, model: str = None):
    """Run an agent CLI in one-shot mode."""
    if agent == "claude":
        cmd = ["claude", "-p", prompt, "--verbose"]
        if model:
            cmd.extend(["--model", model])
        if auto_accept:
            cmd.extend(["--permission-mode", "bypassPermissions"])
        result = subprocess.run(cmd, capture_output=False, text=True)
    elif agent == "gemini":
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
