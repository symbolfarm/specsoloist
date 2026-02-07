---
name: manifest
type: bundle
tags:
  - core
  - builds
---

# Overview

Build manifest for tracking spec compilation state. Enables incremental builds by recording what was built, when, and from what inputs — so only changed specs (and their dependents) need recompilation.

# Types

## SpecBuildInfo

Build record for a single spec. Tracks the spec content hash at build time, the build timestamp, its dependencies, and the output files produced.

**Fields:** `spec_hash` (string), `built_at` (ISO timestamp string), `dependencies` (list of spec name strings), `output_files` (list of relative file path strings).

Must support round-tripping to/from dict for JSON serialization (`to_dict`, `from_dict`).

## BuildManifest

Collection of build records, persisted as `.specsoloist-manifest.json` in the build directory.

**Fields:** `version` (string, default `"1.0"`), `specs` (dict mapping spec name to `SpecBuildInfo`).

**Methods:**
- `get_spec_info(name)` -> `SpecBuildInfo` or `None`
- `update_spec(name, spec_hash, dependencies, output_files)` — record a successful build with current UTC timestamp
- `remove_spec(name)` — remove a spec's build record
- `save(build_dir)` — write manifest to `{build_dir}/.specsoloist-manifest.json` as JSON
- `load(build_dir)` (classmethod) — load manifest from file; return empty manifest if file doesn't exist or is corrupted/invalid JSON

## IncrementalBuilder

Determines which specs need rebuilding. Constructed with a `BuildManifest` and a `src_dir` string.

**Methods:**
- `needs_rebuild(spec_name, current_hash, current_deps, rebuilt_specs)` -> bool
- `get_rebuild_plan(build_order, spec_hashes, spec_deps)` -> list of spec names

# Functions

## compute_file_hash(path) -> string

Compute SHA-256 hash of a file's contents. Returns empty string if file doesn't exist.

## compute_content_hash(content) -> string

Compute SHA-256 hash of a string.

# Behavior

## Incremental rebuild logic

A spec needs rebuilding if ANY of:
1. It has never been built (not in manifest)
2. Its content hash has changed since last build
3. Its dependency list has changed since last build
4. Any of its current dependencies were rebuilt in this build cycle

`get_rebuild_plan` walks the build order (which is topological — dependencies first), checking each spec against the above rules. When a spec is marked for rebuild, it's added to the "rebuilt" set so downstream dependents will also trigger.

# Examples

| Scenario | needs_rebuild? | Why |
|----------|---------------|-----|
| Spec "foo" not in manifest | Yes | Never built |
| Spec "foo" hash changed from "abc" to "def" | Yes | Content changed |
| Spec "foo" deps were `[]`, now `["bar"]` | Yes | Dependencies changed |
| Spec "foo" unchanged, but dep "bar" was rebuilt this cycle | Yes | Dependency rebuilt |
| Spec "foo" unchanged, deps unchanged, no deps rebuilt | No | Nothing changed |
