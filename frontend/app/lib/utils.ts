import { Revenue } from '@/app/lib/definitions';

export function formatCurrency(amount: number | string) {
  const numericAmount =
    typeof amount === 'number' ? amount : Number.parseFloat(amount);
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(Number.isFinite(numericAmount) ? numericAmount : 0);
}

export function formatDateToLocal(
  dateStr: string,
  locale: string = 'en-US',
) {
  const date = new Date(dateStr);
  return new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(date);
}

export function generateYAxis(revenue: Revenue[]) {
  const highestRecord = Math.max(...revenue.map((month) => month.revenue), 0);
  const topLabel = Math.ceil(highestRecord / 1000) * 1000 || 1000;

  const yAxisLabels = [] as string[];
  for (let i = topLabel; i >= 0; i -= topLabel / 4) {
    yAxisLabels.push(formatCurrency(i));
  }

  return { yAxisLabels, topLabel };
}

export function generatePagination(currentPage: number, totalPages: number) {
  currentPage = Math.max(1, Math.min(currentPage, totalPages));

  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  if (currentPage <= 3) {
    return [1, 2, 3, '...', totalPages - 1, totalPages];
  }

  if (currentPage >= totalPages - 2) {
    return [1, 2, '...', totalPages - 2, totalPages - 1, totalPages];
  }

  return [1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages];
}
