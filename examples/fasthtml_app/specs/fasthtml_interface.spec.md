---
name: fasthtml_interface
type: reference
status: stable
---

# Overview

The subset of [FastHTML](https://fastht.ml) used in this project (`python-fasthtml >= 0.12`).
This spec exists so soloists have accurate API documentation — FastHTML is new enough that LLMs
may hallucinate its API.

Specs that depend on FastHTML components should list `fasthtml_interface` as a dependency.
No implementation is generated for this spec — it is API documentation only.

**Critical import:** Always import from `fasthtml.common`, never from `fasthtml` directly:
```python
from fasthtml.common import fast_app, serve, Div, P, H1, Form, Input, Button, Title, Ul, Li
```

**Testing:** Use `from starlette.testclient import TestClient`. Never call `serve()` in test files —
guard with `if __name__ == "__main__": serve()`.

# API

## fast_app()

Creates the FastHTML ASGI app and route decorator.

```python
app, rt = fast_app()
```

Returns a tuple `(app, rt)` where `app` is the ASGI application and `rt` is a route decorator factory.

## serve()

Starts the development server on `localhost:5001`. **Never call in test files.**

## HTML components

All HTML components share this signature: `Tag(*children, **attrs)`.

| Component | HTML element | Notes |
|-----------|-------------|-------|
| `Div` | `<div>` | General container |
| `P` | `<p>` | Paragraph |
| `H1` | `<h1>` | Heading |
| `Form` | `<form>` | Use `hx_post`, `hx_swap`, `hx_target` for HTMX |
| `Input` | `<input>` | `name=` delivers form field to route handler |
| `Button` | `<button>` | Submit button |
| `Title` | `<title>` | Page title in head |
| `Ul` | `<ul>` | Unordered list |
| `Li` | `<li>` | List item |

## Route registration

```python
app, rt = fast_app()

@rt("/")
def get():
    return Div(H1("Hello"), P("World"))

@rt("/todos")
def post(item: str):   # form field 'item' injected as keyword arg
    return Li(item)
```

Route handlers return HTML components directly. FastHTML serialises them to HTML strings.
To return multiple top-level elements, return a tuple: `return H1("Title"), P("Body")`.

## HTMX attributes on Form

```python
Form(
    Input(name="item", placeholder="Add todo"),
    Button("Add"),
    hx_post="/todos",
    hx_swap="beforeend",
    hx_target="#todo-list",
)
```

## Starlette test client

```python
from starlette.testclient import TestClient
client = TestClient(app)
response = client.get("/")
assert response.status_code == 200
assert "<ul" in response.text
```

# Verification

```python
from fasthtml.common import fast_app, serve, Div, P, H1, Form, Input, Button, Title, Ul, Li
app, rt = fast_app()
assert callable(rt)
div = Div("hello", id="x")
assert "hello" in str(div)
form = Form(Input(name="item"), Button("Add"), hx_post="/add", hx_swap="beforeend")
assert "hx-post" in str(form)
```
