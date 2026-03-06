---
name: web-dev-template
description: >-
  Guide for building full-stack features on this FastAPI + Next.js + PostgreSQL template.
  Use when adding new models, API routes, services, schemas, frontend pages, server actions,
  data fetchers, database migrations, or tests. Provides architecture patterns, step-by-step
  procedures, and code conventions for extending the template into a complete application.
metadata:
  author: shaojielu
  version: "1.0"
---

This skill teaches how to extend this full-stack web application template into a complete product. The golden rule: **follow existing patterns exactly**. Every new feature should look like it was written by the same developer who built the existing code.

Before adding any feature, study the existing `Customer` and `Invoice` implementations end-to-end. They are the canonical reference for every layer of the stack.

## Architecture Overview

### Backend (FastAPI + SQLAlchemy + PostgreSQL)

```
backend/app/
  models/        SQLAlchemy ORM models (inherit Base from models/base.py)
  schemas/       Pydantic request/response schemas
  services/      Business logic functions (receive AsyncSession, never commit)
  api/routes/    Thin route handlers (inject deps, call services, return schemas)
  api/deps.py    FastAPI dependencies: SessionDep, CurrentUserDep, CurrentActiveUserDep
  api/main.py    Router registry (include_router for each route module)
  core/config.py Pydantic Settings (reads ../.env)
  core/db.py     Async SQLAlchemy engine + session factory
  core/security.py JWT + password hashing
```

**Request flow**: Route handler -> injects `SessionDep` + `CurrentActiveUserDep` -> calls service function -> service queries/mutates via session -> route returns Pydantic schema.

**Session lifecycle**: `deps.py:get_db()` auto-commits on success, rolls back on exception. Services use `flush()` (not `commit()`).

### Frontend (Next.js App Router + React 19)

```
frontend/app/
  lib/api.ts          Server-side apiFetch() wrapper (reads JWT from cookies)
  lib/data.ts         Data fetching functions (called from server components)
  lib/actions.ts      Server Actions (form mutations with Zod validation)
  lib/definitions.ts  TypeScript type definitions
  ui/                 Reusable UI components organized by feature
  dashboard/          Protected route pages
```

**Data flow**: Server component -> calls data fetcher from `data.ts` -> `apiFetch()` calls backend API -> returns typed data -> renders in component.

**Mutation flow**: Client form -> `useActionState` hook -> Server Action in `actions.ts` -> Zod validation -> `apiFetch()` POST/PATCH/DELETE -> `revalidatePath()` -> redirect.

## Full-Stack Feature Procedure

Follow these steps in order when adding a new feature (e.g., a "Product" resource).

### Step 1: Create SQLAlchemy Model

Create `backend/app/models/product.py`:

- Import and inherit from `Base` (provides `id`, `created_at`, `updated_at`)
- Set `__tablename__` (plural, snake_case)
- Use `Mapped[T]` type annotations with `mapped_column()`
- For foreign keys: `Mapped[uuid.UUID] = mapped_column(ForeignKey("tablename.id"))`
- For relationships: use `TYPE_CHECKING` guard to avoid circular imports
- See `references/backend-patterns.md` for the exact model pattern

### Step 2: Register Model in `__init__.py`

Add to `backend/app/models/__init__.py`:

```python
from app.models.product import Product
# Add to __all__ list
```

This is **required** for Alembic autogenerate to detect the model.

### Step 3: Create Pydantic Schemas

Create `backend/app/schemas/products.py` following the hierarchy:

- `ProductBase(BaseModel)` - shared fields with validation (Field, max_length, etc.)
- `ProductCreate(ProductBase)` - fields needed for creation
- `ProductUpdate(BaseModel)` - all fields optional (`None` defaults)
- `ProductPublic(ProductBase, BaseSchema)` - adds `id`, `created_at`, `updated_at`
- `ProductsPublic(BaseSchema)` - list wrapper with `data: list[ProductPublic]` and `count: int`

`BaseSchema` (from `schemas/base.py`) enables `model_config = ConfigDict(from_attributes=True)` for ORM conversion.

### Step 4: Create Service Functions

Create `backend/app/services/product.py`:

- All functions receive `session: AsyncSession` as first parameter
- Use `session.flush()` after mutations (NOT `session.commit()` - the dep handles commits)
- Standard CRUD: `create_product`, `get_product_by_id`, `get_products`, `update_product`, `delete_product`
- For updates: use `model_dump(exclude_unset=True)` then `setattr()` loop
- For pagination: return `tuple[list[Product], int]` (items + total count)
- See `references/backend-patterns.md` for the exact service pattern

### Step 5: Create API Route

Create `backend/app/api/routes/products.py`:

- Create router: `router = APIRouter(prefix="/products", tags=["products"])`
- Inject dependencies in function signature: `session: SessionDep`, `current_user: CurrentActiveUserDep`
- Call service functions, convert results to schema with `model_validate()`
- Use `Query()` for pagination params with `ge`/`le` validation
- Return Pydantic response models (set `response_model` on decorator)
- See `references/backend-patterns.md` for the exact route pattern

### Step 6: Register Router

In `backend/app/api/main.py`:

```python
from app.api.routes import products
api_router.include_router(products.router)
```

All routes are automatically prefixed under `/api/v1` by the app configuration.

### Step 7: Generate Alembic Migration

```bash
cd backend
uv run alembic revision --autogenerate -m "Add product table"
uv run alembic upgrade head
```

Review the generated migration file before applying. Verify it creates the correct table and columns.

### Step 8: Define TypeScript Types

Add to `frontend/app/lib/definitions.ts`:

```typescript
export type Product = {
  id: string;
  name: string;
  // ... fields matching ProductPublic schema
  created_at: string;
  updated_at: string;
};
```

Use `string` for UUIDs, dates, and decimals. Use specific union types for enums (e.g., `'active' | 'inactive'`).

### Step 9: Add Data Fetchers

Add to `frontend/app/lib/data.ts`:

```typescript
export async function fetchProducts(
  query: string,
  currentPage: number,
): Promise<Product[]> {
  const skip = (currentPage - 1) * ITEMS_PER_PAGE;
  const params = new URLSearchParams();
  params.set("skip", skip.toString());
  params.set("limit", ITEMS_PER_PAGE.toString());
  if (query) params.set("query", query);

  const data = await apiFetch<{ data: Product[]; count: number }>(
    `/api/v1/products/?${params.toString()}`,
  );
  return data.data;
}
```

All data fetchers use `apiFetch<T>()` which auto-attaches auth token from cookies.

### Step 10: Add Server Actions

Add to `frontend/app/lib/actions.ts`:

- Define a Zod schema for form validation
- Define a `State` type for form error handling
- Create server action: validate with Zod -> call `apiFetch()` -> `revalidatePath()` -> `redirect()`
- See `references/frontend-patterns.md` for the exact pattern

### Step 11: Create UI Components

Create `frontend/app/ui/products/` directory:

- `table.tsx` - data table component
- `create-form.tsx` - creation form using `useActionState`
- `edit-form.tsx` - edit form (pre-filled)
- `buttons.tsx` - action buttons (Create, Update, Delete)

Form components use `useActionState` to bind server actions with error state.

### Step 12: Create Pages

Create under `frontend/app/dashboard/products/`:

- `page.tsx` - list page with search, pagination, Suspense
- `create/page.tsx` - creation form page
- `[id]/edit/page.tsx` - edit form page

Pages are async server components. Use `Suspense` with skeleton fallbacks for data loading.

### Step 13: Add Navigation Link

In `frontend/app/ui/dashboard/nav-links.tsx`, add to the `links` array:

```typescript
{ name: 'Products', href: '/dashboard/products', icon: SomeIcon },
```

### Step 14: Write Backend Tests

Create `backend/tests/api/routes/test_products.py`:

- Add `pytestmark = pytest.mark.anyio` at module level
- Use fixtures: `client`, `db`, `superuser_token_headers`, `normal_user_token_headers`
- Test auth requirements (401 without token)
- Test CRUD operations through API
- Test validation (422 for bad input)
- Test pagination boundaries
- See `references/testing-and-config.md` for the exact test pattern

### Step 15: Write E2E Tests (Playwright)

Create `frontend/tests/products.spec.ts`:

- Test page load, search, create, edit, delete flows
- Run via Docker: `docker compose run --rm playwright npx playwright test tests/products.spec.ts`

## Code Conventions

### Naming

- **Models**: PascalCase singular (`Product`), tablename plural snake_case (`products`)
- **Schemas**: `ProductBase`, `ProductCreate`, `ProductUpdate`, `ProductPublic`, `ProductsPublic`
- **Services**: `create_product`, `get_product_by_id`, `get_products`, `update_product`, `delete_product`
- **Routes**: file name matches resource (`products.py`), router prefix matches resource (`/products`)
- **Frontend files**: kebab-case (`create-form.tsx`), directories by feature (`ui/products/`)

### Import Patterns

- Backend: absolute imports from `app.` prefix (e.g., `from app.models.product import Product`)
- Frontend: `@/app/` path alias (e.g., `import { Product } from '@/app/lib/definitions'`)
- Use `TYPE_CHECKING` guard for model cross-references to prevent circular imports

### File Organization

- One model per file in `models/`
- One schema module per resource in `schemas/`
- One service module per resource in `services/`
- One route module per resource in `api/routes/`
- Frontend components grouped by feature in `ui/[feature]/`

## Key Rules and Anti-patterns

### Backend Rules

1. **Never call `session.commit()` in services**. Use `session.flush()`. The dependency in `deps.py` handles commit/rollback automatically.
2. **Always register new models** in `models/__init__.py`. Alembic won't detect them otherwise.
3. **Always register new routers** in `api/main.py`. Routes won't be accessible otherwise.
4. **Use `Mapped[T]` annotations** with `mapped_column()`. Do not use legacy `Column()` style.
5. **Use `TYPE_CHECKING` guards** for relationship type hints between models to avoid circular imports.
6. **All route handlers and service functions must be `async`**. The entire backend is async.
7. **Use `select()` + `session.execute()`** for queries, not `session.query()` (that's the sync API).
8. **Schema hierarchy matters**: `Update` schemas make all fields optional. `Public` schemas inherit from both the `Base` schema and `BaseSchema` (for ORM mode).
9. **Pagination pattern**: return `tuple[list[Model], int]` from services. Routes wrap in `{data: [...], count: N}` response.
10. **Foreign keys reference tablename.column** (string), not model class: `ForeignKey("customers.id")`.

### Frontend Rules

1. **`apiFetch()` is server-only**. It imports `next/headers` and cannot run in client components.
2. **Server Actions must have `'use server'`** at the top of the file or function.
3. **Client components must have `'use client'`** at the top of the file.
4. **Always use `revalidatePath()`** after mutations to refresh cached data.
5. **Use Zod for form validation** in server actions, not manual checks.
6. **Use `useActionState`** (React 19) for form state management, not `useFormState`.
7. **Use UUIDs as strings** in TypeScript types. The backend returns UUID strings in JSON.
8. **Handle 404 in data fetchers** by catching `ApiError` and checking `error.status`.

### Testing Rules

1. **Tests require `ENVIRONMENT=test`** and database name ending in `_test`.
2. **Always add `pytestmark = pytest.mark.anyio`** at the module level for async tests.
3. **Use service functions to set up test data**, then test through the API client.
4. **Call `await db.commit()`** after setting up test data in fixtures (the test session doesn't auto-commit).

## Commands Reference

```bash
# Development
docker compose watch                              # Start all services
cd frontend && pnpm dev                           # Frontend dev server

# Backend tests
cd backend
ENVIRONMENT=test POSTGRES_DB=app_test POSTGRES_SERVER=localhost \
  POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=aabbccpostgres \
  uv run pytest                                   # Run all tests
  uv run pytest tests/api/routes/test_products.py # Run single file
  uv run pytest -k "test_create_product"          # Run by name

# Linting
cd backend
uv run ruff check app                             # Lint
uv run ruff format app                            # Format
uv run mypy app                                   # Type check

# Frontend
cd frontend
pnpm lint                                         # ESLint
pnpm build                                        # Production build

# Database migrations
cd backend
uv run alembic revision --autogenerate -m "desc"  # Generate migration
uv run alembic upgrade head                       # Apply migrations
uv run alembic downgrade -1                       # Rollback one

# E2E tests
docker compose run --rm playwright npx playwright test
```

## Reference Files

For annotated code examples extracted from this project:

- `references/backend-patterns.md` - Model, schema, service, route, and dependency patterns
- `references/frontend-patterns.md` - API wrapper, data fetchers, server actions, pages, and components
- `references/testing-and-config.md` - Test fixtures, route tests, environment config, and commands
