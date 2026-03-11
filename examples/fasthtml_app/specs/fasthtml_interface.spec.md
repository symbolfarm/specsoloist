---
name: fasthtml_interface
type: bundle
status: stable
---

# Overview

The subset of [FastHTML](https://fastht.ml) used in this project. This spec exists so soloists
have accurate API documentation — FastHTML is new enough that LLMs may hallucinate its API.

Specs that import FastHTML components should list `fasthtml_interface` as a dependency.

**Critical import:** Always import from `fasthtml.common`, never from `fasthtml` directly:
```python
from fasthtml.common import fast_app, serve, Div, P, H1, Form, Input, Button, Title, Ul, Li
```

**Testing:** Use `from starlette.testclient import TestClient`. Never call `serve()` in test files —
guard with `if __name__ == "__main__": serve()`.

# Functions

```yaml:functions
fast_app:
  inputs: {}
  outputs:
    result: {type: object, description: "Tuple (app, rt) — ASGI app and route decorator factory"}
  behavior: "Creates the FastHTML ASGI app and route decorator. Use as: app, rt = fast_app()"

serve:
  inputs: {}
  outputs: {}
  behavior: "Starts the development server on localhost:5001. Never call in test files."

Div:
  inputs:
    children: {type: array, description: "Positional child elements"}
    attrs: {type: object, description: "HTML attribute keyword arguments"}
  outputs:
    result: {type: object, description: "HTMX-aware HTML element"}
  behavior: "Renders a <div> element. All HTML components share this signature."

P:
  inputs:
    children: {type: array}
    attrs: {type: object}
  outputs:
    result: {type: object}
  behavior: "Renders a <p> element."

H1:
  inputs:
    children: {type: array}
    attrs: {type: object}
  outputs:
    result: {type: object}
  behavior: "Renders an <h1> element."

Form:
  inputs:
    children: {type: array}
    hx_post: {type: string, description: "POST endpoint URL for HTMX"}
    hx_swap: {type: string, description: "HTMX swap mode: innerHTML, outerHTML, beforeend, afterbegin"}
    hx_target: {type: string, description: "CSS selector for the DOM element to update"}
    attrs: {type: object}
  outputs:
    result: {type: object}
  behavior: "Renders an HTMX-enabled <form>. hx_post, hx_swap, hx_target are keyword args."

Input:
  inputs:
    name: {type: string, description: "Form field name delivered to the route handler"}
    type: {type: string, description: "Input type, default text"}
    placeholder: {type: string}
    attrs: {type: object}
  outputs:
    result: {type: object}
  behavior: "Renders a form <input> field."

Button:
  inputs:
    children: {type: array}
    attrs: {type: object}
  outputs:
    result: {type: object}
  behavior: "Renders a <button> element."

Title:
  inputs:
    children: {type: array}
    attrs: {type: object}
  outputs:
    result: {type: object}
  behavior: "Renders a <title> element for the page head."

Ul:
  inputs:
    children: {type: array}
    attrs: {type: object}
  outputs:
    result: {type: object}
  behavior: "Renders a <ul> element."

Li:
  inputs:
    children: {type: array}
    attrs: {type: object}
  outputs:
    result: {type: object}
  behavior: "Renders a <li> element."
```

# Behavior

## Returning responses from route handlers

Route handlers return HTML components directly. FastHTML serialises them to HTML strings.
To return multiple top-level elements, return a tuple: `return H1("Title"), P("Body")`.

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

## Starlette test client

```python
from starlette.testclient import TestClient
client = TestClient(app)
response = client.get("/")
assert response.status_code == 200
assert "<ul" in response.text
```
