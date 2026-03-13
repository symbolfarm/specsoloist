# Database and Persistence Spec Patterns

This guide covers how to spec and generate database-backed code with SpecSoloist.
The patterns here apply to any ORM, but the concrete examples use fastlite (FastHTML)
and Prisma (Next.js) — the two most common stacks in the target web frameworks.

See `examples/fasthtml_app/specs/` for working fastlite specs and
`examples/nextjs_ai_chat/specs/` for the Prisma reference spec.

---

## Pattern 1: Reference spec for the ORM

**Always write a `type: reference` spec for any ORM before speccing data access code.**

This is the most important step. Soloists that don't have accurate ORM documentation
will hallucinate the API:

- fastlite is bundled with python-fasthtml but virtually unknown — soloists generate
  SQLAlchemy models or raw `sqlite3` calls instead.
- Prisma has a generated client with a specific query API — soloists often generate
  raw SQL or invent method names (`prisma.todo.fetch()` doesn't exist).

The reference spec documents the exact API surface your project uses — nothing more.
Every spec that queries the database lists the reference spec in `dependencies:`.

```markdown
---
name: fastlite_interface
type: reference
status: stable
---

# Overview
...

# API
## Opening a Database
...
## Table Operations
...

# Verification
```python
from fastlite import database, NotFoundError
...
```
```

Reference specs generate no implementation code. They are injected into each dependent
soloist's context, giving them accurate documentation for the library.

**Specs to create:**
- `specs/fastlite_interface.spec.md` — for FastHTML projects
- `specs/prisma_interface.spec.md` — for Next.js/Prisma projects

---

## Pattern 2: Separate data access from routing

Keep the data access layer in its own spec (`db.spec.md` or `todo_store.spec.md`),
separate from routes.

**Why:** The data layer is independently testable with a real (temporary) database.
Routes are tested with a mock or injected data layer. Mixing them makes tests slow
and fragile.

**FastHTML example:**

```
specs/
  fastlite_interface.spec.md   ← reference: documents the ORM API
  db.spec.md                   ← bundle: open_db, get_todos, add_todo, delete_todo
  layout.spec.md               ← bundle: UI components
  routes_db.spec.md            ← bundle: HTTP handlers (depends on db + layout)
```

`db.spec.md` imports nothing from FastHTML or HTTP. Its tests use `open_db(":memory:")`.
`routes_db.spec.md` depends on `db` and `layout`. Its tests use the Starlette TestClient
with a patched in-memory database table.

**Next.js example:**

```
specs/
  prisma_interface.spec.md     ← reference: documents the Prisma client API
  todo_store.spec.md           ← bundle: getTodos, addTodo, deleteTodo (wraps Prisma)
  todo_routes.spec.md          ← bundle: Next.js API routes (depends on todo_store)
```

`todo_store.spec.md` depends on `prisma_interface`. Its tests mock the Prisma client.
`todo_routes.spec.md` depends on `todo_store`. Its tests mock `todo_store` functions.

---

## Pattern 3: Schema as the source of truth

Include field names, types, and constraints explicitly in the data access spec.
Don't let the soloist guess the schema.

**FastHTML/fastlite:** Put the dataclass definition in the spec:

```markdown
## `Todo` dataclass

```python
@dataclass
class Todo:
    id: int         # primary key — None on insert; fastlite assigns it
    text: str
    done: bool = False
```
```

**Next.js/Prisma:** Include the Prisma schema model in the reference spec:

```markdown
# Schema

```prisma
model Todo {
  id        Int      @id @default(autoincrement())
  text      String
  done      Boolean  @default(false)
  createdAt DateTime @default(now())
}
```
```

If the schema is in the reference spec, every dependent spec automatically has
access to the field names and types through the dependency injection system.

---

## Pattern 4: Test fixtures

### fastlite — in-memory database

Use `":memory:"` for fast, isolated tests. Create a fresh database per test via a
pytest fixture:

```python
import pytest
from db import open_db, Todo

@pytest.fixture
def todos():
    _, todos = open_db(":memory:")
    return todos

def test_add_todo(todos):
    todo = add_todo(todos, "Buy milk")
    assert todo.text == "Buy milk"
    assert todo.done is False
    assert todo.id is not None
```

Each test function gets a fresh, empty table. No teardown needed — in-memory databases
are destroyed when the connection closes.

**File-based tests (persistence across connections):**

```python
import pytest, tempfile, os
from db import open_db

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")

@pytest.fixture
def todos(db_path):
    _, todos = open_db(db_path)
    return todos
```

Use pytest's built-in `tmp_path` fixture — it creates a temporary directory and cleans
it up automatically.

### Prisma (Next.js/Vitest) — mock the client

Never use a real database in unit tests. Mock the Prisma client in `tests/setup.ts`:

```typescript
import { vi } from 'vitest';

vi.mock('../lib/prisma', () => ({
  prisma: {
    todo: {
      findMany: vi.fn(),
      findUniqueOrThrow: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
  },
}));
```

In each test, configure the mock return value:

```typescript
import { prisma } from '../lib/prisma';
import { vi } from 'vitest';

beforeEach(() => { vi.clearAllMocks(); });

test('returns all todos', async () => {
  vi.mocked(prisma.todo.findMany).mockResolvedValue([
    { id: 1, text: 'Buy milk', done: false, createdAt: new Date() },
  ]);
  const result = await getTodos();
  expect(result).toHaveLength(1);
});
```

Reference this pattern in `prisma_interface.spec.md` so soloists generating
`todo_store.spec.md` tests know exactly how to mock.

---

## Pattern 5: Migration handling

SpecSoloist specs describe application logic. Migrations are infrastructure — they're
out of scope for specs.

The right place to handle migrations is `setup_commands` in the arrangement:

**FastHTML/fastlite:**
```yaml
environment:
  setup_commands:
    - uv sync
    # No migration needed — fastlite creates tables automatically via db.create()
```

fastlite's `db.create(cls, pk)` is idempotent — it creates the table if it doesn't
exist and is a no-op if it does. No migration command needed.

**Next.js/Prisma (development):**
```yaml
environment:
  setup_commands:
    - npm install --no-package-lock
    - npx prisma generate   # regenerates the client from prisma/schema.prisma
    - npx prisma db push    # syncs schema to the dev database (no migration history)
```

**Next.js/Prisma (production):**
```yaml
environment:
  setup_commands:
    - npm install --no-package-lock
    - npx prisma generate
    - npx prisma migrate deploy   # applies pending migrations
```

Never put schema migration logic in application specs. If the schema changes, update
the `prisma_interface.spec.md` reference spec and the data access spec, then run
`sp conduct` to regenerate the data layer.

---

## Quick reference

```bash
# FastHTML: validate new specs
sp validate specs/fastlite_interface.spec.md
sp validate specs/db.spec.md
sp validate specs/routes_db.spec.md

# Build data layer and run tests
sp conduct specs/db.spec.md --arrangement arrangement.yaml
PYTHONPATH=src uv run pytest tests/test_db.py

# Next.js: validate Prisma reference
sp validate specs/prisma_interface.spec.md
```
