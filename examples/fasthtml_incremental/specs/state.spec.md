---
name: state
type: bundle
status: stable
---

# Overview

In-memory state management for a priority-based todo app. Stores todos as dicts
with `text` (string) and `priority` (one of "low", "medium", "high"). No persistence
— state resets on restart. No FastHTML or HTTP imports.

Valid priorities are exactly: `"low"`, `"medium"`, `"high"`. The default priority is
`"medium"` when an unrecognised value is supplied.

# Functions

## `get_todos(priority: str = "") -> list[dict]`

Return all todos. If `priority` is a valid priority string, return only todos with
that priority. Otherwise return all todos.

Each todo dict has keys `"text"` (str) and `"priority"` (str).

## `add_todo(text: str, priority: str = "medium") -> int`

Add a todo with the given text and priority. If `priority` is not a valid priority,
use `"medium"`. Return the index of the newly added todo.

Raises `ValueError` if `text` is empty or whitespace-only.

## `delete_todo(index: int) -> None`

Remove the todo at the given index. Raises `IndexError` if `index` is out of range.

## `get_stats() -> dict[str, int]`

Return a dict with the count of todos per priority, plus a `"total"` key:
`{"low": int, "medium": int, "high": int, "total": int}`.

# Examples

| Scenario | Action | Expected |
|----------|--------|----------|
| Add low priority | `add_todo("Fix bug", "low")` | Returns 0; `get_todos()` has one item |
| Filter by priority | `add_todo("A", "high")`, `add_todo("B", "low")`, `get_todos("high")` | Returns only the "high" item |
| Invalid priority | `add_todo("Task", "critical")` → priority stored as "medium" | `get_todos("medium")` includes the task |
| Stats | 1 low + 2 medium | `get_stats()` = `{"low":1, "medium":2, "high":0, "total":3}` |
| Delete out of range | `delete_todo(99)` | Raises `IndexError` |
| Empty text | `add_todo("")` | Raises `ValueError` |
