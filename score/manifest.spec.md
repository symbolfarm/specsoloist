---
name: manifest
type: module
---

# Overview
This module provides functionality for managing a build manifest, which tracks the compilation state of specs to enable incremental builds. It includes classes for representing build information for individual specs (`SpecBuildInfo`) and the overall build manifest (`BuildManifest`). It also provides functions for computing file hashes and determining which specs need to be rebuilt based on changes. The module is designed to support efficient recompilation by only rebuilding specs that have changed or whose dependencies have changed.

# Exports
- `SpecBuildInfo`: Represents build information for a single spec.
- `BuildManifest`: Tracks build state for incremental compilation.
- `compute_file_hash`: Computes SHA-256 hash of a file's contents.
- `compute_content_hash`: Computes SHA-256 hash of string content.
- `IncrementalBuilder`: Determines which specs need rebuilding based on changes.

---
name: spec_build_info
type: type
---

# Overview
Represents build information for a single spec, including its hash, build timestamp, dependencies, and output files.

# Schema
```yaml:schema
properties:
  spec_hash:
    type: string
    description: Hash of spec file content.
  built_at:
    type: string
    format: datetime
    description: ISO timestamp of last build.
  dependencies:
    type: array
    items:
      type: string
    description: Spec names this depends on.
  output_files:
    type: array
    items:
      type: string
    description: Generated file paths (relative to build/).
required:
  - spec_hash
  - built_at
  - dependencies
  - output_files
```

# Constraints
- [NFR-01]: `built_at` must be a valid ISO 8601 timestamp.
- [NFR-02]: `spec_hash` must be a valid SHA-256 hash.

# Examples
| Valid | Invalid | Why |
|---|---|---|
| `{"spec_hash": "e5b7a3d2c...", "built_at": "2024-10-27T10:00:00Z", "dependencies": [], "output_files": ["build/foo.py"]}` | | Valid example |
| `{"built_at": "2024-10-27T10:00:00Z", "dependencies": [], "output_files": ["build/foo.py"]}` | | Missing `spec_hash` |
| `{"spec_hash": "e5b7a3d2c...", "built_at": "invalid", "dependencies": [], "output_files": ["build/foo.py"]}` | | Invalid `built_at` format |

---
name: build_manifest
type: type
---

# Overview
Tracks the build state for incremental compilation, storing information about each spec's build status.

# Schema
```yaml:schema
properties:
  version:
    type: string
    description: Version of the manifest format.
    default: "1.0"
  specs:
    type: object
    additionalProperties:
      type: ref
      ref: spec_build_info
    description: Map of spec name to build information.
required:
  - version
  - specs
```

# Constraints
- [NFR-01]: The `version` field should follow semantic versioning.
- [NFR-02]: The keys in the `specs` object should be valid spec names.

# Examples
| Valid | Invalid | Why |
|---|---|---|
| `{"version": "1.0", "specs": {"foo": {"spec_hash": "...", "built_at": "...", "dependencies": [], "output_files": []}}}` | | Valid example |
| `{"specs": {"foo": {"spec_hash": "...", "built_at": "...", "dependencies": [], "output_files": []}}}` | | Missing `version` |
| `{"version": "1.0", "specs": {"foo": {"built_at": "...", "dependencies": [], "output_files": []}}}` | | Missing `spec_hash` in `specs.foo` |

---
name: compute_file_hash
type: function
---

# Overview
Computes the SHA-256 hash of a file's contents.

# Interface
```yaml:schema
inputs:
  path:
    type: string
    description: The path to the file.
outputs:
  result:
    type: string
    description: The SHA-256 hash of the file's contents, or an empty string if the file does not exist.
```

# Behavior
- [FR-01]: If the file at `path` exists, compute and return its SHA-256 hash.
- [FR-02]: If the file at `path` does not exist, return an empty string.

# Constraints
- [NFR-01]: The function must handle files of any size.

# Examples
| Input | Output | Notes |
|---|---|---|
| "path/to/existing/file.txt" | "e5b7a3d2c..." | File exists and hash is computed. |
| "path/to/nonexistent/file.txt" | "" | File does not exist. |

---
name: compute_content_hash
type: function
---

# Overview
Computes the SHA-256 hash of a string's content.

# Interface
```yaml:schema
inputs:
  content:
    type: string
    description: The string content to hash.
outputs:
  result:
    type: string
    description: The SHA-256 hash of the string content.
```

# Behavior
- [FR-01]: Compute and return the SHA-256 hash of the input string `content`.

# Constraints
- [NFR-01]: The function must handle strings of any length.

# Examples
| Input | Output | Notes |
|---|---|---|
| "hello world" | "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9" | Hash of "hello world". |
| "" | "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" | Hash of an empty string. |

---
name: incremental_builder
type: type
---

# Overview
Determines which specs need rebuilding based on changes to their content, dependencies, or the rebuild status of their dependencies.

# Schema
```yaml:schema
properties:
  manifest:
    type: ref
    ref: build_manifest
    description: The build manifest to use for tracking build state.
  src_dir:
    type: string
    description: The source directory containing the spec files.
required:
  - manifest
  - src_dir
```

---
name: incremental_builder/needs_rebuild
type: function
---

# Overview
Determines if a spec needs rebuilding based on its current hash, dependencies, and the rebuild status of its dependencies.

# Interface
```yaml:schema
inputs:
  spec_name:
    type: string
    description: Name of the spec to check.
  current_hash:
    type: string
    description: Current hash of the spec file.
  current_deps:
    type: array
    items:
      type: string
    description: Current list of dependencies.
  rebuilt_specs:
    type: array
    items:
      type: string
    description: Set of specs already rebuilt in this cycle.
outputs:
  result:
    type: boolean
    description: True if the spec needs rebuilding, False otherwise.
```

# Behavior
- [FR-01]: Return `True` if the spec has never been built (not in manifest).
- [FR-02]: Return `True` if the spec's content hash has changed.
- [FR-03]: Return `True` if the spec's dependencies have changed.
- [FR-04]: Return `True` if any of the spec's dependencies were rebuilt in this build cycle.
- [FR-05]: Return `False` if none of the above conditions are met.

# Constraints
- [NFR-01]: The function must efficiently compare the current state with the manifest.

# Examples
| Input | Output | Notes |
|---|---|---|
| `spec_name="foo", current_hash="abc", current_deps=[], rebuilt_specs=[]` (and `foo` not in manifest) | `True` | Spec has never been built. |
| `spec_name="foo", current_hash="def", current_deps=[], rebuilt_specs=[]` (and `foo` in manifest with hash "abc") | `True` | Spec content has changed. |
| `spec_name="foo", current_hash="abc", current_deps=["bar"], rebuilt_specs=[]` (and `foo` in manifest with deps []) | `True` | Spec dependencies have changed. |
| `spec_name="foo", current_hash="abc", current_deps=[], rebuilt_specs=["bar"]` (and `foo` in manifest with deps ["bar"]) | `True` | A dependency has been rebuilt. |
| `spec_name="foo", current_hash="abc", current_deps=[], rebuilt_specs=[]` (and `foo` in manifest with hash "abc" and deps []) | `False` | Spec does not need rebuilding. |

---
name: incremental_builder/get_rebuild_plan
type: function
---

# Overview
Determines which specs in the build order need rebuilding, considering dependencies and already rebuilt specs.

# Interface
```yaml:schema
inputs:
  build_order:
    type: array
    items:
      type: string
    description: Specs in topological order.
  spec_hashes:
    type: object
    additionalProperties:
      type: string
    description: Map of spec name to current content hash.
  spec_deps:
    type: object
    additionalProperties:
      type: array
      items:
        type: string
    description: Map of spec name to list of dependencies.
outputs:
  result:
    type: array
    items:
      type: string
    description: List of spec names that need rebuilding, in build order.
```

# Behavior
- [FR-01]: Iterate through the `build_order`.
- [FR-02]: For each spec, determine if it needs rebuilding using `needs_rebuild`.
- [FR-03]: If a spec needs rebuilding, add it to the `result` list and mark it as rebuilt.
- [FR-04]: Return the `result` list.

# Constraints
- [NFR-01]: The function must maintain the original build order.
- [NFR-02]: The function must avoid redundant rebuilds by tracking rebuilt specs.

# Examples
| Input | Output | Notes |
|---|---|---|
| `build_order=["foo", "bar"], spec_hashes={"foo": "abc", "bar": "def"}, spec_deps={"foo": [], "bar": ["foo"]}` (and `foo` needs rebuild, `bar` doesn't initially) | `["foo", "bar"]` | `bar` needs rebuild because `foo` was rebuilt. |
| `build_order=["foo", "bar"], spec_hashes={"foo": "abc", "bar": "def"}, spec_deps={"foo": [], "bar": ["foo"]}` (and neither needs rebuild initially) | `[]` | No rebuilds needed. |