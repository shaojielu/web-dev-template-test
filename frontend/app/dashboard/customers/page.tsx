import CustomersTable from '@/app/ui/customers/table';
import { fetchCustomersSummary } from '@/app/lib/data';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Customers',
};

export default async function Page(props: {
  searchParams?: Promise<{
    query?: string;
  }>;
}) {
  const searchParams = await props.searchParams;
  const query = searchParams?.query || '';
  const customers = await fetchCustomersSummary(query);

  return <CustomersTable customers={customers} />;
}
