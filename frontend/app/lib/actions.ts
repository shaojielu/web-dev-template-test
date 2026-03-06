'use server';

import { revalidatePath } from 'next/cache';
import { cookies, headers } from 'next/headers';
import { redirect } from 'next/navigation';
import { z } from 'zod';

import { apiFetch, API_BASE_URL } from '@/app/lib/api';

function sanitizeRedirectTo(value: FormDataEntryValue | null): string {
  if (!value) {
    return '/dashboard';
  }
  const redirectTo = value.toString().trim();
  if (!redirectTo.startsWith('/') || redirectTo.startsWith('//')) {
    return '/dashboard';
  }
  if (redirectTo.includes('\\')) {
    return '/dashboard';
  }
  return redirectTo;
}

const InvoiceSchema = z.object({
  customerId: z.string().uuid({ message: 'Please select a customer.' }),
  amount: z.coerce.number().gt(0, { message: 'Amount must be greater than 0.' }),
  status: z.enum(['pending', 'paid'], {
    errorMap: () => ({ message: 'Please select a status.' }),
  }),
});

export type State = {
  errors?: {
    customerId?: string[];
    amount?: string[];
    status?: string[];
  };
  message?: string | null;
};

export async function authenticate(
  _prevState: string | undefined,
  formData: FormData,
): Promise<string | undefined> {
  const email = formData.get('email');
  const password = formData.get('password');
  const redirectTo = sanitizeRedirectTo(formData.get('redirectTo'));

  if (!email || !password) {
    return 'Please enter both email and password.';
  }

  const body = new URLSearchParams();
  body.set('username', email.toString());
  body.set('password', password.toString());

  const response = await fetch(`${API_BASE_URL}/api/v1/login/access-token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body,
    cache: 'no-store',
  });

  if (!response.ok) {
    return 'Incorrect email or password.';
  }

  const data = (await response.json()) as {
    access_token?: string;
    refresh_token?: string;
  };
  if (!data.access_token) {
    return 'Login failed. Please try again.';
  }

  // Only mark cookie as secure when the request is served over HTTPS.
  const requestHeaders = await headers();
  const forwardedProto = requestHeaders.get('x-forwarded-proto');
  const isSecureRequest = forwardedProto
    ?.split(',')
    .some((value) => value.trim().toLowerCase() === 'https');

  const cookieStore = await cookies();
  cookieStore.set('access_token', data.access_token, {
    httpOnly: true,
    sameSite: 'strict',
    secure: Boolean(isSecureRequest),
    path: '/',
  });

  if (data.refresh_token) {
    cookieStore.set('refresh_token', data.refresh_token, {
      httpOnly: true,
      sameSite: 'strict',
      secure: Boolean(isSecureRequest),
      path: '/',
      maxAge: 60 * 60 * 24 * 7, // 7 days
    });
  }

  redirect(redirectTo);
}

export async function signOut() {
  const cookieStore = await cookies();
  cookieStore.delete('access_token');
  cookieStore.delete('refresh_token');
  redirect('/login');
}

export async function createInvoice(
  _prevState: State,
  formData: FormData,
): Promise<State> {
  const validatedFields = InvoiceSchema.safeParse({
    customerId: formData.get('customerId'),
    amount: formData.get('amount'),
    status: formData.get('status'),
  });

  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
      message: 'Missing fields. Failed to create invoice.',
    };
  }

  const { customerId, amount, status } = validatedFields.data;

  await apiFetch('/api/v1/invoices/', {
    method: 'POST',
    body: JSON.stringify({
      customer_id: customerId,
      amount,
      status,
    }),
  });

  revalidatePath('/dashboard/invoices');
  redirect('/dashboard/invoices');
}

export async function updateInvoice(
  id: string,
  _prevState: State,
  formData: FormData,
): Promise<State> {
  const validatedFields = InvoiceSchema.safeParse({
    customerId: formData.get('customerId'),
    amount: formData.get('amount'),
    status: formData.get('status'),
  });

  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
      message: 'Missing fields. Failed to update invoice.',
    };
  }

  const { customerId, amount, status } = validatedFields.data;

  await apiFetch(`/api/v1/invoices/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({
      customer_id: customerId,
      amount,
      status,
    }),
  });

  revalidatePath('/dashboard/invoices');
  redirect('/dashboard/invoices');
}

export async function deleteInvoice(id: string) {
  await apiFetch(`/api/v1/invoices/${id}`, {
    method: 'DELETE',
  });
  revalidatePath('/dashboard/invoices');
}
