---
name: user_service
type: module
language_target: python
status: stable
dependencies:
  - name: User
    from: types.spec.md
  - name: UserCreateRequest
    from: types.spec.md
  - name: ValidationError
    from: types.spec.md
  - name: validate_user_create
    from: validation.spec.md
---

# 1. Overview
User service providing high-level operations for user management.
Handles user creation with validation and provides user lookup functionality.

# 2. Interface Specification

## 2.1 Inputs

### `create_user(request: UserCreateRequest) -> Union[User, List[ValidationError]]`
| Name | Type | Description |
|------|------|-------------|
| `request` | `UserCreateRequest` | User creation request |

### `get_user(user_id: str) -> Optional[User]`
| Name | Type | Description |
|------|------|-------------|
| `user_id` | `str` | User's unique identifier |

## 2.2 Outputs
| Type | Description |
|------|-------------|
| `Union[User, List[ValidationError]]` | Created user or validation errors |
| `Optional[User]` | User if found, None otherwise |

# 3. Functional Requirements (Behavior)
*   **FR-01**: `create_user` shall validate the request using `validate_user_create`.
*   **FR-02**: If validation fails, `create_user` shall return the list of validation errors.
*   **FR-03**: If validation passes, `create_user` shall create a new `User` with a generated UUID.
*   **FR-04**: The created user's `created_at` shall be set to the current UTC time.
*   **FR-05**: `get_user` shall return None if no user exists with the given ID.
*   **FR-06**: For this demo, users shall be stored in a module-level dictionary.

# 4. Non-Functional Requirements (Constraints)
*   **NFR-Security**: Passwords shall never be stored in the User object (only hashed if needed).
*   **NFR-Threading**: The in-memory store is not thread-safe (acceptable for demo).

# 5. Design Contract
*   **Pre-condition**: `user_id` for `get_user` should be a non-empty string.
*   **Post-condition**: `create_user` always returns either a User or a non-empty error list.
*   **Invariant**: All returned User objects have a valid UUID as their `id`.

# 6. Test Scenarios
| Scenario | Input | Expected Output | Notes |
|----------|-------|-----------------|-------|
| Create valid user | Valid request | `User` object | Has generated UUID |
| Create with invalid email | Bad email | `List[ValidationError]` | Contains email error |
| Get existing user | Valid ID | `User` object | Same as created |
| Get non-existent user | Random ID | `None` | Not found |
