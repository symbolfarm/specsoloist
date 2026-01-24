---
name: validation
type: module
language_target: python
status: stable
dependencies:
  - name: ValidationError
    from: types.spec.md
  - name: UserCreateRequest
    from: types.spec.md
---

# 1. Overview
Validation utilities for user input. Provides functions to validate
email addresses, passwords, and user creation requests.

# 2. Interface Specification

## 2.1 Inputs

### `validate_email(email: str) -> List[ValidationError]`
| Name | Type | Description |
|------|------|-------------|
| `email` | `str` | Email address to validate |

### `validate_password(password: str) -> List[ValidationError]`
| Name | Type | Description |
|------|------|-------------|
| `password` | `str` | Password to validate |

### `validate_user_create(request: UserCreateRequest) -> List[ValidationError]`
| Name | Type | Description |
|------|------|-------------|
| `request` | `UserCreateRequest` | User creation request to validate |

## 2.2 Outputs
| Type | Description |
|------|-------------|
| `List[ValidationError]` | List of validation errors (empty if valid) |

# 3. Functional Requirements (Behavior)

## Email Validation
*   **FR-01**: `validate_email` shall return an error if the email is empty.
*   **FR-02**: `validate_email` shall return an error if the email does not contain '@'.
*   **FR-03**: `validate_email` shall return an error if the email does not contain a '.' after '@'.

## Password Validation
*   **FR-04**: `validate_password` shall return an error if password is less than 8 characters.
*   **FR-05**: `validate_password` shall return an error if password contains no digits.
*   **FR-06**: `validate_password` shall return an error if password contains no uppercase letters.

## User Create Validation
*   **FR-07**: `validate_user_create` shall validate both email and password.
*   **FR-08**: `validate_user_create` shall return an error if name is empty.

# 4. Non-Functional Requirements (Constraints)
*   **NFR-Purity**: All validation functions must be pure (no side effects).
*   **NFR-Performance**: Validation should be O(n) where n is input string length.

# 5. Design Contract
*   **Pre-condition**: Input strings may be any valid Python string (including empty).
*   **Post-condition**: Return value is always a list (never None).
*   **Invariant**: Validation functions never raise exceptions for invalid input.

# 6. Test Scenarios
| Scenario | Input | Expected Output | Notes |
|----------|-------|-----------------|-------|
| Valid email | `"user@example.com"` | `[]` | No errors |
| Missing @ | `"userexample.com"` | `[ValidationError("email", ...)]` | One error |
| Empty email | `""` | `[ValidationError("email", ...)]` | One error |
| Valid password | `"SecurePass1"` | `[]` | No errors |
| Short password | `"Ab1"` | `[ValidationError("password", ...)]` | One error |
| No digit | `"SecurePassword"` | `[ValidationError("password", ...)]` | One error |
| Valid user create | Valid request | `[]` | No errors |
| Invalid email in request | Bad email | `[ValidationError("email", ...)]` | Email error |
