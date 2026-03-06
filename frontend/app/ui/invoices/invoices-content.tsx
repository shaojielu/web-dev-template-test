import Pagination from '@/app/ui/invoices/pagination';
import InvoicesTable from '@/app/ui/invoices/table';
import { fetchFilteredInvoicesWithCount } from '@/app/lib/data';

export default async function InvoicesContent({
  query,
  currentPage,
}: {
  query: string;
  currentPage: number;
}) {
  const { invoices, totalPages } = await fetchFilteredInvoicesWithCount(
    query,
    currentPage,
  );

  return (
    <>
      <InvoicesTable invoices={invoices} />
      <div className="mt-5 flex w-full justify-center">
        <Pagination totalPages={totalPages} />
      </div>
    </>
  );
}
