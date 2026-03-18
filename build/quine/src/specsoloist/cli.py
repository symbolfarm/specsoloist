"""Command-line interface for SpecSoloist."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Optional

import click

from specsoloist import ui
from specsoloist.config import SpecSoloistConfig
from specsoloist.core import SpecSoloistCore
from specsoloist.resolver import CircularDependencyError, MissingDependencyError


def _load_arrangement(arrangement_path: Optional[str]):
    """Load arrangement from file or auto-discover."""
    if arrangement_path:
        try:
            import yaml
            with open(arrangement_path) as f:
                data = yaml.safe_load(f)
            from specsoloist.schema import Arrangement
            return Arrangement(**data)
        except Exception as e:
            ui.print_warning(f"Could not load arrangement: {e}")
            return None

    # Auto-discover
    for candidate in ("arrangement.yaml", "arrangement.yml"):
        if os.path.exists(candidate):
            return _load_arrangement(candidate)

    return None


def _resolve_model(model: Optional[str], arrangement=None) -> Optional[str]:
    """Resolve model with precedence: --model > arrangement.model > env var > default."""
    if model:
        return model
    if arrangement and hasattr(arrangement, "model") and arrangement.model:
        return arrangement.model
    env_model = os.environ.get("SPECSOLOIST_LLM_MODEL")
    if env_model:
        return env_model
    return None


def _check_api_key(config: SpecSoloistConfig) -> bool:
    """Check if the required API key is set."""
    provider = config.llm_provider
    key_vars = {
        "gemini": "GEMINI_API_KEY",
        "google": "GEMINI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    if provider in ("ollama",):
        return True  # No key required
    if provider in key_vars:
        key_var = key_vars[provider]
        if not os.environ.get(key_var) and not config.api_key:
            ui.print_error(
                f"Missing API key: set {key_var} environment variable for {provider} provider"
            )
            return False
    return True


@click.group()
@click.option("--quiet", is_flag=True, help="Suppress all non-error output")
@click.option("--json", "json_mode", is_flag=True, help="Emit machine-readable JSON")
@click.pass_context
def cli(ctx: click.Context, quiet: bool, json_mode: bool) -> None:
    """sp - SpecSoloist CLI for spec-driven development."""
    ui.configure(quiet=quiet, json_mode=json_mode)
    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet
    ctx.obj["json_mode"] = json_mode


@cli.command("list")
def list_specs() -> None:
    """List all specs in the project."""
    try:
        config = SpecSoloistConfig.from_env()
        core = SpecSoloistCore(config=config)
        specs = core.list_specs()

        if ui.is_json_mode():
            click.echo(json.dumps({"specs": specs}))
            return

        if not specs:
            ui.print_info("No specs found.")
            return

        table = ui.create_table(["Name", "Type", "Status", "Description"])
        for spec_path in specs:
            try:
                spec = core.parser.parse_spec(spec_path)
                name = spec.metadata.name or core.parser.get_module_name(spec_path)
                table.add_row(
                    name,
                    spec.metadata.type,
                    spec.metadata.status,
                    spec.metadata.description[:60] if spec.metadata.description else "",
                )
            except Exception:
                table.add_row(spec_path, "", "", "")

        ui.console.print(table)
    except (CircularDependencyError, MissingDependencyError) as e:
        ui.print_error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        ui.print_warning("Interrupted")
        sys.exit(130)


@cli.command("create")
@click.argument("name")
@click.argument("description")
@click.option("--type", "spec_type", default="function", help="Spec type")
def create_spec(name: str, description: str, spec_type: str) -> None:
    """Create a new spec from template."""
    config = SpecSoloistConfig.from_env()
    core = SpecSoloistCore(config=config)
    try:
        result = core.create_spec(name, description, spec_type)
        ui.print_success(result)
    except FileExistsError as e:
        ui.print_error(str(e))
        sys.exit(1)


@cli.command("validate")
@click.argument("name")
@click.option("--arrangement", "arrangement_path", default=None, help="Arrangement file")
@click.option("--json", "json_out", is_flag=True, help="JSON output")
def validate_spec(name: str, arrangement_path: Optional[str], json_out: bool) -> None:
    """Validate a spec's structure."""
    config = SpecSoloistConfig.from_env()
    core = SpecSoloistCore(config=config)
    result = core.validate_spec(name)

    if json_out or ui.is_json_mode():
        click.echo(json.dumps(result))
    else:
        if result["valid"]:
            ui.print_success(f"{name}: valid")
        else:
            ui.print_error(f"{name}: invalid")
            for err in result["errors"]:
                ui.print_step(f"  {err}")

    if not result["valid"]:
        sys.exit(1)


@cli.command("verify")
def verify_project() -> None:
    """Verify all specs for orchestration readiness."""
    config = SpecSoloistConfig.from_env()
    core = SpecSoloistCore(config=config)
    result = core.verify_project()

    if result["success"]:
        ui.print_success("All specs verified successfully")
    else:
        ui.print_error("Verification failed")
        for spec, details in result["results"].items():
            if not details.get("valid", True):
                for err in details.get("errors", []):
                    ui.print_step(f"  {spec}: {err}")
        sys.exit(1)


@cli.command("graph")
def export_graph() -> None:
    """Export dependency graph as Mermaid diagram."""
    config = SpecSoloistConfig.from_env()
    core = SpecSoloistCore(config=config)

    try:
        specs = core.list_specs()
        spec_names = [core.parser.get_module_name(s) for s in specs]
        graph = core.get_dependency_graph(spec_names)

        lines = ["graph TD"]
        for name in spec_names:
            deps = graph.get_dependencies(name)
            if deps:
                for dep in deps:
                    lines.append(f"    {dep} --> {name}")
            else:
                lines.append(f"    {name}")

        click.echo("\n".join(lines))
    except (CircularDependencyError, MissingDependencyError) as e:
        ui.print_error(str(e))
        sys.exit(1)


@cli.command("status")
@click.option("--json", "json_out", is_flag=True, help="JSON output")
def show_status(json_out: bool) -> None:
    """Show compilation state of each spec."""
    config = SpecSoloistConfig.from_env()
    core = SpecSoloistCore(config=config)
    specs = core.list_specs()

    status_data = {}
    for spec_path in specs:
        name = core.parser.get_module_name(spec_path)
        status_data[name] = {
            "has_implementation": core.runner.code_exists(name),
            "has_tests": core.runner.test_exists(name),
        }

    if json_out or ui.is_json_mode():
        click.echo(json.dumps(status_data))
        return

    table = ui.create_table(["Name", "Implementation", "Tests"])
    for name, status in status_data.items():
        impl = "[green]yes[/green]" if status["has_implementation"] else "[red]no[/red]"
        tests = "[green]yes[/green]" if status["has_tests"] else "[red]no[/red]"
        table.add_row(name, impl, tests)
    ui.console.print(table)


@cli.command("compile")
@click.argument("name")
@click.option("--model", default=None, help="LLM model override")
@click.option("--no-tests", is_flag=True, help="Skip test generation")
@click.option("--arrangement", "arrangement_path", default=None)
@click.option("--json", "json_out", is_flag=True)
def compile_spec(
    name: str,
    model: Optional[str],
    no_tests: bool,
    arrangement_path: Optional[str],
    json_out: bool,
) -> None:
    """Compile a single spec to code."""
    try:
        config = SpecSoloistConfig.from_env()
        if not _check_api_key(config):
            sys.exit(1)

        arrangement = _load_arrangement(arrangement_path)
        effective_model = _resolve_model(model, arrangement)

        core = SpecSoloistCore(config=config)

        # Validate first
        validation = core.validate_spec(name)
        if not validation["valid"]:
            ui.print_error(f"Spec validation failed: {', '.join(validation['errors'])}")
            sys.exit(1)

        with ui.spinner(f"Compiling {name}..."):
            code = core.compile_spec(name, model=effective_model, arrangement=arrangement)

        if not no_tests:
            with ui.spinner(f"Generating tests for {name}..."):
                core.compile_tests(name, model=effective_model, arrangement=arrangement)

        if json_out or ui.is_json_mode():
            click.echo(json.dumps({"success": True, "name": name}))
        else:
            ui.print_success(f"Compiled {name}")

    except (CircularDependencyError, MissingDependencyError) as e:
        ui.print_error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        ui.print_warning("Interrupted")
        sys.exit(130)


@cli.command("build")
@click.option("--incremental", is_flag=True, help="Only recompile changed specs")
@click.option("--parallel", is_flag=True, help="Compile independent specs concurrently")
@click.option("--workers", "max_workers", default=4, type=int)
@click.option("--model", default=None)
@click.option("--no-tests", is_flag=True)
@click.option("--arrangement", "arrangement_path", default=None)
def build_project(
    incremental: bool,
    parallel: bool,
    max_workers: int,
    model: Optional[str],
    no_tests: bool,
    arrangement_path: Optional[str],
) -> None:
    """Compile all specs in dependency order."""
    try:
        config = SpecSoloistConfig.from_env()
        if not _check_api_key(config):
            sys.exit(1)

        arrangement = _load_arrangement(arrangement_path)
        effective_model = _resolve_model(model, arrangement)

        core = SpecSoloistCore(config=config)

        with ui.spinner("Building project..."):
            result = core.compile_project(
                model=effective_model,
                generate_tests=not no_tests,
                incremental=incremental,
                parallel=parallel,
                max_workers=max_workers,
                arrangement=arrangement,
            )

        ui.print_success(f"Compiled: {len(result.specs_compiled)}")
        if result.specs_skipped:
            ui.print_info(f"Skipped: {len(result.specs_skipped)}")
        if result.specs_failed:
            ui.print_error(f"Failed: {len(result.specs_failed)}")
            for name, error in result.errors.items():
                ui.print_step(f"  {name}: {error}")
            sys.exit(1)

    except (CircularDependencyError, MissingDependencyError) as e:
        ui.print_error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        ui.print_warning("Interrupted")
        sys.exit(130)


@cli.command("test")
@click.argument("name", required=False)
@click.option("--all", "run_all", is_flag=True, help="Run tests for all specs")
def run_tests(name: Optional[str], run_all: bool) -> None:
    """Run tests for a spec."""
    config = SpecSoloistConfig.from_env()
    core = SpecSoloistCore(config=config)

    if run_all or not name:
        result = core.run_all_tests()
        if ui.is_json_mode():
            click.echo(json.dumps(result))
        else:
            for spec_name, test_result in result["results"].items():
                if test_result["success"]:
                    ui.print_success(spec_name)
                else:
                    ui.print_error(spec_name)
                    ui.console.print(test_result["output"])
        if not result["success"]:
            sys.exit(1)
    else:
        result = core.run_tests(name)
        if ui.is_json_mode():
            click.echo(json.dumps(result))
        else:
            if result["success"]:
                ui.print_success(f"Tests passed: {name}")
            else:
                ui.print_error(f"Tests failed: {name}")
                ui.console.print(result["output"])
        if not result["success"]:
            sys.exit(1)


@cli.command("fix")
@click.argument("name")
@click.option("--no-agent", is_flag=True)
@click.option("--auto-accept", is_flag=True)
@click.option("--model", default=None)
def fix_spec(name: str, no_agent: bool, auto_accept: bool, model: Optional[str]) -> None:
    """Auto-fix failing tests."""
    config = SpecSoloistConfig.from_env()
    if not _check_api_key(config):
        sys.exit(1)

    core = SpecSoloistCore(config=config)
    effective_model = _resolve_model(model)

    with ui.spinner(f"Attempting fix for {name}..."):
        result = core.attempt_fix(name, model=effective_model)

    ui.print_info(result[:200] + "..." if len(result) > 200 else result)


@cli.command("doctor")
@click.option("--arrangement", "arrangement_path", default=None)
def doctor(arrangement_path: Optional[str]) -> None:
    """Check environment health."""
    config = SpecSoloistConfig.from_env()

    # Check API keys
    provider = config.llm_provider
    key_vars = {
        "gemini": "GEMINI_API_KEY",
        "google": "GEMINI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }

    if provider in key_vars:
        key_var = key_vars[provider]
        if os.environ.get(key_var):
            ui.print_success(f"{key_var}: set")
        else:
            ui.print_warning(f"{key_var}: not set (required for {provider})")

    # Check agent CLIs
    for agent_cli in ("claude", "gemini"):
        try:
            subprocess.run(
                [agent_cli, "--version"],
                capture_output=True,
                timeout=5,
            )
            ui.print_success(f"{agent_cli}: available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            ui.print_info(f"{agent_cli}: not found (optional)")

    # Check arrangement env vars
    if arrangement_path:
        arrangement = _load_arrangement(arrangement_path)
        if arrangement and hasattr(arrangement, "env_vars") and arrangement.env_vars:
            for var_name, var_def in arrangement.env_vars.items():
                if not os.environ.get(var_name):
                    if var_def.required:
                        ui.print_warning(f"{var_name}: not set (required) — {var_def.description}")
                    else:
                        ui.print_info(f"{var_name}: not set (optional) — {var_def.description}")
                else:
                    ui.print_success(f"{var_name}: set")


@cli.command("respec")
@click.argument("file")
@click.option("--test", "test_path", default=None)
@click.option("--out", "out_path", default=None)
@click.option("--no-agent", is_flag=True)
@click.option("--model", default=None)
@click.option("--auto-accept", is_flag=True)
def respec_file(
    file: str,
    test_path: Optional[str],
    out_path: Optional[str],
    no_agent: bool,
    model: Optional[str],
    auto_accept: bool,
) -> None:
    """Reverse engineer source code to spec."""
    config = SpecSoloistConfig.from_env()
    if not _check_api_key(config):
        sys.exit(1)

    from specsoloist.respec import Respecer

    respecer = Respecer(config=config)
    effective_model = _resolve_model(model)

    try:
        result = respecer.respec(file, test_path=test_path, model=effective_model)

        if out_path:
            with open(out_path, "w") as f:
                f.write(result)
            ui.print_success(f"Spec written to {out_path}")
        else:
            click.echo(result)
    except FileNotFoundError as e:
        ui.print_error(str(e))
        sys.exit(1)


@cli.command("diff")
@click.argument("left")
@click.argument("right", required=False)
@click.option("--json", "json_out", is_flag=True)
@click.option("--label-left", default="left")
@click.option("--label-right", default="right")
@click.option("--report", "report_path", default="build/diff_report.json")
@click.option("--runs", default=0, type=int)
def diff_command(
    left: str,
    right: Optional[str],
    json_out: bool,
    label_left: str,
    label_right: str,
    report_path: str,
    runs: int,
) -> None:
    """Detect spec vs code drift or compare build directories."""
    from specsoloist.build_diff import run_diff

    if right is None:
        ui.print_error("Please provide two directories to compare")
        sys.exit(1)

    summary = run_diff(left, right, report_path, label_left, label_right)

    if json_out or ui.is_json_mode():
        import dataclasses
        data = {
            "passed": summary.passed,
            "failed": summary.failed,
            "missing_left": summary.missing_left,
            "missing_right": summary.missing_right,
        }
        click.echo(json.dumps(data))

    if summary.failed > 0 or summary.missing_left > 0 or summary.missing_right > 0:
        sys.exit(1)


@cli.command("init")
@click.argument("name", required=False)
@click.option("--arrangement", default="python")
@click.option("--template", default=None)
@click.option("--list-templates", is_flag=True)
def init_project(
    name: Optional[str],
    arrangement: str,
    template: Optional[str],
    list_templates: bool,
) -> None:
    """Scaffold a new SpecSoloist project."""
    available_templates = ["python-fasthtml", "nextjs-vitest", "nextjs-playwright"]

    if list_templates:
        for t in available_templates:
            click.echo(t)
        return

    target = name or os.getcwd()
    if name:
        os.makedirs(target, exist_ok=True)

    # Create basic structure
    for subdir in ("src", "build", "tests"):
        os.makedirs(os.path.join(target, subdir), exist_ok=True)

    ui.print_success(f"Initialized project in {target}")


@cli.command("compose")
@click.argument("request")
@click.option("--no-agent", is_flag=True)
@click.option("--auto-accept", is_flag=True)
@click.option("--model", default=None)
def compose_command(
    request: str, no_agent: bool, auto_accept: bool, model: Optional[str]
) -> None:
    """Draft architecture and specs from natural language description."""
    config = SpecSoloistConfig.from_env()
    if not _check_api_key(config):
        sys.exit(1)

    from spechestra.composer import SpecComposer

    composer = SpecComposer(project_dir=".", config=config)
    effective_model = _resolve_model(model)

    with ui.spinner("Composing architecture..."):
        result = composer.compose(request, auto_accept=auto_accept)

    if result.cancelled:
        ui.print_warning("Composition cancelled: no components generated")
        sys.exit(0)

    ui.print_success(f"Created {len(result.spec_paths)} specs")
    for path in result.spec_paths:
        ui.print_step(path)


@cli.command("conduct")
@click.argument("src_dir", required=False, default="src")
@click.option("--no-agent", is_flag=True)
@click.option("--auto-accept", is_flag=True)
@click.option("--incremental", is_flag=True)
@click.option("--parallel", is_flag=True)
@click.option("--workers", "max_workers", default=4)
@click.option("--model", default=None)
@click.option("--arrangement", "arrangement_path", default=None)
@click.option("--resume", is_flag=True)
@click.option("--force", is_flag=True)
def conduct_command(
    src_dir: str,
    no_agent: bool,
    auto_accept: bool,
    incremental: bool,
    parallel: bool,
    max_workers: int,
    model: Optional[str],
    arrangement_path: Optional[str],
    resume: bool,
    force: bool,
) -> None:
    """Orchestrate project build."""
    config = SpecSoloistConfig.from_env()
    if not _check_api_key(config):
        sys.exit(1)

    arrangement = _load_arrangement(arrangement_path)
    effective_model = _resolve_model(model, arrangement)

    # --force overrides incremental
    if force:
        incremental = False
    elif resume:
        incremental = True

    config.src_dir = src_dir
    config.src_path = os.path.abspath(src_dir)

    core = SpecSoloistCore(config=config)

    try:
        with ui.spinner("Conducting build..."):
            result = core.compile_project(
                model=effective_model,
                generate_tests=True,
                incremental=incremental,
                parallel=parallel,
                max_workers=max_workers,
                arrangement=arrangement,
            )

        ui.print_success(f"Compiled: {len(result.specs_compiled)}")
        if result.specs_skipped:
            ui.print_info(f"Skipped: {len(result.specs_skipped)}")
        if result.specs_failed:
            ui.print_error(f"Failed: {len(result.specs_failed)}")
            sys.exit(1)

    except (CircularDependencyError, MissingDependencyError) as e:
        ui.print_error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        ui.print_warning("Interrupted")
        sys.exit(130)


def main() -> None:
    """Entry point for the sp CLI."""
    try:
        cli(standalone_mode=True)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        ui.print_warning("Interrupted")
        sys.exit(130)


if __name__ == "__main__":
    main()
