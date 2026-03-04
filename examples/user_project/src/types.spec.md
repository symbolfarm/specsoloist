---
name: types
type: typedef
status: stable
---

# 1. Overview
Shared data types for the user management system. These types are used across
multiple modules and represent the core domain entities.

# 2. Interface Specification

```yaml:types
User:
  properties:
    id: {type: string, format: uuid}
    email: {type: string, format: email}
    name: {type: string}
    created_at: {type: string, format: date-time}
    is_active: {type: boolean, default: true}

UserCreateRequest:
  properties:
    email: {type: string, format: email}
    name: {type: string}
    password: {type: string}

ValidationError:
  properties:
    field: {type: string}
    message: {type: string}
```

# 3. Functional Requirements (Behavior)
*   **FR-01**: All types shall be implemented as Python dataclasses with type hints.
*   **FR-02**: The `User` type shall use `field(default_factory=...)` for `created_at` to default to current time.
*   **FR-03**: The `is_active` field shall default to `True`.

# 4. Non-Functional Requirements (Constraints)
*   **NFR-Immutability**: All dataclasses should be frozen (immutable) except `UserCreateRequest`.
*   **NFR-Serialization**: Types should be JSON-serializable (use standard types only).

# 5. Design Contract
*   **Invariant**: `User.id` must be a valid UUID string.
*   **Invariant**: `User.email` must contain an '@' character.
