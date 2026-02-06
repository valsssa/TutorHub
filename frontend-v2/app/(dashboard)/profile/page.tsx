'use client';

import Link from 'next/link';
import {
  Edit,
  Star,
  Calendar,
  BookOpen,
  Clock,
  MessageSquare,
  Settings,
  DollarSign,
} from 'lucide-react';
import { useAuth, useMyTutorProfile } from '@/lib/hooks';
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
import { formatCurrency } from '@/lib/utils';

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={`h-4 w-4 ${
            i < rating
              ? 'fill-amber-400 text-amber-400'
              : 'fill-slate-200 text-slate-200 dark:fill-slate-700 dark:text-slate-700'
          }`}
        />
      ))}
    </div>
  );
}

function ProfileSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-10 w-32" />
      </div>
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
      <div className="grid md:grid-cols-2 gap-6">
        <Skeleton className="h-48 rounded-2xl" />
        <Skeleton className="h-48 rounded-2xl" />
      </div>
    </div>
  );
}

function TutorProfile() {
  const { user } = useAuth();
  const { data: tutorProfile, isLoading: profileLoading } = useMyTutorProfile();

  if (profileLoading) {
    return <ProfileSkeleton />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          My Profile
        </h1>
        <div className="flex gap-2">
          <Link href="/profile/availability">
            <Button variant="outline">
              <Clock className="h-4 w-4 mr-2" />
              Manage Availability
            </Button>
          </Link>
          <Link href="/profile/edit">
            <Button>
              <Edit className="h-4 w-4 mr-2" />
              Edit Profile
            </Button>
          </Link>
        </div>
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row items-start gap-6">
            <Avatar
              src={tutorProfile?.avatar_url || user?.avatar_url}
              name={tutorProfile?.display_name || `${user?.first_name} ${user?.last_name}`}
              size="xl"
              className="h-24 w-24"
            />
            <div className="flex-1">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                    {tutorProfile?.display_name || `${user?.first_name} ${user?.last_name}`}
                  </h2>
                  {tutorProfile?.headline && (
                    <p className="text-slate-600 dark:text-slate-400 mt-1">
                      {tutorProfile.headline}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {tutorProfile?.is_approved ? (
                    <Badge variant="success">Verified</Badge>
                  ) : (
                    <Badge variant="warning">Pending Approval</Badge>
                  )}
                </div>
              </div>

              <div className="mt-4 flex items-center gap-4 flex-wrap">
                {tutorProfile && (
                  <>
                    <div className="flex items-center gap-2">
                      <StarRating rating={Math.round(Number(tutorProfile.average_rating || 0))} />
                      <span className="text-sm font-medium text-slate-900 dark:text-white">
                        {Number(tutorProfile.average_rating || 0).toFixed(1)}
                      </span>
                      <span className="text-sm text-slate-500">
                        ({tutorProfile.total_reviews ?? 0} reviews)
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-slate-500">
                      <DollarSign className="h-4 w-4" />
                      <span className="text-sm">
                        {formatCurrency(tutorProfile.hourly_rate, tutorProfile.currency)}/hr
                      </span>
                    </div>
                  </>
                )}
              </div>

              {tutorProfile?.subjects && tutorProfile.subjects.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {tutorProfile.subjects.map((subject) => (
                    <Badge key={subject.id} variant="primary">
                      {subject.name}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>About Me</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-600 dark:text-slate-400 whitespace-pre-line">
            {tutorProfile?.bio || 'No bio added yet. Add one to help students learn more about you!'}
          </p>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Quick Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="h-5 w-5 text-primary-500" />
                  <span className="text-sm text-slate-500">Total Sessions</span>
                </div>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {tutorProfile?.review_count ? tutorProfile.total_reviews ?? 0 * 3 : 0}
                </p>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800">
                <div className="flex items-center gap-2 mb-2">
                  <Star className="h-5 w-5 text-amber-500" />
                  <span className="text-sm text-slate-500">Average Rating</span>
                </div>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {Number(tutorProfile?.average_rating || 0).toFixed(1)}
                </p>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800">
                <div className="flex items-center gap-2 mb-2">
                  <MessageSquare className="h-5 w-5 text-green-500" />
                  <span className="text-sm text-slate-500">Reviews</span>
                </div>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {tutorProfile?.review_count || 0}
                </p>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800">
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen className="h-5 w-5 text-blue-500" />
                  <span className="text-sm text-slate-500">Subjects</span>
                </div>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {tutorProfile?.subjects?.length || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Link href="/profile/edit" className="block">
              <Button variant="ghost" className="w-full justify-start">
                <Edit className="h-4 w-4 mr-3" />
                Edit Profile
              </Button>
            </Link>
            <Link href="/profile/availability" className="block">
              <Button variant="ghost" className="w-full justify-start">
                <Clock className="h-4 w-4 mr-3" />
                Manage Availability
              </Button>
            </Link>
            <Link href="/bookings" className="block">
              <Button variant="ghost" className="w-full justify-start">
                <Calendar className="h-4 w-4 mr-3" />
                View Bookings
              </Button>
            </Link>
            <Link href="/messages" className="block">
              <Button variant="ghost" className="w-full justify-start">
                <MessageSquare className="h-4 w-4 mr-3" />
                Messages
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StudentProfile() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          My Profile
        </h1>
        <Link href="/profile/edit">
          <Button>
            <Edit className="h-4 w-4 mr-2" />
            Edit Profile
          </Button>
        </Link>
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row items-start gap-6">
            <Avatar
              src={user?.avatar_url}
              name={`${user?.first_name} ${user?.last_name}`}
              size="xl"
              className="h-24 w-24"
            />
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                {user?.first_name} {user?.last_name}
              </h2>
              <p className="text-slate-600 dark:text-slate-400 mt-1">
                {user?.email}
              </p>
              <Badge variant="primary" className="mt-2">
                Student
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Link href="/profile/edit" className="block">
              <Button variant="ghost" className="w-full justify-start">
                <Edit className="h-4 w-4 mr-3" />
                Edit Profile
              </Button>
            </Link>
            <Link href="/tutors" className="block">
              <Button variant="ghost" className="w-full justify-start">
                <BookOpen className="h-4 w-4 mr-3" />
                Find Tutors
              </Button>
            </Link>
            <Link href="/bookings" className="block">
              <Button variant="ghost" className="w-full justify-start">
                <Calendar className="h-4 w-4 mr-3" />
                My Bookings
              </Button>
            </Link>
            <Link href="/messages" className="block">
              <Button variant="ghost" className="w-full justify-start">
                <MessageSquare className="h-4 w-4 mr-3" />
                Messages
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Account Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Link href="/settings" className="block">
              <Button variant="ghost" className="w-full justify-start">
                <Settings className="h-4 w-4 mr-3" />
                Settings
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <ProfileSkeleton />;
  }

  if (user?.role === 'tutor') {
    return <TutorProfile />;
  }

  return <StudentProfile />;
}
