'use client';

import Link from 'next/link';
import { Search, Calendar, Clock, Wallet, Package } from 'lucide-react';
import { useAuth, useBookings, useBookingStats } from '@/lib/hooks';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Skeleton,
  SkeletonCard,
} from '@/components/ui';

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
            <Icon className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {value}
            </p>
            <p className="text-sm text-slate-500">{label}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function StudentDashboard() {
  const { user } = useAuth();
  const { data: stats, isLoading: statsLoading } = useBookingStats();
  const { data: bookings, isLoading: bookingsLoading } = useBookings({
    status: 'confirmed',
    page_size: 3,
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Welcome back, {user?.first_name}!
          </h1>
          <p className="text-slate-500">Ready to continue learning?</p>
        </div>
        <div className="flex gap-3">
          <Button asChild>
            <Link href="/tutors">
              <Search className="h-4 w-4 mr-2" />
              Find a Tutor
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statsLoading ? (
          <>
            <Skeleton className="h-24 rounded-2xl" />
            <Skeleton className="h-24 rounded-2xl" />
            <Skeleton className="h-24 rounded-2xl" />
            <Skeleton className="h-24 rounded-2xl" />
          </>
        ) : (
          <>
            <StatCard
              label="Upcoming Sessions"
              value={stats?.upcoming ?? 0}
              icon={Calendar}
            />
            <StatCard
              label="Hours Learned"
              value={stats?.total_hours ?? 0}
              icon={Clock}
            />
            <StatCard label="Wallet Balance" value="$0" icon={Wallet} />
            <StatCard label="Package Credits" value={0} icon={Package} />
          </>
        )}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Sessions</CardTitle>
              <Link
                href="/student/bookings"
                className="text-sm text-primary-600 hover:underline"
              >
                View all
              </Link>
            </CardHeader>
            <CardContent>
              {bookingsLoading ? (
                <div className="space-y-3">
                  <SkeletonCard />
                  <SkeletonCard />
                </div>
              ) : bookings?.items.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">No upcoming sessions</p>
                  <Button asChild variant="link" className="mt-2">
                    <Link href="/tutors">Find a tutor</Link>
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {bookings?.items.map((booking) => (
                    <div
                      key={booking.id}
                      className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium text-slate-900 dark:text-white">
                            {booking.subject?.name}
                          </p>
                          <p className="text-sm text-slate-500">
                            with {booking.tutor?.display_name}
                          </p>
                        </div>
                        <Button size="sm" variant="outline">
                          View
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button asChild variant="ghost" className="w-full justify-start">
                <Link href="/tutors">
                  <Search className="h-4 w-4 mr-3" />
                  Browse Tutors
                </Link>
              </Button>
              <Button asChild variant="ghost" className="w-full justify-start">
                <Link href="/student/bookings">
                  <Calendar className="h-4 w-4 mr-3" />
                  My Bookings
                </Link>
              </Button>
              <Button asChild variant="ghost" className="w-full justify-start">
                <Link href="/messages">
                  <Calendar className="h-4 w-4 mr-3" />
                  Messages
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
