---
name: types
type: typedef
language_target: python
status: stable
dependencies: []
---

# 1. Overview
Shared data types for the user management system. These types are used across
multiple modules and represent the core domain entities.

# 2. Interface Specification

## 2.1 Types

### User
A registered user in the system.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier (UUID format) |
| `email` | `str` | User's email address |
| `name` | `str` | User's display name |
| `created_at` | `datetime` | Account creation timestamp |
| `is_active` | `bool` | Whether the account is active |

### UserCreateRequest
Request payload for creating a new user.

| Field | Type | Description |
|-------|------|-------------|
| `email` | `str` | User's email address |
| `name` | `str` | User's display name |
| `password` | `str` | Plain text password (will be hashed) |

### ValidationError
Represents a validation failure.

| Field | Type | Description |
|-------|------|-------------|
| `field` | `str` | Name of the invalid field |
| `message` | `str` | Human-readable error message |

## 2.2 Outputs
N/A - This is a type definition module.

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
