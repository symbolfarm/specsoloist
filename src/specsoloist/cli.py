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
from spechestra.composer import SpecComposer, Architecture
from spechestra.conductor import SpecConductor
from .lifter import SpecLifter
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

    # verify
    subparsers.add_parser("verify", help="Verify all specs for orchestration readiness")

    # graph
    subparsers.add_parser("graph", help="Export dependency graph as Mermaid")

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

    # compose
    compose_parser = subparsers.add_parser("compose", help="Draft architecture and specs from natural language (uses AI agent)")
    compose_parser.add_argument("request", help="Description of the system you want to build")
    compose_parser.add_argument("--agent", choices=["claude", "gemini", "auto"], default="auto",
                                help="AI agent to use (default: auto-detect)")
    compose_parser.add_argument("--no-agent", action="store_true",
                                help="Use direct LLM API instead of agent CLI")
    compose_parser.add_argument("--auto-accept", action="store_true", help="Skip interactive review (only with --no-agent)")

    # conduct
    conduct_parser = subparsers.add_parser("conduct", help="Orchestrate project build")
    conduct_parser.add_argument("--incremental", action="store_true", help="Only recompile changed specs")
    conduct_parser.add_argument("--parallel", action="store_true", help="Compile independent specs concurrently")
    conduct_parser.add_argument("--workers", type=int, default=4, help="Max parallel workers (default: 4)")
    conduct_parser.add_argument("--model", help="Override LLM model")

    # perform
    perform_parser = subparsers.add_parser("perform", help="Execute an orchestration workflow")
    perform_parser.add_argument("workflow", help="Workflow spec name")
    perform_parser.add_argument("inputs", help="JSON inputs for the workflow")

    # respec
    respec_parser = subparsers.add_parser("respec", help="Reverse engineer code to spec (uses AI agent)")
    respec_parser.add_argument("file", help="Path to source file")
    respec_parser.add_argument("--test", help="Path to test file (optional)")
    respec_parser.add_argument("--out", help="Output path (optional)")
    respec_parser.add_argument("--agent", choices=["claude", "gemini", "auto"], default="auto",
                               help="AI agent to use (default: auto-detect)")
    respec_parser.add_argument("--no-agent", action="store_true",
                               help="Use direct LLM API instead of agent CLI")
    respec_parser.add_argument("--model", help="LLM model override (only with --no-agent)")

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
            agent = None if args.no_agent else args.agent
            cmd_compose(core, args.request, agent, args.auto_accept)
        elif args.command == "conduct":
            cmd_conduct(core, args.incremental, args.parallel, args.workers)
        elif args.command == "perform":
            cmd_perform(core, args.workflow, args.inputs)
        elif args.command == "respec":
            agent = None if args.no_agent else args.agent
            cmd_respec(core, args.file, args.test, args.out, args.model, agent)
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


def cmd_compose(core: SpecSoloistCore, request: str, agent: str, auto_accept: bool):
    """Draft architecture and specs from natural language, optionally using an AI agent."""

    ui.print_header("Composing System", request[:50] + "..." if len(request) > 50 else request)

    if agent:
        # Agent mode: invoke external AI agent CLI
        _compose_with_agent(request, agent)
    else:
        # Classic mode: direct LLM API calls
        _compose_with_llm(core, request, auto_accept)


def _compose_with_agent(request: str, agent: str):
    """Use an AI agent CLI (claude, gemini) for multi-step composition."""
    import shutil
    import subprocess

    # Auto-detect agent if requested
    if agent == "auto":
        if shutil.which("claude"):
            agent = "claude"
        elif shutil.which("gemini"):
            agent = "gemini"
        else:
            ui.print_error("No AI agent CLI found. Install 'claude' or 'gemini' CLI, or use --no-agent flag.")
            sys.exit(1)

    # Check agent is available
    if not shutil.which(agent):
        ui.print_error(f"Agent CLI '{agent}' not found in PATH.")
        sys.exit(1)

    # Load the compose prompt
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "score", "prompts", "compose.md")
    if not os.path.exists(prompt_path):
        # Try relative to cwd
        prompt_path = os.path.join(os.getcwd(), "score", "prompts", "compose.md")

    if not os.path.exists(prompt_path):
        ui.print_error("Compose prompt not found at score/prompts/compose.md")
        sys.exit(1)

    with open(prompt_path, 'r') as f:
        base_prompt = f.read()

    # Build the task prompt
    task_prompt = f"""{base_prompt}

---

## Your Task

Design and implement specs for the following request:

**Request**: {request}

**Project directory**: {os.getcwd()}

After creating each spec, validate it with `sp validate <spec_path>` and fix any errors before proceeding.
When all specs are created, show the user what was created.
"""

    ui.print_info(f"Invoking {agent} agent...")
    ui.print_step(f"Request: {request}")

    # Invoke the agent
    try:
        if agent == "claude":
            # Claude Code CLI: claude --print "prompt"
            result = subprocess.run(
                ["claude", "--print", task_prompt],
                capture_output=False,
                text=True
            )
        elif agent == "gemini":
            # Gemini CLI
            result = subprocess.run(
                ["gemini", task_prompt],
                capture_output=False,
                text=True
            )

        if result.returncode != 0:
            ui.print_error(f"Agent exited with code {result.returncode}")
            sys.exit(1)

    except FileNotFoundError:
        ui.print_error(f"Failed to invoke {agent} CLI")
        sys.exit(1)
    except Exception as e:
        ui.print_error(f"Agent error: {e}")
        sys.exit(1)


def _compose_with_llm(core: SpecSoloistCore, request: str, auto_accept: bool):
    """Classic direct LLM composition (single-shot, no agent iteration)."""
    _check_api_key()

    ui.print_warning("Classic mode: using direct LLM calls. Use --agent for multi-step composition.")

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


def cmd_conduct(core: SpecSoloistCore, incremental: bool, parallel: bool, workers: int):
    _check_api_key()
    
    ui.print_header("Conducting Build", "Using SpecConductor")
    
    conductor = SpecConductor(core.project_dir)
    
    with ui.spinner("Orchestrating build..."):
        result = conductor.build(
            incremental=incremental,
            parallel=parallel,
            max_workers=workers
        )
        
    # Reuse the summary display from build? Or create new one.
    # For now, let's create a similar summary.
    
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


def cmd_perform(core: SpecSoloistCore, workflow: str, inputs_json: str):
    import json
    from rich.prompt import Confirm
    
    ui.print_header("Performing Workflow", workflow)
    
    try:
        inputs = json.loads(inputs_json)
    except json.JSONDecodeError:
        ui.print_error("Invalid JSON inputs")
        sys.exit(1)
        
    conductor = SpecConductor(core.project_dir)
    
    def checkpoint_callback(step_name: str) -> bool:
        return Confirm.ask(f"[bold yellow]Checkpoint:[/] Proceed with step '{step_name}'?")

    try:
        result = conductor.perform(
            workflow, 
            inputs, 
            checkpoint_callback=checkpoint_callback
        )
        
        # Display results
        table = ui.create_table(["Step", "Status", "Duration", "Result"], title="Performance Summary")
        for step in result.steps:
            status = "[green]Success[/]" if step.success else "[red]Failed[/]"
            duration = f"{step.duration:.2f}s"
            
            # Format output briefly
            output_str = str(step.outputs)[:50] + "..." if len(str(step.outputs)) > 50 else str(step.outputs)
            if step.error:
                output_str = f"[red]{step.error}[/]"
                
            table.add_row(step.name, status, duration, output_str)
            
        ui.console.print(table)
        
        if result.success:
            ui.print_success("Performance complete")
            ui.print_info(f"Trace saved to: {result.trace_path}")
            # Show final outputs
            ui.console.print(ui.Panel(str(result.outputs), title="Final Outputs"))
        else:
            ui.print_error("Performance failed")
            sys.exit(1)
            
    except Exception as e:
        ui.print_error(f"Performance error: {e}")
        # Print traceback for debugging
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_respec(core: SpecSoloistCore, file_path: str, test_path: str, out_path: str, model: str, agent: str):
    """Reverse engineer code to spec, optionally using an AI agent."""

    ui.print_header("Respec: Code → Spec", file_path)

    if agent:
        # Agent mode: invoke external AI agent CLI
        _respec_with_agent(file_path, test_path, out_path, agent)
    else:
        # Classic mode: single LLM API call
        _respec_with_llm(core, file_path, test_path, out_path, model)


def _respec_with_agent(file_path: str, test_path: str, out_path: str, agent: str):
    """Use an AI agent CLI (claude, gemini) for multi-step respec."""
    import shutil
    import subprocess

    # Auto-detect agent if requested
    if agent == "auto":
        if shutil.which("claude"):
            agent = "claude"
        elif shutil.which("gemini"):
            agent = "gemini"
        else:
            ui.print_error("No AI agent CLI found. Install 'claude' or 'gemini' CLI, or omit --agent flag.")
            sys.exit(1)

    # Check agent is available
    if not shutil.which(agent):
        ui.print_error(f"Agent CLI '{agent}' not found in PATH.")
        sys.exit(1)

    # Load the respec prompt
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "score", "prompts", "respec.md")
    if not os.path.exists(prompt_path):
        # Try relative to cwd
        prompt_path = os.path.join(os.getcwd(), "score", "prompts", "respec.md")

    if not os.path.exists(prompt_path):
        ui.print_error("Respec prompt not found at score/prompts/respec.md")
        sys.exit(1)

    with open(prompt_path, 'r') as f:
        base_prompt = f.read()

    # Build the task prompt
    out_instruction = f"Write the spec to: {out_path}" if out_path else "Print the spec to stdout"
    test_instruction = f"Test file for examples: {test_path}" if test_path else "No test file provided"

    task_prompt = f"""{base_prompt}

---

## Your Task

Respec this file: `{file_path}`
{test_instruction}
{out_instruction}

After generating the spec, validate it with `sp validate <spec_path>` and fix any errors.
"""

    ui.print_info(f"Invoking {agent} agent...")
    ui.print_step(f"Source: {file_path}")
    if out_path:
        ui.print_step(f"Output: {out_path}")

    # Invoke the agent
    try:
        if agent == "claude":
            # Claude Code CLI: claude --print "prompt"
            result = subprocess.run(
                ["claude", "--print", task_prompt],
                capture_output=False,
                text=True
            )
        elif agent == "gemini":
            # Gemini CLI: gemini "prompt" (adjust based on actual CLI)
            result = subprocess.run(
                ["gemini", task_prompt],
                capture_output=False,
                text=True
            )

        if result.returncode != 0:
            ui.print_error(f"Agent exited with code {result.returncode}")
            sys.exit(1)

    except FileNotFoundError:
        ui.print_error(f"Failed to invoke {agent} CLI")
        sys.exit(1)
    except Exception as e:
        ui.print_error(f"Agent error: {e}")
        sys.exit(1)


def _respec_with_llm(core: SpecSoloistCore, file_path: str, test_path: str, out_path: str, model: str):
    """Classic single-shot LLM respec (no validation loop)."""
    _check_api_key()

    lifter = SpecLifter(core.config)

    with ui.spinner("Analyzing code and generating spec..."):
        try:
            spec_content = lifter.lift(file_path, test_path, model)
        except Exception as e:
            ui.print_error(f"Respec failed: {e}")
            sys.exit(1)

    ui.print_warning("Classic mode: spec not validated. Use --agent for multi-step respec with validation.")

    if out_path:
        with open(out_path, 'w') as f:
            f.write(spec_content)
        ui.print_success(f"Spec saved to: [bold]{out_path}[/]")
    else:
        ui.console.print(ui.Panel(spec_content, title="Generated Spec", border_style="blue"))
        ui.print_info("Use --out <path> to save to file.")


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