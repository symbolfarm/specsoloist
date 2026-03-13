---
name: prisma_interface
type: reference
status: stable
---

# Overview

The subset of [Prisma](https://www.prisma.io) ORM (v5.x) used in Next.js projects.
Specs that query or mutate the database should list `prisma_interface` as a dependency.
No implementation is generated from this spec — it is API documentation only.

Prisma's generated client API is distinct from raw SQL, ORMs like TypeORM, and query
builders like Knex. Without this reference spec, soloists often generate raw SQL or
non-existent Prisma methods.

**Packages:** `@prisma/client` (runtime) and `prisma` (CLI for schema management).

```
npm install @prisma/client
npm install --save-dev prisma
```

**Import:**
```typescript
import { PrismaClient } from '@prisma/client';
```

**Singleton pattern (required in Next.js):**
```typescript
// lib/prisma.ts
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };
export const prisma = globalForPrisma.prisma ?? new PrismaClient();
if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;
```

Always import `prisma` from `lib/prisma` in Next.js app code — never instantiate
`PrismaClient` directly in route handlers (causes "too many connections" in dev).

# Schema

Prisma schemas live in `prisma/schema.prisma`. The `Todo` model used in this project:

```prisma
model Todo {
  id        Int      @id @default(autoincrement())
  text      String
  done      Boolean  @default(false)
  createdAt DateTime @default(now())
}
```

Run `npx prisma generate` after editing the schema to regenerate the client.
Run `npx prisma db push` to sync the schema to the database (dev).
Run `npx prisma migrate dev` for migration-tracked changes (production).

# API

## Querying

```typescript
// All records
const todos = await prisma.todo.findMany();

// Filtered
const done = await prisma.todo.findMany({ where: { done: true } });

// Ordered
const sorted = await prisma.todo.findMany({ orderBy: { createdAt: 'asc' } });

// Single record (throws if not found)
const todo = await prisma.todo.findUniqueOrThrow({ where: { id: 1 } });

// Single record or null
const maybeNull = await prisma.todo.findUnique({ where: { id: 1 } });
```

## Creating

```typescript
const todo = await prisma.todo.create({
  data: { text: 'Buy milk', done: false },
});
// Returns the created record with id and createdAt populated
```

## Updating

```typescript
const updated = await prisma.todo.update({
  where: { id: 1 },
  data: { done: true },
});
```

Throws `PrismaClientKnownRequestError` (code `P2025`) if the record does not exist.

## Deleting

```typescript
await prisma.todo.delete({ where: { id: 1 } });
```

Throws `PrismaClientKnownRequestError` (code `P2025`) if the record does not exist.

## Error Handling

```typescript
import { Prisma } from '@prisma/client';

try {
  await prisma.todo.delete({ where: { id: 99 } });
} catch (e) {
  if (e instanceof Prisma.PrismaClientKnownRequestError && e.code === 'P2025') {
    // Record not found
  }
  throw e;
}
```

# Testing with Vitest (Mock Pattern)

Never use a real database in unit tests. Mock the Prisma client:

```typescript
// tests/setup.ts
import { vi } from 'vitest';

vi.mock('../lib/prisma', () => ({
  prisma: {
    todo: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
      findUniqueOrThrow: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
  },
}));
```

Then in each test, configure the mock return value:

```typescript
import { prisma } from '../lib/prisma';
import { vi } from 'vitest';

test('returns all todos', async () => {
  vi.mocked(prisma.todo.findMany).mockResolvedValue([
    { id: 1, text: 'Buy milk', done: false, createdAt: new Date() },
  ]);
  // ... call your function under test
});
```

Reset mocks between tests with `vi.clearAllMocks()` in `beforeEach`.

# Verification

```typescript
// Verify the package can be imported (does not execute queries)
import { PrismaClient, Prisma } from '@prisma/client';

const client = new PrismaClient();
console.assert(typeof client.todo.findMany === 'function');
console.assert(typeof client.todo.create === 'function');
console.assert(typeof client.todo.update === 'function');
console.assert(typeof client.todo.delete === 'function');
console.assert(typeof Prisma.PrismaClientKnownRequestError === 'function');

await client.$disconnect();
```
