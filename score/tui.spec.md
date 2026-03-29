---
name: tui
type: bundle
dependencies:
  - from: subscribers/build_state.spec.md
tags:
  - observability
  - ui
---

# Overview

Terminal dashboard for SpecSoloist builds, built on the Textual framework. Displays a live view of build progress: a navigable spec list with status icons, a detail panel for the selected spec, and an aggregate status bar.

The dashboard is read-only — it observes builds but does not control them. State comes from a `BuildState` object updated by `TuiSubscriber` via `refresh_state()`.

The app runs in two modes (transparent to the Textual code):
- **In-process**: `sp conduct --tui` runs the build in a background thread; events flow through an in-process `EventBus`
- **Remote**: `sp dashboard` connects to an SSE endpoint and reconstructs state from events (future, task 32)

# Types

## DashboardApp

Textual `App` subclass. The main application.

**Behavior:**
- On mount, displays a "Waiting for build..." message until `refresh_state()` is called
- Layout: two-column with a spec list on the left and detail panel on the right, plus a status bar at the bottom
- Keyboard: `q` quits the app
- Provides `refresh_state(state: BuildState)` method that updates all widgets with new state
- When the build status becomes `"completed"` or `"failed"`, the app remains open (user reviews results, then presses `q`)

## SpecListWidget

Left panel. Renders the spec list from `BuildState` in dependency order.

**Behavior:**
- Each spec shows a status icon and the spec name
- Status icons: `○` passed, `●` compiling/testing/fixing (in progress), `◌` queued, `✖` failed
- The list is navigable with arrow keys (up/down)
- The currently selected spec is highlighted
- Selecting a spec updates the detail panel
- When state updates arrive, the list re-renders preserving the current selection

## SpecDetailWidget

Right panel. A vertical container holding a `SpecInfoWidget` (metadata) and a `LogPanel` (scrollable event log).

**Behavior:**
- Updates when selection changes or when state refreshes
- Delegates to child widgets for rendering

## SpecInfoWidget

Top portion of the detail panel. Displays spec metadata.

**Behavior:**
- Displays: spec name (bold), status with icon, duration (if available), retry count, token counts, error message (if any, in red)
- When no spec is selected, shows a placeholder message

## LogPanel

Scrollable log of events for the selected spec. Extends `RichLog`.

**Behavior:**
- Shows the accumulated `log` lines from the selected `SpecState`
- `set_log(lines)` replaces the log content (clears and re-writes all lines)
- Scrolls automatically to show the latest entries

## StatusBar

Bottom bar. Shows aggregate build statistics.

**Behavior:**
- Displays: total input/output tokens, progress (completed/total specs), elapsed time, build status
- When idle (no build), shows "No build in progress"
- Updates on each `refresh_state()` call

# Functions

## DashboardApp.refresh_state(state)

Update the dashboard with a new `BuildState` snapshot. Called from `TuiSubscriber` via `call_from_thread()` (thread-safe — Textual guarantees this runs on the UI thread).

Updates all child widgets: spec list, detail panel, and status bar.

## DashboardApp.on_spec_selected(spec_name)

Handle spec selection from the spec list. Updates the detail panel to show the selected spec's state.

# Examples

```python
from specsoloist.tui import DashboardApp
from specsoloist.subscribers.build_state import BuildState, SpecState

# Headless test via Textual's run_test()
async with DashboardApp().run_test() as pilot:
    # Initially shows waiting message
    app = pilot.app
    assert "Waiting" in app.query_one("StatusBar").renderable_text

    # Feed a build state
    state = BuildState(
        status="building",
        total_specs=2,
        build_order=["config", "parser"],
        specs={
            "config": SpecState(name="config", status="compiling"),
            "parser": SpecState(name="parser", status="queued"),
        },
    )
    app.refresh_state(state)
    await pilot.pause()

    # Spec list now shows both specs
    spec_list = app.query_one("SpecListWidget")
    assert len(spec_list.spec_names) == 2
```

# Verification

```python
from specsoloist.tui import DashboardApp

# App class exists and is a Textual App
from textual.app import App
assert issubclass(DashboardApp, App)

# refresh_state method exists
assert callable(getattr(DashboardApp, "refresh_state", None))
```

# Constraints

- Requires `textual>=1.0` as a runtime dependency
- The `tui` module is the only module that imports Textual — all other modules (build_state, tui subscriber) remain Textual-free
- Must work in headless mode via `app.run_test()` for CI (no terminal required)
- Selection state (which spec is highlighted) must survive `refresh_state()` calls — the list should not jump back to the top on every update
- Status icons must be distinguishable in monochrome terminals (different Unicode characters, not just color)
