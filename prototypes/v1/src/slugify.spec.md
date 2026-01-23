---
name: slugify
type: function
language_target: python
status: draft
---

# 1. Overview
Converts an input string into a URL-friendly "slug" by normalizing, filtering, and sanitizing characters.

# 2. Interface Specification

## 2.1 Inputs
| Name | Type | Constraints | Description |
|------|------|-------------|-------------|
| `text` | `str` | None | The raw input text. |
| `separator` | `str` | Default=`"-"` | The replacement string for non-valid chars. |

## 2.2 Outputs
| Type | Description |
|------|-------------|
| `str` | The sanitized slug. |

# 3. Functional Requirements (Behavior)
*   **FR-01**: The function shall normalize Unicode characters to NFKD form (decomposing accents, e.g., 'é' -> 'e' + '´').
*   **FR-02**: The function shall filter out non-ASCII characters (e.g., removing the standalone '´' after normalization) to ensure the output is pure ASCII.
*   **FR-03**: The function shall convert all characters to lowercase.
*   **FR-04**: The function shall replace any sequence of non-alphanumeric characters (regex `[^a-z0-9]+`) with a single instance of `separator`.
*   **FR-05**: The function shall remove any leading or trailing instances of `separator` from the final result.

# 4. Non-Functional Requirements (Constraints)
*   **NFR-Performance**: Time complexity must be linear O(n) relative to the input string length.
*   **NFR-Purity**: The function must be pure (no side effects, no global state usage).
*   **NFR-Dependencies**: Use standard library `unicodedata` and `re` only.

# 5. Design Contract
*   **Pre-condition**: `text` can be `None` (should handle gracefully) or any string.
*   **Post-condition**: Output string contains only lowercase alphanumeric characters and the `separator`.
*   **Post-condition**: Output string never contains consecutive `separator`s.
*   **Post-condition**: If input is `None` or empty, output is `""`.

# 6. Test Scenarios
| Scenario | Input (`text`, `separator`) | Expected Output |
|----------|-----------------------------|-----------------|
| Basic | `"Hello World"`, `"-"` | `"hello-world"` |
| Punctuation | `"Hello, World!"`, `"-"` | `"hello-world"` |
| Accents | `"Crème Brûlée"`, `"-"` | `"creme-brulee"` |
| Consecutive Special | `"foo & bar"`, `"-"` | `"foo-bar"` |
| Custom Sep | `"Hello World"`, `"_"` | `"hello_world"` |
| Trimming | `" -foo- "`, `"-"` | `"foo"` |
| None Input | `None`, `"-"` | `""` |