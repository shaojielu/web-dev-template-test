import { ApiError, apiFetch } from '@/app/lib/api';
import {
  CustomerField,
  FormattedCustomersTable,
  Invoice,
  InvoiceForm,
  LatestInvoice,
  Revenue,
} from '@/app/lib/definitions';

const ITEMS_PER_PAGE = 6;

export async function fetchRevenue(): Promise<Revenue[]> {
  return apiFetch<Revenue[]>('/api/v1/dashboard/revenue');
}

export async function fetchLatestInvoices(): Promise<LatestInvoice[]> {
  return apiFetch<LatestInvoice[]>('/api/v1/invoices/latest');
}

export async function fetchCardData() {
  const data = await apiFetch<{
    number_of_invoices: number;
    number_of_customers: number;
    total_paid_invoices: string;
    total_pending_invoices: string;
  }>('/api/v1/dashboard/cards');

  return {
    numberOfInvoices: data.number_of_invoices,
    numberOfCustomers: data.number_of_customers,
    totalPaidInvoices: data.total_paid_invoices,
    totalPendingInvoices: data.total_pending_invoices,
  };
}

export async function fetchFilteredInvoices(
  query: string,
  currentPage: number,
): Promise<Invoice[]> {
  const result = await fetchFilteredInvoicesWithCount(query, currentPage);
  return result.invoices;
}

export async function fetchInvoicesPages(query: string): Promise<number> {
  const result = await fetchFilteredInvoicesWithCount(query, 1);
  return result.totalPages;
}

export async function fetchFilteredInvoicesWithCount(
  query: string,
  currentPage: number,
): Promise<{ invoices: Invoice[]; totalPages: number }> {
  const safePage = Math.max(1, Math.floor(currentPage));
  const skip = (safePage - 1) * ITEMS_PER_PAGE;
  const params = new URLSearchParams();
  params.set('skip', skip.toString());
  params.set('limit', ITEMS_PER_PAGE.toString());
  if (query) {
    params.set('query', query);
  }

  const data = await apiFetch<{ data: Invoice[]; count: number }>(
    `/api/v1/invoices/?${params.toString()}`,
  );
  const totalPages = Math.ceil(data.count / ITEMS_PER_PAGE);
  return {
    invoices: data.data,
    totalPages: totalPages > 0 ? totalPages : 1,
  };
}

export async function fetchInvoiceById(id: string): Promise<InvoiceForm | null> {
  try {
    const invoice = await apiFetch<Invoice>(`/api/v1/invoices/${id}`);
    return {
      id: invoice.id,
      customer_id: invoice.customer_id,
      amount: Number.parseFloat(invoice.amount),
      status: invoice.status,
    };
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function fetchCustomers(): Promise<CustomerField[]> {
  const data = await apiFetch<{ data: CustomerField[]; count: number }>(
    '/api/v1/customers/?skip=0&limit=500',
  );
  return data.data.map((customer) => ({
    id: customer.id,
    name: customer.name,
  }));
}

export async function fetchCustomersSummary(
  query: string,
): Promise<FormattedCustomersTable[]> {
  const params = new URLSearchParams();
  if (query) {
    params.set('query', query);
  }

  const data = await apiFetch<{
    data: FormattedCustomersTable[];
    count: number;
  }>(`/api/v1/customers/summary?${params.toString()}`);
  return data.data;
}
