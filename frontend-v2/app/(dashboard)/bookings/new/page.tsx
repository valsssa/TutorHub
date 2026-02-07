'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Calendar,
  Clock,
  DollarSign,
  User,
  BookOpen,
  MessageSquare,
  X,
  CheckCircle,
} from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useCreateBooking, useTutors, useSubjects, useTutor } from '@/lib/hooks';
import {
  createBookingSchema,
  type CreateBookingFormData,
} from '@/lib/validators';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
  Button,
  Input,
  Avatar,
  Skeleton,
} from '@/components/ui';
import { formatCurrency } from '@/lib/utils';
import { useToast } from '@/lib/stores/ui-store';

const durationOptions = [
  { value: '30', label: '30 minutes' },
  { value: '60', label: '1 hour' },
  { value: '90', label: '1.5 hours' },
  { value: '120', label: '2 hours' },
];

export default function NewBookingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tutorIdParam = searchParams.get('tutor');

  const toast = useToast();
  const [selectedTutorId, setSelectedTutorId] = useState<number | null>(
    tutorIdParam ? Number(tutorIdParam) : null
  );
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingFormData, setPendingFormData] = useState<CreateBookingFormData | null>(null);

  const { data: tutors, isLoading: tutorsLoading } = useTutors({ page_size: 100 });
  const { data: subjects, isLoading: subjectsLoading } = useSubjects();
  const { data: selectedTutor } = useTutor(selectedTutorId ?? 0);
  const createBooking = useCreateBooking();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CreateBookingFormData>({
    resolver: zodResolver(createBookingSchema),
    defaultValues: {
      tutor_id: selectedTutorId ?? undefined,
      duration: '60',
    },
  });

  useEffect(() => {
    if (selectedTutorId) {
      setValue('tutor_id', selectedTutorId);
    }
  }, [selectedTutorId, setValue]);

  const watchTutorId = watch('tutor_id');
  const watchDuration = watch('duration');
  const watchSubjectId = watch('subject_id');
  const watchStartTime = watch('start_time');

  useEffect(() => {
    if (watchTutorId && watchTutorId !== selectedTutorId) {
      setSelectedTutorId(watchTutorId);
    }
  }, [watchTutorId, selectedTutorId]);

  const minDateTime = useMemo(() => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }, []);

  const hourlyRate = selectedTutor?.hourly_rate ?? 0;
  const durationMinutes = Number(watchDuration) || 60;
  const estimatedPrice = (hourlyRate * durationMinutes) / 60;

  const onSubmit = (data: CreateBookingFormData) => {
    setPendingFormData(data);
    setShowConfirmDialog(true);
  };

  const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  const handleConfirmBooking = () => {
    if (!pendingFormData) return;
    // Convert local datetime to UTC ISO string for the backend
    const startAtUtc = new Date(pendingFormData.start_time).toISOString();
    createBooking.mutate(
      {
        tutor_profile_id: pendingFormData.tutor_id,
        subject_id: pendingFormData.subject_id,
        start_at: startAtUtc,
        duration_minutes: Number(pendingFormData.duration),
        notes_student: pendingFormData.message,
      },
      {
        onSuccess: () => {
          setShowConfirmDialog(false);
          toast.success('Booking request submitted successfully!');
          router.push('/bookings');
        },
        onError: () => {
          setShowConfirmDialog(false);
        },
      }
    );
  };

  const selectedSubjectName = useMemo(() => {
    const subjectId = Number(pendingFormData?.subject_id);
    const allSubjects = selectedTutor?.subjects ?? subjects ?? [];
    return allSubjects.find((s) => s.id === subjectId)?.name ?? '-';
  }, [pendingFormData?.subject_id, selectedTutor?.subjects, subjects]);

  const confirmDurationLabel = useMemo(() => {
    return durationOptions.find((d) => d.value === pendingFormData?.duration)?.label ?? '-';
  }, [pendingFormData?.duration]);

  const confirmStartTime = useMemo(() => {
    if (!pendingFormData?.start_time) return '-';
    const date = new Date(pendingFormData.start_time);
    return date.toLocaleString(undefined, {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }, [pendingFormData?.start_time]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button asChild variant="ghost" size="icon">
          <Link href="/bookings">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Book a Session
          </h1>
          <p className="text-slate-500">Schedule a tutoring session</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Select Tutor
                </CardTitle>
              </CardHeader>
              <CardContent>
                {tutorsLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} className="h-20 rounded-xl" />
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {tutors?.items.map((tutor) => (
                      <label
                        key={tutor.id}
                        className={`flex items-center gap-3 sm:gap-4 p-3 sm:p-4 rounded-xl border-2 cursor-pointer transition-all ${
                          selectedTutorId === tutor.id
                            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                            : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                        }`}
                      >
                        <input
                          type="radio"
                          {...register('tutor_id', { valueAsNumber: true })}
                          value={tutor.id}
                          className="sr-only"
                        />
                        <Avatar
                          src={tutor.avatar_url}
                          name={tutor.display_name}
                          size="lg"
                          className="shrink-0"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-slate-900 dark:text-white truncate">
                            {tutor.display_name}
                          </p>
                          {tutor.headline && (
                            <p className="text-sm text-slate-500 truncate">
                              {tutor.headline}
                            </p>
                          )}
                          <div className="flex items-center gap-2 mt-1 text-sm">
                            <span className="text-amber-500">
                              {'*'.repeat(Math.round(tutor.average_rating))}
                            </span>
                            <span className="text-slate-500 truncate">
                              ({tutor.total_reviews ?? 0} reviews)
                            </span>
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <p className="font-semibold text-slate-900 dark:text-white text-sm sm:text-base">
                            {formatCurrency(tutor.hourly_rate, tutor.currency)}
                          </p>
                          <p className="text-xs text-slate-500">per hour</p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
                {errors.tutor_id && (
                  <p className="mt-2 text-sm text-red-500">
                    {errors.tutor_id.message}
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  Select Subject
                </CardTitle>
              </CardHeader>
              <CardContent>
                {subjectsLoading ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                      <Skeleton key={i} className="h-12 rounded-xl" />
                    ))}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                    {(selectedTutor?.subjects ?? subjects ?? []).map(
                      (subject) => (
                        <label
                          key={subject.id}
                          className={`flex items-center justify-center p-3 rounded-xl border-2 cursor-pointer text-sm font-medium transition-all ${
                            Number(watchSubjectId) === subject.id
                              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
                              : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 text-slate-700 dark:text-slate-300'
                          }`}
                        >
                          <input
                            type="radio"
                            {...register('subject_id', { valueAsNumber: true })}
                            value={subject.id}
                            className="sr-only"
                          />
                          {subject.name}
                        </label>
                      )
                    )}
                  </div>
                )}
                {errors.subject_id && (
                  <p className="mt-2 text-sm text-red-500">
                    {errors.subject_id.message}
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Date & Time
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Input
                    type="datetime-local"
                    label="Select Date & Time"
                    min={minDateTime}
                    {...register('start_time')}
                    error={errors.start_time?.message}
                  />
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    Your timezone: {userTimezone}
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 block">
                    Duration
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {durationOptions.map((option) => (
                      <label
                        key={option.value}
                        className={`flex items-center justify-center p-3 rounded-xl border-2 cursor-pointer text-sm font-medium transition-all ${
                          watchDuration === option.value
                            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
                            : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 text-slate-700 dark:text-slate-300'
                        }`}
                      >
                        <input
                          type="radio"
                          {...register('duration')}
                          value={option.value}
                          className="sr-only"
                        />
                        <Clock className="h-4 w-4 mr-2" />
                        {option.label}
                      </label>
                    ))}
                  </div>
                  {errors.duration && (
                    <p className="mt-2 text-sm text-red-500">
                      {errors.duration.message}
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Message to Tutor (Optional)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <textarea
                  {...register('message')}
                  rows={4}
                  placeholder="Let the tutor know what you'd like to focus on..."
                  className="flex w-full rounded-xl border bg-white px-3 py-2 text-sm
                    border-slate-200 dark:border-slate-700 dark:bg-slate-900
                    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                    placeholder:text-slate-400 dark:placeholder:text-slate-500
                    disabled:cursor-not-allowed disabled:opacity-50 resize-none"
                />
                {errors.message && (
                  <p className="mt-2 text-sm text-red-500">
                    {errors.message.message}
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="lg:sticky lg:top-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5" />
                  Booking Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {selectedTutor ? (
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
                    <Avatar
                      src={selectedTutor.avatar_url}
                      name={selectedTutor.display_name}
                      size="md"
                    />
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">
                        {selectedTutor.display_name}
                      </p>
                      <p className="text-sm text-slate-500">
                        {formatCurrency(
                          selectedTutor.hourly_rate,
                          selectedTutor.currency
                        )}
                        /hr
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800 text-center text-slate-500">
                    Select a tutor to see pricing
                  </div>
                )}

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Duration</span>
                    <span className="font-medium text-slate-900 dark:text-white">
                      {durationOptions.find((d) => d.value === watchDuration)
                        ?.label ?? '-'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Hourly Rate</span>
                    <span className="font-medium text-slate-900 dark:text-white">
                      {selectedTutor
                        ? formatCurrency(
                            selectedTutor.hourly_rate,
                            selectedTutor.currency
                          )
                        : '-'}
                    </span>
                  </div>
                </div>

                <hr className="border-slate-200 dark:border-slate-700" />

                <div className="flex justify-between text-lg">
                  <span className="font-semibold text-slate-900 dark:text-white">
                    Total
                  </span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {selectedTutor
                      ? formatCurrency(
                          estimatedPrice,
                          selectedTutor.currency
                        )
                      : '-'}
                  </span>
                </div>
              </CardContent>
              <CardFooter>
                <Button
                  type="submit"
                  className="w-full"
                  loading={createBooking.isPending}
                  disabled={!selectedTutorId || !watchSubjectId || !watchStartTime}
                >
                  Confirm Booking
                </Button>
              </CardFooter>
            </Card>

            <Card>
              <CardContent className="p-4">
                <h4 className="font-medium text-slate-900 dark:text-white mb-2">
                  Booking Policy
                </h4>
                <ul className="space-y-2 text-sm text-slate-500">
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">*</span>
                    Free cancellation up to 24 hours before
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">*</span>
                    Full refund if tutor doesn&apos;t show
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">*</span>
                    Secure payment processing
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>

      {showConfirmDialog && pendingFormData && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div
            className="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700"
            role="dialog"
            aria-modal="true"
            aria-label="Confirm booking"
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                Confirm Your Booking
              </h2>
              <button
                onClick={() => setShowConfirmDialog(false)}
                className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                aria-label="Close confirmation dialog"
              >
                <X className="h-5 w-5 text-slate-400" />
              </button>
            </div>

            <div className="px-6 py-5 space-y-4">
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Please review your booking details before confirming.
              </p>

              {selectedTutor && (
                <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
                  <Avatar
                    src={selectedTutor.avatar_url}
                    name={selectedTutor.display_name}
                    size="md"
                  />
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">
                      {selectedTutor.display_name}
                    </p>
                    <p className="text-sm text-slate-500">
                      {formatCurrency(selectedTutor.hourly_rate, selectedTutor.currency)}/hr
                    </p>
                  </div>
                </div>
              )}

              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Subject</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {selectedSubjectName}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Date & Time</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {confirmStartTime}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Duration</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {confirmDurationLabel}
                  </span>
                </div>

                <hr className="border-slate-200 dark:border-slate-700" />

                <div className="flex justify-between text-base">
                  <span className="font-semibold text-slate-900 dark:text-white">
                    Estimated Total
                  </span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {selectedTutor
                      ? formatCurrency(estimatedPrice, selectedTutor.currency)
                      : '-'}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-200 dark:border-slate-700">
              <Button
                variant="ghost"
                onClick={() => setShowConfirmDialog(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirmBooking}
                loading={createBooking.isPending}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Confirm Booking
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
