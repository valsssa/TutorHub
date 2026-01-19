"use client";

/**
 * Reusable pagination component
 */
interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  hasNext: boolean;
  hasPrev: boolean;
  totalItems?: number;
}

export default function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  hasNext,
  hasPrev,
  totalItems,
}: PaginationProps) {
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisible = 7; // Show max 7 page numbers

    if (totalPages <= maxVisible) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);

      if (currentPage > 3) {
        pages.push('...');
      }

      // Show pages around current page
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (currentPage < totalPages - 2) {
        pages.push('...');
      }

      // Always show last page
      pages.push(totalPages);
    }

    return pages;
  };

  return (
    <div className="flex flex-col items-center gap-4 mt-8">
      {/* Page info */}
      {totalItems !== undefined && (
        <p className="text-sm text-slate-600">
          Showing page <span className="font-semibold">{currentPage}</span> of{' '}
          <span className="font-semibold">{totalPages}</span>
          {' '}({totalItems} total)
        </p>
      )}

      {/* Pagination controls */}
      <div className="flex items-center gap-2">
        {/* Previous button */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={!hasPrev}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            hasPrev
              ? 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400'
              : 'bg-slate-100 text-slate-400 cursor-not-allowed'
          }`}
          aria-label="Previous page"
        >
          ← Previous
        </button>

        {/* Page numbers */}
        <div className="hidden sm:flex items-center gap-1">
          {getPageNumbers().map((page, idx) => {
            if (page === '...') {
              return (
                <span key={`ellipsis-${idx}`} className="px-2 text-slate-400">
                  ...
                </span>
              );
            }

            const pageNum = page as number;
            const isActive = pageNum === currentPage;

            return (
              <button
                key={pageNum}
                onClick={() => onPageChange(pageNum)}
                className={`min-w-[40px] h-10 rounded-lg font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-sky-500 to-blue-500 text-white shadow-lg'
                    : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400'
                }`}
                aria-label={`Page ${pageNum}`}
                aria-current={isActive ? 'page' : undefined}
              >
                {pageNum}
              </button>
            );
          })}
        </div>

        {/* Mobile: Current page indicator */}
        <div className="sm:hidden px-4 py-2 bg-white border border-slate-300 rounded-lg text-slate-700 font-medium">
          {currentPage} / {totalPages}
        </div>

        {/* Next button */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={!hasNext}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            hasNext
              ? 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400'
              : 'bg-slate-100 text-slate-400 cursor-not-allowed'
          }`}
          aria-label="Next page"
        >
          Next →
        </button>
      </div>
    </div>
  );
}
