---
name: fasthtml_interface
type: type
status: stable
---

# FastHTML Interface Contract

The subset of [FastHTML](https://fastht.ml) used in this project. This spec exists so soloists
have accurate API documentation — FastHTML is new enough that LLMs may hallucinate its API.

Specs that import FastHTML components should list `fasthtml_interface` as a dependency.

## HTML Components

All components accept keyword attribute arguments (`**attrs`) and positional child arguments
(`*children`). They return HTMX-aware HTML elements.

- `Div(**attrs, *children)` — renders a `<div>`
- `P(**attrs, *children)` — renders a `<p>`
- `H1(**attrs, *children)` — renders an `<h1>`
- `Form(hx_post, hx_swap, hx_target, **attrs, *children)` — HTMX-enabled form; `hx_post` is
  the POST endpoint, `hx_swap` controls how the response is inserted, `hx_target` selects
  the DOM element to update
- `Input(name, type="text", placeholder="", **attrs)` — form input field
- `Button(*children, **attrs)` — submit button

Common `hx_swap` values: `"innerHTML"`, `"outerHTML"`, `"beforeend"`, `"afterbegin"`.

## Application

- `app, rt = fast_app()` — creates the FastHTML app instance and route decorator
- `@rt(path)` — decorator that registers a route handler; the decorated function receives
  request data as keyword arguments matching form field names
- `serve()` — starts the development server on `localhost:5001`

## Returning Responses

Route handlers return HTML components directly. FastHTML serialises them to HTML strings.
To return multiple elements, return a tuple: `return H1("Title"), P("Body")`.
