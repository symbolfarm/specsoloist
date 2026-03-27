# Quine Validation Results

A quine run compiles every spec in `score/` to working code and verifies all generated
tests pass. A successful quine proves the Score accurately describes the implementation.

---

## 2026-03-27 — v0.7.0 ✅

**Command:**
```bash
sp conduct score/ --arrangement score/arrangement.yaml --model haiku --auto-accept
```

**Result:** 584/584 tests passing (100%)
**Build time:** ~600 seconds (parallel, 5 phases)
**Generated:** ~14,700 lines of code across 16 modules + 16 test files

### Compilation phases

| Phase | Specs | Tests |
|-------|-------|-------|
| 1 — Base | config, manifest, ui, schema | 173 |
| 2 — Parsing & execution | respec, runner, parser, resolver | 135 |
| 3 — Analysis | build_diff, compiler, spec_diff | 125 |
| 4 — Orchestration | core, composer | 59 |
| 5 — CLI & conductor | conductor, cli | 92 |
| **Total** | **14 specs** | **584** |

### Output structure

```
build/quine/
├── src/
│   ├── specsoloist/          # 10 modules
│   │   ├── build_diff.py
│   │   ├── cli.py
│   │   ├── compiler.py
│   │   ├── config.py
│   │   ├── core.py
│   │   ├── manifest.py
│   │   ├── parser.py
│   │   ├── resolver.py
│   │   ├── respec.py
│   │   ├── runner.py
│   │   ├── schema.py
│   │   ├── spec_diff.py
│   │   ├── ui.py
│   │   ├── help/             # static — copied verbatim
│   │   ├── skills/           # static — copied verbatim
│   │   └── providers/        # 5 provider modules
│   └── spechestra/           # 2 modules (output_paths.overrides)
│       ├── composer.py
│       └── conductor.py
└── tests/
    └── test_*.py             # 14 test files
```

### Notes

- First quine run using `score/arrangement.yaml` — static artifacts (`help/`, `skills/`)
  and spechestra `output_paths.overrides` both validated for the first time.
- Quine generated 584 tests vs 411 in the canonical test suite; the Score prompts
  more thorough test generation than the hand-written suite in some modules.
- Agent fixed `create_provider()` in config.py during compilation (provider
  instantiation logic for AnthropicProvider, GeminiProvider, PydanticAIProvider).

---

## 2026-03-19 — v0.5.0 ✅

**Command:** `sp conduct score/ --model haiku --auto-accept`
**Result:** 355/355 tests passing (100%)
**Specs:** 14 code-generating specs (score/ refreshed in task 21; spec_diff added in task 22)

---

## 2026-02-09 — v0.2.x ✅

**Command:** `sp conduct score/ --model haiku --auto-accept`
**Result:** 563/563 tests passing (100%)
**Specs:** 17 specs (older score structure with speccomposer/specconductor naming)
**Build time:** ~13 minutes
