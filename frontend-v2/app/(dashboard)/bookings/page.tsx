'use client';

import { useState, useMemo, useCallback } from 'react';
import Link from 'next/link';
import { Plus, Calendar, Filter, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import {
  useBookings,
  useCancelBooking,
  useConfirmBooking,
  useAuth,
} from '@/lib/hooks';
import {
  Card,
  CardHeader,
  CardContent,
  Button,
  Input,
  Skeleton,
} from '@/components/ui';
import { BookingCard } from '@/components/bookings';
import type { SessionState } from '@/types';

type TabKey = 'upcoming' | 'past' | 'cancelled';

const BOOKINGS_PER_PAGE = 10;

const tabs: { key: TabKey; label: string; states: SessionState[] }[] = [
  {
    key: 'upcoming',
    label: 'Upcoming',
    states: ['REQUESTED', 'SCHEDULED', 'ACTIVE'],
  },
  {
    key: 'past',
    label: 'Past',
    states: ['ENDED'],
  },
  {
    key: 'cancelled',
    label: 'Cancelled',
    states: ['CANCELLED', 'EXPIRED'],
  },
];

export default function BookingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabKey>('upcoming');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const currentTabStates = tabs.find((t) => t.key === activeTab)?.states ?? [];

  const { data: bookings, isLoading } = useBookings({
    from_date: fromDate || undefined,
    to_date: toDate || undefined,
    page_size: 50,
  });

  const cancelBooking = useCancelBooking();
  const confirmBooking = useConfirmBooking();

  const bookingItems = bookings?.bookings ?? [];

  const tabCounts = useMemo(() => {
    const counts: Record<TabKey, number> = { upcoming: 0, past: 0, cancelled: 0 };
    for (const b of bookingItems) {
      for (const tab of tabs) {
        if (tab.states.includes(b.session_state)) {
          counts[tab.key]++;
          break;
        }
      }
    }
    return counts;
  }, [bookingItems]);

  const filteredBookings = useMemo(
    () => bookingItems.filter((b) => currentTabStates.includes(b.session_state)),
    [bookingItems, currentTabStates]
  );

  const totalPages = Math.max(1, Math.ceil(filteredBookings.length / BOOKINGS_PER_PAGE));
  const paginatedBookings = useMemo(() => {
    const start = (currentPage - 1) * BOOKINGS_PER_PAGE;
    return filteredBookings.slice(start, start + BOOKINGS_PER_PAGE);
  }, [filteredBookings, currentPage]);

  const handleTabChange = useCallback((tabKey: TabKey) => {
    setActiveTab(tabKey);
    setFromDate('');
    setToDate('');
    setCurrentPage(1);
  }, []);

  const handleCancel = (id: number) => {
    if (window.confirm('Are you sure you want to cancel this booking?')) {
      cancelBooking.mutate({ id });
    }
  };

  const handleConfirm = (id: number) => {
    confirmBooking.mutate(id);
  };

  const userRole = user?.role === 'tutor' ? 'tutor' : 'student';
  const isStudent = user?.role === 'student';

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            My Bookings
          </h1>
          <p className="text-slate-500">Manage your tutoring sessions</p>
        </div>
        {isStudent && (
          <Button asChild>
            <Link href="/bookings/new">
              <Plus className="h-4 w-4 mr-2" />
              New Booking
            </Link>
          </Button>
        )}
      </div>

      <Card>
        <CardHeader className="flex-col sm:flex-row gap-4">
          <div className="flex flex-wrap gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => handleTabChange(tab.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.key
                    ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {tab.label}
                {!isLoading && tabCounts[tab.key] > 0 && (
                  <span className={`ml-1.5 inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full text-xs font-medium ${
                    activeTab === tab.key
                      ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                      : 'bg-slate-200 text-slate-600 dark:bg-slate-600 dark:text-slate-300'
                  }`}>
                    {tabCounts[tab.key]}
                  </span>
                )}
              </button>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:ml-auto w-full sm:w-auto">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Filter className="h-4 w-4 text-slate-400 shrink-0" />
              <Input
                type="date"
                value={fromDate}
                onChange={(e) => { setFromDate(e.target.value); setCurrentPage(1); }}
                className="w-full sm:w-36"
                placeholder="From"
              />
              <span className="text-slate-400 shrink-0">-</span>
              <Input
                type="date"
                value={toDate}
                onChange={(e) => { setToDate(e.target.value); setCurrentPage(1); }}
                className="w-full sm:w-36"
                placeholder="To"
              />
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800"
                >
                  <div className="flex gap-4">
                    <Skeleton className="h-12 w-12 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-5 w-1/3" />
                      <Skeleton className="h-4 w-1/2" />
                      <Skeleton className="h-4 w-2/3" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : filteredBookings.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500 mb-4">
                No {activeTab} bookings found
              </p>
              {activeTab === 'upcoming' && isStudent && (
                <Button asChild variant="outline">
                  <Link href="/tutors">
                    <Search className="h-4 w-4 mr-2" />
                    Find a Tutor
                  </Link>
                </Button>
              )}
            </div>
          ) : (
            <>
              <div className="space-y-4">
                {paginatedBookings.map((booking) => (
                  <BookingCard
                    key={booking.id}
                    booking={booking}
                    userRole={userRole}
                    onCancel={handleCancel}
                    onConfirm={handleConfirm}
                  />
                ))}
              </div>

              {totalPages > 1 && (
                <div className="mt-6 flex items-center justify-between border-t border-slate-200 dark:border-slate-700 pt-4">
                  <p className="text-sm text-slate-500">
                    Showing {(currentPage - 1) * BOOKINGS_PER_PAGE + 1}
                    {' '}-{' '}
                    {Math.min(currentPage * BOOKINGS_PER_PAGE, filteredBookings.length)}
                    {' '}of {filteredBookings.length}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={currentPage === 1}
                      onClick={() => setCurrentPage((p) => p - 1)}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm text-slate-600 dark:text-slate-400">
                      Page {currentPage} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={currentPage === totalPages}
                      onClick={() => setCurrentPage((p) => p + 1)}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
