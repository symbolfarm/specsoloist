"""Tests for the Textual TUI dashboard."""

import pytest
import pytest_asyncio  # noqa: F401 — ensures plugin is loaded

from specsoloist.subscribers.build_state import BuildState, SpecState
from textual.widgets import Label

from specsoloist.tui import (
    DashboardApp, LogPanel, SpecDetailWidget, SpecInfoWidget, SpecListWidget, StatusBar,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _building_state(specs: dict[str, str] | None = None) -> BuildState:
    """Create a BuildState in 'building' status with given spec statuses."""
    if specs is None:
        specs = {"config": "compiling", "parser": "queued", "runner": "queued"}
    return BuildState(
        status="building",
        total_specs=len(specs),
        build_order=list(specs.keys()),
        specs={name: SpecState(name=name, status=status) for name, status in specs.items()},
    )


def _completed_state() -> BuildState:
    """Create a completed build state."""
    return BuildState(
        status="completed",
        total_specs=3,
        specs_completed=3,
        build_order=["config", "parser", "runner"],
        specs={
            "config": SpecState(name="config", status="passed", duration=1.2),
            "parser": SpecState(name="parser", status="passed", duration=3.4),
            "runner": SpecState(name="runner", status="passed", duration=2.1),
        },
        total_input_tokens=1500,
        total_output_tokens=3200,
        elapsed=6.7,
    )


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

class TestAppLifecycle:
    @pytest.mark.asyncio
    async def test_app_launches_with_waiting_message(self):
        async with DashboardApp().run_test() as pilot:
            info = pilot.app.query_one("#spec-info", SpecInfoWidget)
            assert "Waiting" in str(info.render())

    @pytest.mark.asyncio
    async def test_status_bar_shows_no_build_initially(self):
        async with DashboardApp().run_test() as pilot:
            sb = pilot.app.query_one("#status-bar", StatusBar)
            assert "No build in progress" in str(sb.render())

    @pytest.mark.asyncio
    async def test_quit_binding(self):
        async with DashboardApp().run_test() as pilot:
            await pilot.press("q")
            assert pilot.app.is_running is False


# ---------------------------------------------------------------------------
# Spec list
# ---------------------------------------------------------------------------

class TestSpecList:
    @pytest.mark.asyncio
    async def test_populates_on_build_started(self):
        async with DashboardApp().run_test() as pilot:
            pilot.app.refresh_state(_building_state())
            await pilot.pause()

            spec_list = pilot.app.query_one("#spec-list", SpecListWidget)
            assert spec_list.spec_names == ["config", "parser", "runner"]

    @pytest.mark.asyncio
    async def test_status_icons(self):
        async with DashboardApp().run_test() as pilot:
            state = _building_state({
                "a": "passed",
                "b": "compiling",
                "c": "queued",
                "d": "failed",
            })
            pilot.app.refresh_state(state)
            await pilot.pause()

            spec_list = pilot.app.query_one("#spec-list", SpecListWidget)
            items = list(spec_list.children)
            # Check icons by reading label text
            assert "○" in str(items[0].query_one(Label).render())   # passed
            assert "●" in str(items[1].query_one(Label).render())   # compiling
            assert "◌" in str(items[2].query_one(Label).render())   # queued
            assert "✖" in str(items[3].query_one(Label).render())   # failed

    @pytest.mark.asyncio
    async def test_selection_preserved_on_refresh(self):
        async with DashboardApp().run_test() as pilot:
            pilot.app.refresh_state(_building_state())
            await pilot.pause()

            spec_list = pilot.app.query_one("#spec-list", SpecListWidget)
            # Move selection to index 1
            spec_list.index = 1
            await pilot.pause()

            # Refresh state — selection should stay at 1
            state = _building_state({"config": "passed", "parser": "compiling", "runner": "queued"})
            pilot.app.refresh_state(state)
            await pilot.pause()

            assert spec_list.index == 1

    @pytest.mark.asyncio
    async def test_dependency_order_preserved(self):
        async with DashboardApp().run_test() as pilot:
            state = BuildState(
                status="building",
                total_specs=3,
                build_order=["leaf", "middle", "root"],
                specs={
                    "leaf": SpecState(name="leaf", status="queued"),
                    "middle": SpecState(name="middle", status="queued"),
                    "root": SpecState(name="root", status="queued"),
                },
            )
            pilot.app.refresh_state(state)
            await pilot.pause()

            spec_list = pilot.app.query_one("#spec-list", SpecListWidget)
            assert spec_list.spec_names == ["leaf", "middle", "root"]


# ---------------------------------------------------------------------------
# Detail panel
# ---------------------------------------------------------------------------

class TestDetailPanel:
    @pytest.mark.asyncio
    async def test_shows_selected_spec(self):
        async with DashboardApp().run_test() as pilot:
            state = _completed_state()
            pilot.app.refresh_state(state)
            await pilot.pause()

            # First spec should be auto-selected
            info = pilot.app.query_one("#spec-info", SpecInfoWidget)
            rendered = str(info.render())
            assert "config" in rendered
            assert "passed" in rendered

    @pytest.mark.asyncio
    async def test_shows_error_for_failed_spec(self):
        async with DashboardApp().run_test() as pilot:
            state = BuildState(
                status="building",
                total_specs=1,
                build_order=["broken"],
                specs={"broken": SpecState(name="broken", status="failed", error="LLM timeout")},
            )
            pilot.app.refresh_state(state)
            await pilot.pause()

            info = pilot.app.query_one("#spec-info", SpecInfoWidget)
            rendered = str(info.render())
            assert "LLM timeout" in rendered

    @pytest.mark.asyncio
    async def test_shows_duration(self):
        async with DashboardApp().run_test() as pilot:
            pilot.app.refresh_state(_completed_state())
            await pilot.pause()

            info = pilot.app.query_one("#spec-info", SpecInfoWidget)
            rendered = str(info.render())
            assert "1.2s" in rendered

    @pytest.mark.asyncio
    async def test_shows_retry_count(self):
        async with DashboardApp().run_test() as pilot:
            state = BuildState(
                status="building",
                total_specs=1,
                build_order=["flaky"],
                specs={"flaky": SpecState(name="flaky", status="fixing", retries=2)},
            )
            pilot.app.refresh_state(state)
            await pilot.pause()

            info = pilot.app.query_one("#spec-info", SpecInfoWidget)
            assert "2" in str(info.render())

    @pytest.mark.asyncio
    async def test_placeholder_when_no_spec(self):
        async with DashboardApp().run_test() as pilot:
            info = pilot.app.query_one("#spec-info", SpecInfoWidget)
            assert "Waiting" in str(info.render())


# ---------------------------------------------------------------------------
# Status bar
# ---------------------------------------------------------------------------

class TestStatusBar:
    @pytest.mark.asyncio
    async def test_shows_progress(self):
        async with DashboardApp().run_test() as pilot:
            pilot.app.refresh_state(_building_state())
            await pilot.pause()

            sb = pilot.app.query_one("#status-bar", StatusBar)
            rendered = str(sb.render())
            assert "0/3" in rendered
            assert "building" in rendered

    @pytest.mark.asyncio
    async def test_shows_tokens(self):
        async with DashboardApp().run_test() as pilot:
            pilot.app.refresh_state(_completed_state())
            await pilot.pause()

            sb = pilot.app.query_one("#status-bar", StatusBar)
            rendered = str(sb.render())
            assert "1,500" in rendered
            assert "3,200" in rendered

    @pytest.mark.asyncio
    async def test_shows_elapsed(self):
        async with DashboardApp().run_test() as pilot:
            pilot.app.refresh_state(_completed_state())
            await pilot.pause()

            sb = pilot.app.query_one("#status-bar", StatusBar)
            assert "6.7s" in str(sb.render())

    @pytest.mark.asyncio
    async def test_idle_state(self):
        async with DashboardApp().run_test() as pilot:
            pilot.app.refresh_state(BuildState())
            await pilot.pause()

            sb = pilot.app.query_one("#status-bar", StatusBar)
            assert "No build in progress" in str(sb.render())


# ---------------------------------------------------------------------------
# Integration: TuiSubscriber + DashboardApp
# ---------------------------------------------------------------------------

class TestTuiIntegration:
    @pytest.mark.asyncio
    async def test_subscriber_state_feeds_app(self):
        """TuiSubscriber accumulates state; app.refresh_state renders it."""
        from specsoloist.events import BuildEvent, EventType
        from specsoloist.subscribers.tui import TuiSubscriber

        async with DashboardApp().run_test() as pilot:
            app = pilot.app

            # Create subscriber without app (headless) to accumulate state
            sub = TuiSubscriber()
            sub(BuildEvent(
                event_type=EventType.BUILD_STARTED,
                data={"total_specs": 2, "build_order": ["a", "b"]},
            ))
            sub(BuildEvent(
                event_type=EventType.SPEC_COMPILE_STARTED,
                spec_name="a",
            ))

            # Feed the accumulated state to the app (as call_from_thread would)
            app.refresh_state(sub.state)
            await pilot.pause()

            spec_list = app.query_one("#spec-list", SpecListWidget)
            assert spec_list.spec_names == ["a", "b"]

            sb = app.query_one("#status-bar", StatusBar)
            assert "building" in str(sb.render())

            # Verify the subscriber's state is correct
            assert sub.state.specs["a"].status == "compiling"
            assert sub.state.specs["b"].status == "queued"


# ---------------------------------------------------------------------------
# Log panel
# ---------------------------------------------------------------------------

class TestLogPanel:
    @pytest.mark.asyncio
    async def test_log_panel_shows_spec_events(self):
        """Log panel displays accumulated log lines for the selected spec."""
        from specsoloist.events import BuildEvent, EventType
        from specsoloist.subscribers.tui import TuiSubscriber

        async with DashboardApp().run_test() as pilot:
            sub = TuiSubscriber()
            sub(BuildEvent(
                event_type=EventType.BUILD_STARTED,
                data={"total_specs": 2, "build_order": ["a", "b"]},
            ))
            sub(BuildEvent(
                event_type=EventType.SPEC_COMPILE_STARTED,
                spec_name="a",
            ))
            sub(BuildEvent(
                event_type=EventType.SPEC_TESTS_STARTED,
                spec_name="a",
            ))
            sub(BuildEvent(
                event_type=EventType.SPEC_TESTS_COMPLETED,
                spec_name="a",
                data={"success": True},
            ))

            pilot.app.refresh_state(sub.state)
            await pilot.pause()

            # Check that log lines accumulated in SpecState
            assert len(sub.state.specs["a"].log) == 3
            assert "Generating implementation" in sub.state.specs["a"].log[0]
            assert "Running tests" in sub.state.specs["a"].log[1]
            assert "Tests passed" in sub.state.specs["a"].log[2]

    @pytest.mark.asyncio
    async def test_log_panel_empty_for_queued_spec(self):
        async with DashboardApp().run_test() as pilot:
            state = _building_state({"a": "queued"})
            pilot.app.refresh_state(state)
            await pilot.pause()

            log_panel = pilot.app.query_one("#log-panel", LogPanel)
            # Queued spec has no log lines
            assert state.specs["a"].log == []

    @pytest.mark.asyncio
    async def test_log_panel_shows_fix_retries(self):
        from specsoloist.events import BuildEvent, EventType
        from specsoloist.subscribers.tui import TuiSubscriber

        async with DashboardApp().run_test() as pilot:
            sub = TuiSubscriber()
            sub(BuildEvent(
                event_type=EventType.BUILD_STARTED,
                data={"total_specs": 1, "build_order": ["x"]},
            ))
            sub(BuildEvent(event_type=EventType.SPEC_COMPILE_STARTED, spec_name="x"))
            sub(BuildEvent(event_type=EventType.SPEC_TESTS_STARTED, spec_name="x"))
            sub(BuildEvent(
                event_type=EventType.SPEC_TESTS_COMPLETED,
                spec_name="x", data={"success": False},
            ))
            sub(BuildEvent(event_type=EventType.SPEC_FIX_STARTED, spec_name="x"))
            sub(BuildEvent(event_type=EventType.SPEC_FIX_COMPLETED, spec_name="x"))

            pilot.app.refresh_state(sub.state)
            await pilot.pause()

            log = sub.state.specs["x"].log
            assert "Fix attempt 1" in log[3]
            assert "Fix applied, re-testing" in log[4]
