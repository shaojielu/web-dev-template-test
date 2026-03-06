# Frontend Patterns

Annotated code examples from the project's Next.js frontend. Follow these patterns exactly when adding new features.

## API Wrapper

Source: `frontend/app/lib/api.ts`

The `apiFetch<T>()` function is the sole interface for server-side API calls. It is **server-only** (imports `next/headers`).

```typescript
import { apiFetch, ApiError } from "@/app/lib/api";

// Basic GET
const data = await apiFetch<{ data: Product[]; count: number }>(
  "/api/v1/products/",
);

// POST with body
await apiFetch("/api/v1/products/", {
  method: "POST",
  body: JSON.stringify({ name: "Widget", price: 9.99 }),
});

// Handle 404 gracefully
try {
  return await apiFetch<Product>(`/api/v1/products/${id}`);
} catch (error) {
  if (error instanceof ApiError && error.status === 404) {
    return null;
  }
  throw error;
}
```

Key points:

- Auto-attaches `Authorization: Bearer <token>` from the `access_token` cookie
- Auto-redirects to `/login` on 401 responses
- Sets `Content-Type: application/json` when body is present
- Returns `undefined` for 204 No Content responses
- Uses `cache: 'no-store'` by default (opt into caching with `revalidate` option)

## Type Definitions

Source: `frontend/app/lib/definitions.ts`

```typescript
export type Product = {
  id: string; // UUID as string
  name: string;
  price: string; // Decimal as string (backend returns string)
  status: "active" | "inactive"; // Enum as union type
  created_at: string; // ISO datetime as string
};

export type ProductForm = {
  id: string;
  name: string;
  price: number; // Parsed to number for form inputs
  status: "active" | "inactive";
};
```

Key points:

- UUIDs, dates, and decimals are `string` (matching JSON serialization)
- Create a separate `*Form` type when form fields need different types (e.g., `number` for input)
- Use union types for enum fields

## Data Fetchers

Source: `frontend/app/lib/data.ts`

```typescript
import { apiFetch } from "@/app/lib/api";
import { Product } from "@/app/lib/definitions";

const ITEMS_PER_PAGE = 6;

// Paginated list with search
export async function fetchFilteredProducts(
  query: string,
  currentPage: number,
): Promise<Product[]> {
  const skip = (currentPage - 1) * ITEMS_PER_PAGE;
  const params = new URLSearchParams();
  params.set("skip", skip.toString());
  params.set("limit", ITEMS_PER_PAGE.toString());
  if (query) {
    params.set("query", query);
  }

  const data = await apiFetch<{ data: Product[]; count: number }>(
    `/api/v1/products/?${params.toString()}`,
  );
  return data.data;
}

// Total pages for pagination
export async function fetchProductsPages(query: string): Promise<number> {
  const params = new URLSearchParams();
  params.set("skip", "0");
  params.set("limit", "1");
  if (query) {
    params.set("query", query);
  }

  const data = await apiFetch<{ data: Product[]; count: number }>(
    `/api/v1/products/?${params.toString()}`,
  );
  const totalPages = Math.ceil(data.count / ITEMS_PER_PAGE);
  return totalPages > 0 ? totalPages : 1;
}

// Single item by ID (returns null on 404)
export async function fetchProductById(
  id: string,
): Promise<ProductForm | null> {
  try {
    const product = await apiFetch<Product>(`/api/v1/products/${id}`);
    return {
      id: product.id,
      name: product.name,
      price: Number.parseFloat(product.price),
      status: product.status,
    };
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}
```

Key points:

- Calculate `skip` from page number: `(currentPage - 1) * ITEMS_PER_PAGE`
- Use `URLSearchParams` for query string construction
- Return `null` for not-found items (catch `ApiError` with status 404)
- Parse string decimals to numbers for form usage

## Server Actions

Source: `frontend/app/lib/actions.ts`

```typescript
"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";
import { apiFetch } from "@/app/lib/api";

// 1. Define Zod schema
const ProductSchema = z.object({
  name: z.string().min(1, { message: "Name is required." }),
  price: z.coerce.number().gt(0, { message: "Price must be greater than 0." }),
  status: z.enum(["active", "inactive"], {
    errorMap: () => ({ message: "Please select a status." }),
  }),
});

// 2. Define State type for form error handling
export type State = {
  errors?: {
    name?: string[];
    price?: string[];
    status?: string[];
  };
  message?: string | null;
};

// 3. Create action: validate -> API call -> revalidate -> redirect
export async function createProduct(
  _prevState: State,
  formData: FormData,
): Promise<State> {
  const validatedFields = ProductSchema.safeParse({
    name: formData.get("name"),
    price: formData.get("price"),
    status: formData.get("status"),
  });

  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
      message: "Missing fields. Failed to create product.",
    };
  }

  const { name, price, status } = validatedFields.data;

  await apiFetch("/api/v1/products/", {
    method: "POST",
    body: JSON.stringify({ name, price, status }),
  });

  revalidatePath("/dashboard/products");
  redirect("/dashboard/products");
}

// 4. Update action: bind id via .bind(), same pattern
export async function updateProduct(
  id: string,
  _prevState: State,
  formData: FormData,
): Promise<State> {
  const validatedFields = ProductSchema.safeParse({
    name: formData.get("name"),
    price: formData.get("price"),
    status: formData.get("status"),
  });

  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
      message: "Missing fields. Failed to update product.",
    };
  }

  await apiFetch(`/api/v1/products/${id}`, {
    method: "PATCH",
    body: JSON.stringify(validatedFields.data),
  });

  revalidatePath("/dashboard/products");
  redirect("/dashboard/products");
}

// 5. Delete action: simple, no form data
export async function deleteProduct(id: string) {
  await apiFetch(`/api/v1/products/${id}`, { method: "DELETE" });
  revalidatePath("/dashboard/products");
}
```

Key points:

- File must start with `'use server'`
- Use `z.coerce.number()` for form inputs that come as strings
- `_prevState` is required by `useActionState` but typically unused
- Always call `revalidatePath()` after mutations
- `redirect()` throws internally (Next.js behavior), so it must be the last call
- For update actions, bind the `id` parameter: `updateProduct.bind(null, id)`

## Page Pattern

Source: `frontend/app/dashboard/invoices/page.tsx`

```typescript
import { Suspense } from 'react';
import { Metadata } from 'next';
import Search from '@/app/ui/search';
import Table from '@/app/ui/products/table';
import Pagination from '@/app/ui/products/pagination';
import { CreateProduct } from '@/app/ui/products/buttons';
import { ProductsTableSkeleton } from '@/app/ui/skeletons';
import { fetchProductsPages } from '@/app/lib/data';

export const metadata: Metadata = {
  title: 'Products',
};

export default async function Page(props: {
  searchParams?: Promise<{
    query?: string;
    page?: string;
  }>;
}) {
  const searchParams = await props.searchParams;
  const query = searchParams?.query || '';
  const currentPage = Number(searchParams?.page) || 1;
  const totalPages = await fetchProductsPages(query);

  return (
    <div className="w-full">
      <div className="flex w-full items-center justify-between">
        <h1 className="text-2xl">Products</h1>
      </div>
      <div className="mt-4 flex items-center justify-between gap-2 md:mt-8">
        <Search placeholder="Search products..." />
        <CreateProduct />
      </div>
      <Suspense key={query + currentPage} fallback={<ProductsTableSkeleton />}>
        <Table query={query} currentPage={currentPage} />
      </Suspense>
      <div className="mt-5 flex w-full justify-center">
        <Pagination totalPages={totalPages} />
      </div>
    </div>
  );
}
```

Key points:

- Pages are async server components (no `'use client'`)
- `searchParams` is a `Promise` in Next.js App Router - must be awaited
- Use `Suspense` with skeleton fallbacks around data-fetching components
- Use `key={query + currentPage}` on Suspense to trigger re-render on param changes
- Export `metadata` for page title

## Form Component Pattern

Source: `frontend/app/ui/invoices/create-form.tsx`

```typescript
'use client';

import { useActionState } from 'react';
import Link from 'next/link';
import { createProduct, State } from '@/app/lib/actions';
import { Button } from '@/app/ui/button';

export default function CreateForm() {
  const initialState: State = { message: null, errors: {} };
  const [state, formAction] = useActionState(createProduct, initialState);

  return (
    <form action={formAction}>
      {/* Form fields that read state.errors for validation messages */}
      <div className="mt-6 flex justify-end gap-4">
        <Link
          href="/dashboard/products"
          className="flex h-10 items-center rounded-lg bg-gray-100 px-4 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-200"
        >
          Cancel
        </Link>
        <Button type="submit">Create Product</Button>
      </div>
    </form>
  );
}
```

Key points:

- Must be `'use client'` (uses React hooks)
- `useActionState` binds a server action to form state
- `state.errors?.fieldName` contains Zod validation error arrays
- Cancel link navigates back to list page
- For edit forms, use `updateProduct.bind(null, id)` to partially apply the ID

## Navigation

Source: `frontend/app/ui/dashboard/nav-links.tsx`

```typescript
const links = [
  { name: "Overview", href: "/dashboard", icon: HomeIcon },
  {
    name: "Invoices",
    href: "/dashboard/invoices",
    icon: DocumentDuplicateIcon,
  },
  { name: "Customers", href: "/dashboard/customers", icon: UserGroupIcon },
  // Add new links here:
  // { name: 'Products', href: '/dashboard/products', icon: CubeIcon },
];
```

Import icons from `@heroicons/react/24/outline`. Active state is applied automatically based on `usePathname()`.
