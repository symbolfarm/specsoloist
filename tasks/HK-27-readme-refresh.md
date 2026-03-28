# HK-27: README refresh — badges, logo, demo GIF, fix PyPI links

## Motivation

The README is functional but plain. For a project seeking adoption, presentation matters.
Also, relative links in the README are broken when displayed on PyPI (which renders from
the uploaded package, not the GitHub repo).

## What to Do

### 1. Fix broken PyPI links

PyPI renders README.md from the package sdist/wheel. Relative links like `[ROADMAP](ROADMAP.md)`
or `[docs](docs/)` don't resolve. Options:
- Replace relative links with absolute GitHub URLs (`https://github.com/symbolfarm/specsoloist/blob/main/ROADMAP.md`)
- Or use PyPI's `project-urls` in `pyproject.toml` to link to docs/roadmap/changelog
- Review all relative links in the README and fix

### 2. Add badges

Standard shields.io badges at the top:
- PyPI version: `![PyPI](https://img.shields.io/pypi/v/specsoloist)`
- Python versions: `![Python](https://img.shields.io/pypi/pyversions/specsoloist)`
- License: `![License](https://img.shields.io/pypi/l/specsoloist)`
- Tests: GitHub Actions badge (link to the test workflow)
- Docs: link to GitHub Pages docs site

### 3. Logo image

- Commission or generate a logo (conductor with baton? music score + code?)
- Add to README header
- Keep it simple — SVG preferred for scalability

### 4. Demo GIF / asciinema

- Record a short demo showing `sp conduct` or `sp vibe` in action
- Once the TUI dashboard exists (task 31), record that instead — much more impressive
- Host in the repo (`docs/assets/demo.gif`) or use asciinema.org
- **Defer the actual recording until after task 31 is done** — the TUI will be the showcase

### 5. Balance README vs docs

- README should be the elevator pitch: what, why, quickstart, badges, demo
- Detailed reference (CLI flags, arrangement schema, spec format, API) belongs in docs
- Currently the README has a large CLI reference table — consider moving the full table
  to docs and keeping only the top 5 commands in the README
- Subscriber/event bus API documentation should go in docs, with a brief mention in README

## Files to Read Before Starting

- `README.md` — current state
- `pyproject.toml` — `[project.urls]` section
- `docs/` — existing documentation structure
- `.github/workflows/` — for test badge URL

## Success Criteria

- All links work on PyPI (test with `pip install specsoloist && pip show specsoloist`)
- Badges render correctly on GitHub
- README is shorter and more focused (detailed reference moved to docs)
- `uv run mkdocs build --strict` still passes
