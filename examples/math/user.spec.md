---
name: user
type: type
status: stable
tags:
  - auth
  - core
---

# Overview

Represents a user account in the system. Users have a unique identifier, email address, display name, and timestamps for auditing.

# Schema

```yaml:schema
properties:
  id:
    type: string
    format: uuid
    description: Unique identifier, assigned at creation
  email:
    type: string
    format: email
    description: Primary email address, must be unique
  name:
    type: string
    minLength: 1
    maxLength: 100
    description: Display name
  role:
    type: string
    enum: [user, admin, guest]
    description: Access level
  created_at:
    type: datetime
    description: When the account was created
  updated_at:
    type: datetime
    description: When the account was last modified
required:
  - id
  - email
  - role
  - created_at
```

# Constraints

- **[NFR-01]**: Email must be unique across all users
- **[NFR-02]**: ID must be immutable after creation
- **[NFR-03]**: updated_at must be >= created_at

# Examples

| Valid | Notes |
|-------|-------|
| `{id: "550e8400-...", email: "jo@example.com", role: "user", created_at: "2024-01-01T00:00:00Z"}` | Minimal valid user |
| `{id: "...", email: "admin@example.com", name: "Admin", role: "admin", created_at: "...", updated_at: "..."}` | Full user |

| Invalid | Why |
|---------|-----|
| `{email: "a@b.com", role: "user"}` | Missing id, created_at |
| `{id: "...", email: "not-an-email", role: "user", created_at: "..."}` | Invalid email format |
| `{id: "...", email: "a@b.com", role: "superuser", created_at: "..."}` | Invalid role enum |
