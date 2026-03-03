export type Revenue = {
  month: string;
  revenue: number;
};

export type LatestInvoice = {
  id: string;
  name: string;
  email: string;
  amount: string;
  image_url: string;
};

export type Invoice = {
  id: string;
  customer_id: string;
  amount: string;
  status: 'pending' | 'paid';
  date: string;
  name: string;
  email: string;
  image_url: string;
};

export type InvoiceForm = {
  id: string;
  customer_id: string;
  amount: number;
  status: 'pending' | 'paid';
};

export type CustomerField = {
  id: string;
  name: string;
};

export type FormattedCustomersTable = {
  id: string;
  name: string;
  email: string;
  image_url: string;
  total_invoices: number;
  total_pending: string;
  total_paid: string;
};

export type CustomersTableType = FormattedCustomersTable;
