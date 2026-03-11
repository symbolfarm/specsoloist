---
name: state
type: bundle
status: stable
---

# Overview

In-memory data model for the FastHTML todo app. Stores the todo list and provides
operations to add, delete, and read items. Keeping state in a separate module makes
it independently testable — no HTTP involved.

# Functions

## `add_todo(item: str) -> int`

Appends `item` to the module-level `todos` list. Returns the index of the newly
added item.

## `delete_todo(index: int) -> None`

Removes the item at `index` from `todos`. Raises `IndexError` if `index` is out of
range.

## `get_todos() -> list[str]`

Returns a copy of the current `todos` list. Callers cannot mutate the internal list
via the return value.

# State

`todos: list[str] = []` — module-level list, initially empty. Mutated by `add_todo`
and `delete_todo`.

# Examples

```
add_todo("Buy milk")   -> 0
add_todo("Walk dog")   -> 1
get_todos()            -> ["Buy milk", "Walk dog"]
delete_todo(0)
get_todos()            -> ["Walk dog"]
delete_todo(99)        -> raises IndexError
```
