# Decision: What Does "Language-Agnostic" Mean at the UI Layer?

**Status:** Decided
**Raised:** 2026-03-12

---

## The Tension

SpecSoloist specs are described as "language-agnostic" — a `state.spec.md` describing
`add_todo(item: str) -> int` could be compiled to Python, Go, or TypeScript equally
well. But once you're writing UI specs for a web application, the browser is the
runtime, and its constraints are real:

- HTML element names (`Ul`, `Li`, `Main`) appear in return types
- HTMX attributes (`hx_delete`, `hx_swap="outerHTML"`) describe UX behaviour
- CSS framework classes (`cls="container"`) are part of the visual contract

Are these violations of the language-agnostic principle? Should we abstract over them?

---

## Analysis

Web applications have distinct layers with different agnosticism properties:

| Layer | Agnostic? | Where captured |
|-------|-----------|----------------|
| Data / state | ✅ fully language-agnostic | spec |
| HTTP routes / API contracts | ✅ mostly agnostic | spec |
| UI components | ❌ browser-coupled, framework-specific | spec + reference spec |
| Styling | ❌ CSS-framework-specific | arrangement constraints + reference spec |

The "language-agnostic" principle was designed to separate *business logic* from
*implementation language*. At the UI layer, the browser replaces the programming
language as the target runtime — and HTML/CSS/HTMX are its "language."

Crucially, the separation of concerns still holds:
- The **spec** describes the browser-facing contract (what HTML structure is produced,
  what HTMX interactions are present)
- The **arrangement** captures the framework choice (`target_language: python`,
  dependency versions)
- The **reference spec** (`fasthtml_interface`, `tailwind`, etc.) documents the
  framework-specific API that soloists use to produce that output

The framework is decoupled from the spec. A `layout.spec.md` describing a todo list
with a delete button and HTMX swap behaviour could be compiled with FastHTML (Python)
or a React/Next.js component — both produce the same browser-facing contract.

---

## Decision

**"Language-agnostic" should be understood as "language-agnostic at the business logic
layer." At the UI layer, specs describe browser-facing contracts.**

The refined principle:

> *Specs are agnostic about the implementation language and framework. At the UI layer,
> they describe what the browser receives (HTML structure, HTTP behaviour, interactive
> attributes) — not how any particular framework produces it. The arrangement and
> reference specs capture the framework mapping.*

This means:

- HTML element semantics in spec return types are fine (`returns an Li`, `returns a Form`)
- HTMX interaction patterns in specs are fine — HTMX is a browser-level protocol, not
  a framework
- Framework-specific identifiers should stay in the arrangement and reference specs,
  not leak into business logic specs (e.g. `picolink` belongs in the arrangement
  constraints and `fasthtml_interface` reference spec, not in `routes.spec.md`)

---

## What Needs Updating

This decision should eventually be reflected in:

- `score/spec_format.spec.md` — clarify the language-agnostic principle with a note
  about the UI layer
- `README.md` — user documentation on writing specs for web apps
- A future "Writing Web App Specs" guide in `docs/` (once docs/ exists)

No code or spec changes are required now. The FastHTML example is a reasonable
expression of this pattern — the slight leak of `picolink` into `routes.spec.md` is
minor and acceptable.
