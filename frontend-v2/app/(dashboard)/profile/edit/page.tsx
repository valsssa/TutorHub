'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowLeft, Save, Upload } from 'lucide-react';
import { useAuth, useMyTutorProfile, useUpdateTutorAbout, useSubjects } from '@/lib/hooks';
import {
  editProfileSchema,
  tutorProfileSchema,
  type EditProfileFormData,
  type TutorProfileFormData,
} from '@/lib/validators/profile';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Avatar,
  Skeleton,
} from '@/components/ui';
import { SubjectSelector } from '@/components/profile/subject-selector';

function EditProfileSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-10 rounded-xl" />
        <Skeleton className="h-8 w-48" />
      </div>
      <Card>
        <CardContent className="p-6 space-y-6">
          <div className="flex items-center gap-6">
            <Skeleton className="h-24 w-24 rounded-full" />
            <Skeleton className="h-10 w-32" />
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
          </div>
          <Skeleton className="h-32" />
        </CardContent>
      </Card>
    </div>
  );
}

function StudentEditForm() {
  const { user, updateProfile, isUpdatingProfile } = useAuth();
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
  } = useForm<EditProfileFormData>({
    resolver: zodResolver(editProfileSchema),
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      bio: '',
    },
  });

  useEffect(() => {
    if (user) {
      reset({
        first_name: user.first_name,
        last_name: user.last_name,
        bio: '',
      });
    }
  }, [user, reset]);

  const onSubmit = async (data: EditProfileFormData) => {
    try {
      await updateProfile(data);
      router.push('/profile');
    } catch (error) {
      console.error('Failed to update profile:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Profile Picture</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-6">
            <Avatar
              src={user?.avatar_url}
              name={`${user?.first_name} ${user?.last_name}`}
              size="xl"
              className="h-24 w-24"
            />
            <div>
              <Button type="button" variant="outline">
                <Upload className="h-4 w-4 mr-2" />
                Upload Photo
              </Button>
              <p className="text-xs text-slate-500 mt-2">
                JPG, PNG or GIF. Max size 2MB.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Personal Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <Input
              label="First Name"
              {...register('first_name')}
              error={errors.first_name?.message}
            />
            <Input
              label="Last Name"
              {...register('last_name')}
              error={errors.last_name?.message}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Bio
            </label>
            <textarea
              {...register('bio')}
              rows={4}
              placeholder="Tell us a bit about yourself..."
              className="flex w-full rounded-xl border bg-white px-3 py-2 text-sm border-slate-200 dark:border-slate-700 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-slate-400 dark:placeholder:text-slate-500 resize-none"
            />
            {errors.bio && (
              <p className="text-sm text-red-500">{errors.bio.message}</p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center justify-end gap-4">
        <Link href="/profile">
          <Button type="button" variant="outline">
            Cancel
          </Button>
        </Link>
        <Button type="submit" loading={isUpdatingProfile} disabled={!isDirty}>
          <Save className="h-4 w-4 mr-2" />
          Save Changes
        </Button>
      </div>
    </form>
  );
}

function TutorEditForm() {
  const { user, updateProfile, isUpdatingProfile } = useAuth();
  const { data: tutorProfile, isLoading: profileLoading } = useMyTutorProfile();
  const { data: subjects = [], isLoading: subjectsLoading } = useSubjects();
  const updateTutorProfile = useUpdateTutorAbout();
  const router = useRouter();

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isDirty },
    reset,
  } = useForm<TutorProfileFormData>({
    resolver: zodResolver(tutorProfileSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      bio: '',
      headline: '',
      hourly_rate: 25,
      subject_ids: [],
    },
  });

  useEffect(() => {
    if (user && tutorProfile) {
      reset({
        first_name: user.first_name,
        last_name: user.last_name,
        bio: tutorProfile.bio || '',
        headline: tutorProfile.headline || '',
        hourly_rate: tutorProfile.hourly_rate,
        subject_ids: tutorProfile.subjects.map((s) => s.id),
      });
    }
  }, [user, tutorProfile, reset]);

  const onSubmit = async (data: TutorProfileFormData) => {
    try {
      await Promise.all([
        updateProfile({
          first_name: data.first_name,
          last_name: data.last_name,
        }),
        updateTutorProfile.mutateAsync({
          bio: data.bio,
          headline: data.headline,
        }),
      ]);
      router.push('/profile');
    } catch (error) {
      console.error('Failed to update profile:', error);
    }
  };

  if (profileLoading || subjectsLoading) {
    return <EditProfileSkeleton />;
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Profile Picture</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-6">
            <Avatar
              src={tutorProfile?.avatar_url || user?.avatar_url}
              name={tutorProfile?.display_name || `${user?.first_name} ${user?.last_name}`}
              size="xl"
              className="h-24 w-24"
            />
            <div>
              <Button type="button" variant="outline">
                <Upload className="h-4 w-4 mr-2" />
                Upload Photo
              </Button>
              <p className="text-xs text-slate-500 mt-2">
                JPG, PNG or GIF. Max size 2MB.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Personal Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <Input
              label="First Name"
              {...register('first_name')}
              error={errors.first_name?.message}
            />
            <Input
              label="Last Name"
              {...register('last_name')}
              error={errors.last_name?.message}
            />
          </div>

          <Input
            label="Headline"
            {...register('headline')}
            error={errors.headline?.message}
            placeholder="e.g., Experienced Math Tutor | PhD in Mathematics"
            hint="A short professional tagline that appears on your profile"
          />

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Bio
            </label>
            <textarea
              {...register('bio')}
              rows={4}
              placeholder="Tell students about your background, teaching style, and what makes you a great tutor..."
              className="flex w-full rounded-xl border bg-white px-3 py-2 text-sm border-slate-200 dark:border-slate-700 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-slate-400 dark:placeholder:text-slate-500 resize-none"
            />
            {errors.bio && (
              <p className="text-sm text-red-500">{errors.bio.message}</p>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tutoring Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Controller
            name="hourly_rate"
            control={control}
            render={({ field }) => (
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Hourly Rate (USD)
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                    $
                  </span>
                  <input
                    type="number"
                    {...field}
                    onChange={(e) => field.onChange(Number(e.target.value))}
                    className="flex h-10 w-full rounded-xl border bg-white pl-8 pr-3 py-2 text-sm border-slate-200 dark:border-slate-700 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    min={1}
                    max={500}
                  />
                </div>
                {errors.hourly_rate && (
                  <p className="text-sm text-red-500">{errors.hourly_rate.message}</p>
                )}
              </div>
            )}
          />

          <Controller
            name="subject_ids"
            control={control}
            render={({ field }) => (
              <SubjectSelector
                label="Subjects You Teach"
                subjects={subjects}
                selectedIds={field.value}
                onChange={field.onChange}
                error={errors.subject_ids?.message}
                placeholder="Select the subjects you teach..."
              />
            )}
          />
        </CardContent>
      </Card>

      <div className="flex items-center justify-end gap-4">
        <Link href="/profile">
          <Button type="button" variant="outline">
            Cancel
          </Button>
        </Link>
        <Button
          type="submit"
          loading={isUpdatingProfile || updateTutorProfile.isPending}
          disabled={!isDirty}
        >
          <Save className="h-4 w-4 mr-2" />
          Save Changes
        </Button>
      </div>
    </form>
  );
}

export default function EditProfilePage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  if (isLoading) {
    return <EditProfileSkeleton />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Edit Profile
        </h1>
      </div>

      {user?.role === 'tutor' ? <TutorEditForm /> : <StudentEditForm />}
    </div>
  );
}
