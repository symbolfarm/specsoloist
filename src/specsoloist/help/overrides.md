# output_paths.overrides Reference

`output_paths.overrides` lets you route specific specs to exact file paths, overriding
the default `{name}` / `{path}` template. This is essential for frameworks with strict
file naming conventions (e.g. Next.js App Router, FastHTML route files).

---

## Syntax

```yaml
output_paths:
  implementation: src/{name}.ts        # default template
  tests: tests/{name}.test.ts          # default template
  overrides:
    <spec-name>:
      implementation: <exact-path>     # optional
      tests: <exact-path>              # optional
```

- Key is the spec name exactly as it appears in frontmatter (without `.spec.md`).
- Either `implementation` or `tests` may be omitted; the omitted field falls back to
  the default template.
- Override paths are literal strings — `{name}` is NOT expanded in override paths.

---

## Example: Next.js API routes

```yaml
output_paths:
  implementation: src/{name}.ts
  tests: tests/{name}.test.ts
  overrides:
    chat_route:
      implementation: src/app/api/chat/route.ts
    auth_route:
      implementation: src/app/api/auth/[...nextauth]/route.ts
      tests: tests/auth_route.test.ts
    middleware:
      implementation: src/middleware.ts
```

In this example:
- `chat_route` lands at `src/app/api/chat/route.ts`; its tests use the default
  template → `tests/chat_route.test.ts`.
- `auth_route` overrides both paths.
- `middleware` overrides only implementation; tests use the default.
- All other specs use the `src/{name}.ts` / `tests/{name}.test.ts` templates.

---

## Example: Python submodules

**Tip**: Use `{path}` in the default template to avoid overrides for specs in
subdirectories. `{path}` includes the subdirectory prefix; `{name}` is just the leaf.

```yaml
output_paths:
  implementation: src/myapp/{path}.py    # subscribers/ndjson → src/myapp/subscribers/ndjson.py
  tests: tests/test_{name}.py           # subscribers/ndjson → tests/test_ndjson.py
  overrides:
    middleware:
      implementation: src/myapp/http/middleware.py  # different target package
```

---

## Checking overrides

`sp schema output_paths` shows the overrides field structure.

After building, `sp status` shows whether each spec's output files were found.

---

## See also

- `sp help arrangement` — full arrangement.yaml reference
- `sp schema output_paths` — annotated schema for the output_paths section
