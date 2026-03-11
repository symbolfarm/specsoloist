# Task: Database and Persistence Spec Patterns

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.

Persistence is present in almost every real web application. The current SpecSoloist
documentation and examples use only in-memory state (a Python list, a JS array). This
leaves a significant gap: developers building database-backed web apps have no guidance
on how to spec and generate data access code.

The two primary stacks for the target web frameworks:

- **FastHTML + fastlite** — FastHTML ships with `fastlite`, a SQLite ORM built on `apsw`.
  Its API is distinct from SQLAlchemy/SQLModel and soloists may hallucinate it.
- **Next.js + Prisma** — the most common Node.js ORM, with its own schema language and
  generated client. Soloists unfamiliar with Prisma's client API often generate raw SQL.
- **Next.js + Drizzle** — a newer, TypeScript-first ORM that is gaining popularity.

This task creates reference specs for these libraries and demonstrates the patterns with
working examples.

## What to Build

### 1. Reference spec: `fastlite`

Create `examples/fasthtml_app/specs/fastlite_interface.spec.md` as a `reference` spec
documenting the fastlite API subset needed for CRUD operations:

Key API surface to document:
- `database(path)` — opens/creates a SQLite database
- `db.t.tablename` — access or create a table
- `Table.__init__(db, cls)` — registers a dataclass as a table schema
- `table.insert(item)` / `table.update(item)` / `table.delete(id)`
- `table[id]` — get by primary key; raises `NotFoundError` if missing
- `table()` — returns all rows as a list
- `table.where(condition)` — filtered query
- The `dataclass` pattern: use a plain Python dataclass to define the schema, then
  `todos = db.create(Todo, pk='id')`

Include version note: fastlite is bundled with python-fasthtml; import as
`from fastlite import database`.

### 2. Extend the FastHTML example with persistence

Add a database-backed variant of the todo app to `examples/fasthtml_app/`:

**`specs/db.spec.md`** (`type: bundle`, depends on `fastlite_interface`)

Data access layer:
- `open_db(path: str = "todos.db") -> Database` — opens the database and ensures the
  `todos` table exists
- `Todo` dataclass: `id: int`, `text: str`, `done: bool = False`
- `get_todos(db) -> list[Todo]`
- `add_todo(db, text: str) -> Todo`
- `delete_todo(db, id: int)` — raises `NotFoundError` if not found
- `toggle_todo(db, id: int) -> Todo` — flips `done` flag

**`specs/routes_db.spec.md`** (`type: bundle`, depends on `fasthtml_interface`, `layout`, `db`)

Same routes as `routes.spec.md` but using the `db` module for persistence. The database
is opened once at startup and passed to handlers. Each todo item now has a done/undone
toggle button in addition to the delete button.

Tests should use a temporary SQLite database (via `tempfile.mkstemp`) and reset it
between tests.

### 3. Reference spec: Prisma (Next.js)

Create `examples/nextjs_ai_chat/specs/prisma_interface.spec.md` as a `reference` spec.

Key API surface to document:
- `PrismaClient` — import from `@prisma/client`, instantiate once per process
- `prisma.modelName.findMany(args?)` / `findUnique` / `create` / `update` / `delete`
- `args` shape: `{ where: {...}, data: {...}, select: {...}, orderBy: {...} }`
- The Prisma schema file (`prisma/schema.prisma`) — document the relevant model definitions
  so soloists know the field names
- `prisma.$disconnect()` — call on shutdown
- Testing: use `@prisma/client/testing` or mock with `jest.mock('@prisma/client')`

Version note: Prisma 5.x API (matches `"^5.0"` in `package.json`).

### 4. Next.js + Prisma example

Add persistence to `examples/nextjs_ai_chat/` or create a separate
`examples/nextjs_todos/` with:
- `prisma/schema.prisma` — `Todo` model (id, text, done, createdAt)
- `specs/prisma_interface.spec.md` — reference spec
- `specs/todo_store.spec.md` — data access layer wrapping Prisma
- `specs/todo_routes.spec.md` — Next.js API routes using `todo_store`
- `arrangement.yaml` with `setup_commands: [npm install, npx prisma generate]`

Tests should mock Prisma using `jest.mock` or `vitest.mock`.

### 5. Guide: `docs/database-patterns.md`

Document the general pattern for database specs:

**Pattern 1: Reference spec for the ORM** — always write a `reference` spec before
speccing any data access layer that uses a new ORM. This is the most important step
to avoid hallucinated API calls.

**Pattern 2: Separate data access from routing** — `db.spec.md` or `todo_store.spec.md`
is independently testable with a real (temporary) or mocked database. Routes are tested
with a mock data layer. Never test routes against a real database.

**Pattern 3: Schema as the source of truth** — the database schema (dataclass fields,
Prisma model) belongs in the spec, not guessed by the soloist. Include field names, types,
and constraints explicitly. Soloists that don't know the schema will invent one.

**Pattern 4: Test fixtures** — document the standard fixture pattern for each ORM:
- fastlite: `tempfile.mkstemp()` + `database(path)` + yield + `os.unlink(path)`
- Prisma: `jest.mock('@prisma/client')` with factory returning mock methods

**Pattern 5: Migration handling** — SpecSoloist specs describe the current schema.
Migrations are out of scope (they're infrastructure, not application logic). Document
what to put in `setup_commands` to run migrations before tests.

## Files to Read First

- `examples/fasthtml_app/specs/` — existing specs to extend
- `examples/nextjs_ai_chat/` — existing Next.js example
- `score/spec_format.spec.md` — reference type and bundle patterns
- `arrangements/python-fasthtml.yaml` (from task 08)
- `AGENTS.md`

## Success Criteria

1. `examples/fasthtml_app/specs/fastlite_interface.spec.md` exists as a `reference` spec
   and passes `sp validate`.
2. `sp conduct` on the db-backed FastHTML specs generates working code with passing tests
   (using a temporary SQLite database in tests).
3. `examples/nextjs_ai_chat/specs/prisma_interface.spec.md` (or equivalent) exists.
4. `docs/database-patterns.md` covers all 5 patterns above.
5. Database test fixtures properly isolate tests — no shared state between test runs.
6. No generated files committed.

## Notes

fastlite is relatively unknown and soloists reliably hallucinate its API. The reference
spec is the entire point — without it, generated code will use SQLAlchemy or raw sqlite3
calls instead of fastlite. Test this explicitly: run `sp conduct` on `db.spec.md` without
the reference spec and observe the error, then run with it and confirm correct output.
This makes a compelling demonstration of why reference specs matter.
