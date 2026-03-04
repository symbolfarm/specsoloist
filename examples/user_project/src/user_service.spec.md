---
name: user_service
type: module
status: stable
dependencies:
  - types
  - validation
---

# 1. Overview
User service providing high-level operations for user management.
Handles user creation with validation and provides user lookup functionality.

# 2. Interface Specification

```yaml:functions
create_user:
  inputs:
    request: {type: ref, ref: types/UserCreateRequest}
  outputs:
    result:
      type: union
      of:
        - {type: ref, ref: types/User}
        - {type: array, items: {type: ref, ref: types/ValidationError}}
  behavior: "Validates the request and creates a new user if valid, otherwise returns errors."

get_user:
  inputs:
    user_id: {type: string, format: uuid}
  outputs:
    user: {type: optional, of: {type: ref, ref: types/User}}
  behavior: "Returns the user if found, or null if no user exists with the given ID."
```

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
