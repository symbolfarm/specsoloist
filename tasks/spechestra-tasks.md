# Spechestra — Initial Task Backlog

> These tasks are for the `symbolfarm/spechestra` repository (separate from specsoloist).
> Copy to `spechestra/tasks/` and adapt to that repo's structure.
>
> Spechestra depends on specsoloist as a Python dependency (editable install for local dev).
> The SSE server (specsoloist task 32) is the integration point — Spechestra connects to it.

---

## S-01: Project scaffold and arrangement

**Effort**: Small

### What

Set up the Spechestra repository as a FastHTML web application:

- `pyproject.toml` with `specsoloist` as a dependency
- `arrangement.yaml` for the project
- FastHTML app skeleton (single `app.py` or modular layout)
- `uv` as the package manager (matching specsoloist)
- Basic development instructions in README

### Stack

- **FastHTML** — Python web framework (SSE-native via HTMX)
- **HTMX** — declarative real-time updates (SSE extension: `hx-ext="sse"`)
- **fastlite** or **SQLite** — local persistence for build history
- **Pico CSS** or **Simple.css** — minimal styling (no build step)

### Success Criteria

- `uv run python app.py` starts a web server
- Browser shows a placeholder page
- `specsoloist` is importable from within the project

---

## S-02: SSE client — connect to sp conduct

**Effort**: Small

**Depends on**: specsoloist task 32, S-01

### What

The dashboard connects to `sp conduct --serve` and receives build events in real time.

- `EventSource` (JavaScript) connects to `localhost:4510/events`
- HTMX SSE extension receives events and swaps DOM elements
- Fallback: poll `GET /status` if SSE connection fails
- Connection status indicator (connected/disconnected/reconnecting)

### Key Design Choice

The browser connects directly to specsoloist's SSE endpoint — Spechestra does NOT proxy
events. This keeps the architecture simple: specsoloist serves events, Spechestra renders UI.

### Success Criteria

- Start `sp conduct --serve` in one terminal
- Open Spechestra dashboard in browser
- Events appear in real time as the build progresses

---

## S-03: Build monitor view

**Effort**: Medium

**Depends on**: S-02

### What

The core dashboard view — a real-time visualization of a running build.

**Components:**
- **Dependency graph** — rendered from `sp graph --json` output or `GET /status` response.
  Nodes colored by status (queued/compiling/testing/passed/failed). Use a simple grid/list
  layout for v1; upgrade to an actual graph visualization later.
- **Spec status cards** — one per spec, showing name, status, duration, token count. Cards
  update in real-time via SSE → HTMX swap.
- **Log panel** — click a spec card to see its compilation log. Scrollable, auto-follows.
- **Aggregate stats bar** — total tokens, estimated cost, progress (N/M specs), elapsed time.

### HTMX Pattern

```html
<!-- SSE updates swap individual spec cards -->
<div hx-ext="sse" sse-connect="/events">
  <div sse-swap="spec.compile.started" hx-target="#spec-{name}">
    <!-- server renders updated card HTML -->
  </div>
</div>
```

The FastHTML server renders HTML fragments in response to SSE events — no client-side
JavaScript framework needed.

### Success Criteria

- Build progress is visible in real time
- Spec cards transition through status states
- Token costs accumulate
- Clicking a spec shows its log

---

## S-04: Build history and persistence

**Effort**: Medium

**Depends on**: S-03

### What

Store completed builds in a local database so users can review past runs.

- Each build run gets a row: timestamp, arrangement path, pass/fail counts, total tokens,
  duration, per-spec results (JSON blob or normalized)
- History list view: table of past builds, sorted by recency
- Build detail view: same as the monitor view but replaying stored events
- Diff between runs: which specs changed status (passed → failed, new, removed)

### Persistence

Use `fastlite` (SQLite wrapper) — matches the FastHTML stack and is already proven in
specsoloist's FastHTML examples.

### Success Criteria

- Completed builds appear in history
- Clicking a past build shows its detail view
- Two builds can be compared

---

## S-05: Auth and team management (future)

**Effort**: Large

**Depends on**: S-04

### What

Multi-user support for teams. This is where the commercial value starts.

- User accounts (email/password or OAuth)
- Projects: a user can have multiple specsoloist projects
- Team: invite collaborators to view/manage builds
- RBAC: viewer (see builds) vs editor (trigger builds, edit specs)
- API keys for CI integration (webhook receiver for remote builds)

### Open Questions (defer until S-04 is done)

- Session-based auth (FastHTML default) or JWT?
- Self-hosted vs cloud-only for team features?
- Pricing model: per-seat, per-build, or usage-based?

### Success Criteria

- Multiple users can log in
- Users see only their own projects
- Team invites work
