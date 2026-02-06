'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Save, Globe } from 'lucide-react';
import { useAuth, useMyTutorProfile, useUpdateAvailability } from '@/lib/hooks';
import { tutorsApi } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Skeleton,
  Badge,
} from '@/components/ui';
import { AvailabilityGrid, AvailabilityPreview } from '@/components/profile/availability-grid';

interface TimeSlot {
  id?: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
}

const COMMON_TIMEZONES = [
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'America/Anchorage', label: 'Alaska Time (AKT)' },
  { value: 'Pacific/Honolulu', label: 'Hawaii Time (HT)' },
  { value: 'Europe/London', label: 'London (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Paris (CET/CEST)' },
  { value: 'Europe/Berlin', label: 'Berlin (CET/CEST)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Asia/Shanghai', label: 'Shanghai (CST)' },
  { value: 'Asia/Singapore', label: 'Singapore (SGT)' },
  { value: 'Asia/Dubai', label: 'Dubai (GST)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEST/AEDT)' },
  { value: 'UTC', label: 'UTC' },
];

function AvailabilitySkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-10 rounded-xl" />
        <Skeleton className="h-8 w-48" />
      </div>
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardContent className="p-6">
              <div className="grid sm:grid-cols-2 gap-4">
                {Array.from({ length: 7 }).map((_, i) => (
                  <Skeleton key={i} className="h-32" />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    </div>
  );
}

export default function AvailabilityPage() {
  const { user, isLoading: authLoading } = useAuth();
  const { data: tutorProfile, isLoading: profileLoading } = useMyTutorProfile();
  const updateAvailability = useUpdateAvailability();
  const router = useRouter();

  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [timezone, setTimezone] = useState(
    Intl.DateTimeFormat().resolvedOptions().timeZone
  );
  const [hasChanges, setHasChanges] = useState(false);

  const { data: existingAvailability, isLoading: availabilityLoading } = useQuery({
    queryKey: ['my-availability'],
    queryFn: async () => {
      if (!tutorProfile?.id) return [];
      return tutorsApi.getAvailability(tutorProfile.id);
    },
    enabled: !!tutorProfile?.id,
  });

  useEffect(() => {
    if (existingAvailability && existingAvailability.length > 0) {
      setSlots(
        existingAvailability.map((slot) => ({
          id: slot.id,
          day_of_week: slot.day_of_week,
          start_time: slot.start_time,
          end_time: slot.end_time,
        }))
      );
    }
  }, [existingAvailability]);

  const handleSlotsChange = (newSlots: TimeSlot[]) => {
    setSlots(newSlots);
    setHasChanges(true);
  };

  const handleTimezoneChange = (newTimezone: string) => {
    setTimezone(newTimezone);
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      await updateAvailability.mutateAsync(
        slots.map((slot) => ({
          day_of_week: slot.day_of_week,
          start_time: slot.start_time,
          end_time: slot.end_time,
        }))
      );
      setHasChanges(false);
      router.push('/profile');
    } catch (error) {
      console.error('Failed to update availability:', error);
    }
  };

  if (authLoading || profileLoading || availabilityLoading) {
    return <AvailabilitySkeleton />;
  }

  if (user?.role !== 'tutor') {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Availability
          </h1>
        </div>
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-slate-500">
              Only tutors can manage availability.
            </p>
            <Link href="/profile">
              <Button className="mt-4">Back to Profile</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
        <div className="flex items-center gap-3 sm:gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
              Manage Availability
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Set your weekly availability for tutoring sessions
            </p>
          </div>
        </div>
        <div className="flex gap-2 ml-11 sm:ml-0">
          <Link href="/profile">
            <Button variant="outline">Cancel</Button>
          </Link>
          <Button
            onClick={handleSave}
            loading={updateAvailability.isPending}
            disabled={!hasChanges}
          >
            <Save className="h-4 w-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        <div className="lg:col-span-2 space-y-4 sm:space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Timezone</CardTitle>
                <Badge variant="default">
                  <Globe className="h-3 w-3 mr-1" />
                  {timezone}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Your Timezone
                </label>
                <select
                  value={timezone}
                  onChange={(e) => handleTimezoneChange(e.target.value)}
                  className="flex h-10 w-full rounded-xl border bg-white px-3 py-2 text-sm border-slate-200 dark:border-slate-700 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {COMMON_TIMEZONES.map((tz) => (
                    <option key={tz.value} value={tz.value}>
                      {tz.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-slate-500">
                  All times will be displayed in this timezone
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Weekly Schedule</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <div className="min-w-[320px]">
                <AvailabilityGrid
                  slots={slots}
                  onChange={handleSlotsChange}
                  disabled={updateAvailability.isPending}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4 sm:space-y-6">
          <AvailabilityPreview slots={slots} />

          <Card>
            <CardHeader>
              <CardTitle>Tips</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  <strong>Be consistent</strong> - Regular availability helps students plan their sessions better.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-green-50 dark:bg-green-900/20">
                <p className="text-sm text-green-700 dark:text-green-300">
                  <strong>Buffer time</strong> - Consider leaving gaps between slots for breaks.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-900/20">
                <p className="text-sm text-amber-700 dark:text-amber-300">
                  <strong>Time zones</strong> - Your availability will be shown to students in their local time.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
