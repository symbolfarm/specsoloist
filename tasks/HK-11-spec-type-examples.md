# HK-11: Add Spec Type Examples and Improve docs/reference/template.md

## Problem

`docs/reference/template.md` shows only a single blank `bundle` template. Users have no
way to understand what the other spec types look like or when to use each one. Key gaps:

- `function`, `type`, `module`, `workflow`, and `reference` types are not shown
- `type: reference` (Phase 8) has specific required sections and conventions that are
  completely undocumented
- `docs/examples/` pages are empty stubs with a dead link to a nonexistent repo path

## Approach

Use the MkDocs `snippets` extension (already configured in `mkdocs.yml`) to **embed
real files from `score/`** as examples rather than writing synthetic snippets that will
drift. This keeps examples permanently in sync with reality.

## Steps

1. **Rename/rewrite `docs/reference/template.md` → `docs/reference/spec-types.md`**
   - One section per type with: purpose, when to use, embedded example from `score/`
   - Suggested examples to embed (trim to relevant sections if files are long):
     - `bundle`: embed `score/config.spec.md` (clean, self-contained)
     - `function`: embed `score/compiler.spec.md` or similar
     - `type`: embed a type-only spec if one exists, otherwise show a trimmed excerpt
     - `module`: embed `score/parser.spec.md` (good module example)
     - `workflow`: embed `score/conductor.spec.md` or similar workflow spec
     - `reference`: embed one of the reference specs from `examples/fasthtml_app/` or
       `examples/nextjs_ai_chat/` (e.g. `fasthtml_interface.spec.md`)
   - Add `reference` type section explaining: no code generated, required sections
     (`# Overview`, `# API`, `# Verification`), verification snippets compiled to tests,
     `sp validate` warns if `# Verification` is absent

2. **Update `mkdocs.yml` nav** to reference the renamed page

3. **Replace `docs/examples/` stubs**
   - Replace placeholder content with embedded real specs from `examples/fasthtml_app/`
     and `examples/nextjs_ai_chat/` showing a real multi-spec project end-to-end
   - Link to the arrangement file for each example

4. **Verify** that `mkdocs build` completes without errors (snippet paths resolve)

## Note on Snippets

The MkDocs `snippets` extension embeds file content at build time:

```markdown
\`\`\`markdown
--8<-- "score/config.spec.md"
\`\`\`
```

All paths are relative to the `docs_dir` root (i.e. the repo root when `docs_dir: docs`
is set). Verify the base path in `mkdocs.yml` before embedding.

## Success Criteria

- `docs/reference/spec-types.md` (or equivalent) shows a real example for every spec type
- `type: reference` conventions are fully documented
- `docs/examples/` pages contain real spec content, not stubs
- `mkdocs build` completes without errors
- No synthetic/hand-copied spec snippets — all examples embedded from real files
