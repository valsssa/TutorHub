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
  Play,
} from 'lucide-react';
import { useTutor, useTutorAvailability, useTutorReviews, useToggleFavorite } from '@/lib/hooks';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  buttonVariants,
  Avatar,
  Badge,
  Skeleton,
} from '@/components/ui';
import { StarRating } from '@/components/reviews';
import { cn, formatCurrency, formatRelativeTime } from '@/lib/utils';

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

function getYouTubeId(url: string): string | null {
  const match = url.match(
    /(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|shorts\/))([a-zA-Z0-9_-]{11})/
  );
  return match ? match[1] : null;
}

function getVimeoId(url: string): string | null {
  const match = url.match(/vimeo\.com\/(\d+)/);
  return match ? match[1] : null;
}

function VideoEmbed({ url }: { url: string }) {
  const youtubeId = getYouTubeId(url);
  if (youtubeId) {
    return (
      <div className="relative w-full aspect-video rounded-xl overflow-hidden">
        <iframe
          src={`https://www.youtube.com/embed/${youtubeId}`}
          title="Tutor intro video"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          className="absolute inset-0 w-full h-full"
        />
      </div>
    );
  }

  const vimeoId = getVimeoId(url);
  if (vimeoId) {
    return (
      <div className="relative w-full aspect-video rounded-xl overflow-hidden">
        <iframe
          src={`https://player.vimeo.com/video/${vimeoId}`}
          title="Tutor intro video"
          allow="autoplay; fullscreen; picture-in-picture"
          allowFullScreen
          className="absolute inset-0 w-full h-full"
        />
      </div>
    );
  }

  return (
    <video
      src={url}
      controls
      className="w-full aspect-video rounded-xl bg-black"
      preload="metadata"
    >
      Your browser does not support the video tag.
    </video>
  );
}

function FavoriteHeartButton({ tutorId }: { tutorId: number }) {
  const { isFavorite, isLoading, toggle } = useToggleFavorite(tutorId);

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={(e) => {
        e.preventDefault();
        toggle();
      }}
      disabled={isLoading}
      aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
    >
      <Heart
        className={cn(
          'h-5 w-5 transition-colors',
          isFavorite ? 'fill-red-500 text-red-500' : ''
        )}
      />
    </Button>
  );
}

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
            <Link href="/tutors" className={buttonVariants({ variant: 'primary', size: 'md' })}>
              Browse Tutors
            </Link>
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
                  className="h-24 w-24 shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div className="min-w-0">
                      <h2 className="text-2xl font-bold text-slate-900 dark:text-white truncate">
                        {tutor.display_name}
                      </h2>
                      {tutor.title && tutor.title !== tutor.display_name && (
                        <p className="text-sm font-medium text-primary-600 dark:text-primary-400 mt-0.5">
                          {tutor.title}
                        </p>
                      )}
                      {tutor.headline && (
                        <p className="text-slate-600 dark:text-slate-400 mt-1 line-clamp-2">
                          {tutor.headline}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <FavoriteHeartButton tutorId={tutorId} />
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

          {tutor.video_url && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Play className="h-5 w-5" />
                  Intro Video
                </CardTitle>
              </CardHeader>
              <CardContent>
                <VideoEmbed url={tutor.video_url} />
              </CardContent>
            </Card>
          )}

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
                      <div className="flex items-start justify-between gap-2 mb-2 flex-wrap">
                        <div className="flex items-center gap-3 min-w-0">
                          <Avatar name="Student" size="sm" className="shrink-0" />
                          <div className="min-w-0">
                            <p className="font-medium text-slate-900 dark:text-white truncate">
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
          <Card className="lg:sticky lg:top-4">
            <CardContent className="p-6">
              <div className="text-center mb-6">
                <div className="text-3xl font-bold text-slate-900 dark:text-white">
                  {formatCurrency(tutor.hourly_rate, tutor.currency)}
                </div>
                <p className="text-slate-500">per hour</p>
              </div>

              <div className="space-y-3">
                <Link
                  href={`/bookings/new?tutor=${tutorId}`}
                  className={cn(buttonVariants({ variant: 'primary', size: 'lg' }), 'w-full')}
                >
                  <Calendar className="h-5 w-5 mr-2" />
                  Book Session
                </Link>
                <Link
                  href={`/messages/${tutor.user_id}`}
                  className={cn(buttonVariants({ variant: 'outline', size: 'lg' }), 'w-full')}
                >
                  <MessageSquare className="h-5 w-5 mr-2" />
                  Send Message
                </Link>
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
                      {tutor.total_sessions ?? (tutor.total_reviews ?? 0)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Member since</span>
                    <span className="font-medium text-slate-900 dark:text-white">
                      {tutor.created_at ? new Date(tutor.created_at).getFullYear() : 'N/A'}
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
