'use client';

import { use, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Clock,
  Calendar,
  MessageSquare,
  Heart,
  Share2,
  CheckCircle,
} from 'lucide-react';
import { useTutor, useTutorAvailability, useTutorReviews } from '@/lib/hooks';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Avatar,
  Badge,
  Skeleton,
} from '@/components/ui';
import { StarRating } from '@/components/reviews';
import { formatCurrency, formatRelativeTime } from '@/lib/utils';

interface TutorProfilePageProps {
  params: Promise<{ id: string }>;
}

const DAYS_OF_WEEK = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
];

const REVIEWS_PAGE_SIZE = 5;

export default function TutorProfilePage({ params }: TutorProfilePageProps) {
  const { id } = use(params);
  const router = useRouter();
  const tutorId = parseInt(id, 10);
  const [reviewsPage, setReviewsPage] = useState(1);

  const { data: tutor, isLoading: tutorLoading } = useTutor(tutorId);
  const { data: availability, isLoading: availabilityLoading } =
    useTutorAvailability(tutorId);
  const { data: reviews, isLoading: reviewsLoading } = useTutorReviews(
    tutorId,
    reviewsPage,
    REVIEWS_PAGE_SIZE
  );

  const groupedAvailability = availability?.reduce(
    (acc, slot) => {
      const day = DAYS_OF_WEEK[slot.day_of_week];
      if (!acc[day]) {
        acc[day] = [];
      }
      acc[day].push(slot);
      return acc;
    },
    {} as Record<string, typeof availability>
  );

  if (tutorLoading) {
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
                <div className="flex items-start gap-6">
                  <Skeleton className="h-24 w-24 rounded-full" />
                  <div className="flex-1 space-y-3">
                    <Skeleton className="h-8 w-48" />
                    <Skeleton className="h-4 w-64" />
                    <Skeleton className="h-4 w-32" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6 space-y-4">
                <Skeleton className="h-6 w-24" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </CardContent>
            </Card>
          </div>
          <div className="space-y-4">
            <Skeleton className="h-48 rounded-2xl" />
          </div>
        </div>
      </div>
    );
  }

  if (!tutor) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Card>
          <CardContent className="py-12 text-center">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              Tutor not found
            </h3>
            <p className="text-slate-500 mb-4">
              The tutor you are looking for does not exist or has been removed.
            </p>
            <Button asChild>
              <Link href="/tutors">Browse Tutors</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Tutor Profile
        </h1>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex flex-col sm:flex-row items-start gap-6">
                <Avatar
                  src={tutor.avatar_url}
                  name={tutor.display_name}
                  size="xl"
                  className="h-24 w-24"
                />
                <div className="flex-1">
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div>
                      <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                        {tutor.display_name}
                      </h2>
                      {tutor.headline && (
                        <p className="text-slate-600 dark:text-slate-400 mt-1">
                          {tutor.headline}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="icon">
                        <Heart className="h-5 w-5" />
                      </Button>
                      <Button variant="ghost" size="icon">
                        <Share2 className="h-5 w-5" />
                      </Button>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center gap-4 flex-wrap">
                    <div className="flex items-center gap-2">
                      <StarRating value={Math.round(Number(tutor.average_rating || 0))} readonly size="sm" />
                      <span className="text-sm font-medium text-slate-900 dark:text-white">
                        {Number(tutor.average_rating || 0).toFixed(1)}
                      </span>
                      <span className="text-sm text-slate-500">
                        ({tutor.total_reviews ?? 0} reviews)
                      </span>
                    </div>
                    {tutor.is_approved && (
                      <div className="flex items-center gap-1 text-green-600">
                        <CheckCircle className="h-4 w-4" />
                        <span className="text-sm font-medium">Verified</span>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {tutor.subjects.map((subject) => (
                      <Badge key={subject.id} variant="primary">
                        {subject.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>About</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600 dark:text-slate-400 whitespace-pre-line">
                {tutor.bio ||
                  'This tutor has not added a bio yet. Contact them to learn more about their teaching style and experience.'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Availability</CardTitle>
            </CardHeader>
            <CardContent>
              {availabilityLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-10 w-full" />
                  ))}
                </div>
              ) : !groupedAvailability ||
                Object.keys(groupedAvailability).length === 0 ? (
                <div className="py-8 text-center">
                  <Calendar className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">
                    No availability set. Contact the tutor to schedule a session.
                  </p>
                </div>
              ) : (
                <div className="grid sm:grid-cols-2 gap-4">
                  {DAYS_OF_WEEK.map((day) => {
                    const slots = groupedAvailability[day];
                    if (!slots || slots.length === 0) return null;

                    return (
                      <div
                        key={day}
                        className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800"
                      >
                        <h4 className="font-medium text-slate-900 dark:text-white mb-2">
                          {day}
                        </h4>
                        <div className="space-y-1">
                          {slots.map((slot) => (
                            <div
                              key={slot.id}
                              className="text-sm text-slate-600 dark:text-slate-400 flex items-center gap-2"
                            >
                              <Clock className="h-3 w-3" />
                              {slot.start_time} - {slot.end_time}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Reviews</CardTitle>
                <Badge variant="default">
                  {tutor.total_reviews ?? 0} reviews
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {reviewsLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div
                      key={i}
                      className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <Skeleton className="h-8 w-8 rounded-full" />
                          <div className="space-y-1">
                            <Skeleton className="h-4 w-24" />
                            <Skeleton className="h-3 w-16" />
                          </div>
                        </div>
                        <Skeleton className="h-4 w-20" />
                      </div>
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-3/4 mt-1" />
                    </div>
                  ))}
                </div>
              ) : !reviews || reviews.length === 0 ? (
                <div className="py-8 text-center">
                  <MessageSquare className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">
                    No reviews yet. Be the first to leave a review!
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {reviews.map((review) => (
                    <div
                      key={review.id}
                      className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <Avatar name="Student" size="sm" />
                          <div>
                            <p className="font-medium text-slate-900 dark:text-white">
                              Student
                            </p>
                            <p className="text-xs text-slate-500">
                              {formatRelativeTime(review.created_at)}
                            </p>
                          </div>
                        </div>
                        <StarRating value={review.rating} readonly size="sm" />
                      </div>
                      {review.comment && (
                        <p className="text-slate-600 dark:text-slate-400">
                          {review.comment}
                        </p>
                      )}
                    </div>
                  ))}
                  {reviews.length >= REVIEWS_PAGE_SIZE && (
                    <div className="text-center pt-2">
                      <Button
                        variant="ghost"
                        onClick={() => setReviewsPage((prev) => prev + 1)}
                      >
                        Load more reviews
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="sticky top-4">
            <CardContent className="p-6">
              <div className="text-center mb-6">
                <div className="text-3xl font-bold text-slate-900 dark:text-white">
                  {formatCurrency(tutor.hourly_rate, tutor.currency)}
                </div>
                <p className="text-slate-500">per hour</p>
              </div>

              <div className="space-y-3">
                <Button className="w-full" size="lg">
                  <Calendar className="h-5 w-5 mr-2" />
                  Book Session
                </Button>
                <Button variant="outline" className="w-full" size="lg">
                  <MessageSquare className="h-5 w-5 mr-2" />
                  Send Message
                </Button>
              </div>

              <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800">
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Response time</span>
                    <span className="font-medium text-slate-900 dark:text-white">
                      Within 24 hours
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Sessions completed</span>
                    <span className="font-medium text-slate-900 dark:text-white">
                      {(tutor.total_reviews || 0) * 3}+
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Member since</span>
                    <span className="font-medium text-slate-900 dark:text-white">
                      2024
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
