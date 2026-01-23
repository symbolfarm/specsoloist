# Component Specification: URL Slugifier

## 1. Metadata
- **Component Name**: `slugify`
- **Type**: `Function`
- **Complexity**: `Low`

## 2. Objective
Converts an input string into a URL-friendly "slug". This involves standardizing character case, removing invalid characters, and managing whitespace.

## 3. Interface

### 3.1 Inputs
| Name | Type | Required | Constraints | Description |
|------|------|----------|-------------|-------------|
| `text` | `String` | Yes | None | The raw input text to convert. |
| `separator` | `String` | No | Default: `"-"` | The character used to replace whitespace. |

### 3.2 Outputs
| Type | Description | Guarantees |
|------|-------------|------------|
| `String` | The generated slug. | Lowercase, contains only alphanumeric and separator. |

## 4. Logical Specification

1. **Normalization**: Convert the `text` to a unicode normalized form (NFKD) to decompose combined characters (e.g., 'é' -> 'e' + '´').
2. **Filtering**: Remove any non-ASCII characters that remain after normalization.
3. **Case Conversion**: Convert the string to lowercase.
4. **Replacement**: Replace any sequence of whitespace or non-alphanumeric characters (excluding the separator itself if strictly alphanumeric is not required, but usually we replace *everything* that isn't a letter or number) with the `separator`. 
    *Refinement*: Replace all characters that are NOT alphanumeric (a-z, 0-9) with the `separator`.
5. **Trimming**: Remove any leading or trailing `separator` characters.
6. **Deduplication**: Collapse multiple consecutive `separator` characters into a single instance.

## 5. Edge Cases & Error Handling
- **Null/Empty Input**: Return an empty string.
- **All Special Characters**: If input is `!@#$%`, result should be empty string (after trimming).
- **Separator Collision**: If input contains the separator, it should be treated as a break/merged if consecutive.

## 6. Dependencies
- Standard String Manipulation Libraries.
- Unicode normalization libraries.

## 7. Test Plan

| Scenario | Input (`text`, `separator`) | Expected Output |
|----------|-----------------------------|-----------------|
| Basic | `"Hello World"`, `"-"` | `"hello-world"` |
| Punctuation | `"Hello, World!"`, `"-"` | `"hello-world"` |
| Accents | `"Crème Brûlée"`, `"-"` | `"creme-brulee"` |
| Multiple Spaces | `"foo    bar"`, `"-"` | `"foo-bar"` |
| Custom Separator | `"Hello World"`, `"_"` | `"hello_world"` |
| Leading/Trailing | `"  foo bar  "`, `"-"` | `"foo-bar"` |
| Empty | `""`, `"-"` | `""` |
