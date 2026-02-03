'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Camera } from 'lucide-react';
import { useAuth } from '@/lib/hooks';
import { profileSchema, type ProfileFormData } from '@/lib/validators/settings';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Button,
  Input,
  Avatar,
} from '@/components/ui';

export default function ProfileSettingsPage() {
  const { user, updateProfile, isUpdatingProfile } = useAuth();

  const form = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: user?.first_name ?? '',
      last_name: user?.last_name ?? '',
      bio: '',
    },
  });

  const onSubmit = async (data: ProfileFormData) => {
    try {
      await updateProfile({
        first_name: data.first_name,
        last_name: data.last_name,
      });
    } catch {
      // Error handled by mutation
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Profile Picture</CardTitle>
          <CardDescription>
            Upload a profile picture to personalize your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-6">
            <div className="relative">
              <Avatar
                src={user?.avatar_url}
                name={`${user?.first_name} ${user?.last_name}`}
                size="xl"
              />
              <button
                type="button"
                className="absolute -bottom-1 -right-1 p-2 rounded-full bg-primary-500 text-white hover:bg-primary-600 transition-colors shadow-md"
              >
                <Camera className="h-4 w-4" />
              </button>
            </div>
            <div className="space-y-2">
              <Button variant="outline" size="sm" type="button">
                Upload new picture
              </Button>
              <p className="text-xs text-slate-500">
                JPG, PNG or GIF. Max size 2MB.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>
              Update your personal details here
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid sm:grid-cols-2 gap-4">
              <Input
                label="First Name"
                placeholder="Enter your first name"
                error={form.formState.errors.first_name?.message}
                {...form.register('first_name')}
              />
              <Input
                label="Last Name"
                placeholder="Enter your last name"
                error={form.formState.errors.last_name?.message}
                {...form.register('last_name')}
              />
            </div>

            <Input
              label="Email"
              type="email"
              value={user?.email ?? ''}
              disabled
              hint="Email cannot be changed"
            />

            <div className="space-y-1.5">
              <label
                htmlFor="bio"
                className="text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                Bio
              </label>
              <textarea
                id="bio"
                rows={4}
                placeholder="Tell us about yourself..."
                className="flex w-full rounded-xl border bg-white px-3 py-2 text-sm border-slate-200 dark:border-slate-700 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-slate-400 dark:placeholder:text-slate-500 resize-none"
                {...form.register('bio')}
              />
              {form.formState.errors.bio && (
                <p className="text-sm text-red-500">
                  {form.formState.errors.bio.message}
                </p>
              )}
              <p className="text-xs text-slate-500">
                {form.watch('bio')?.length ?? 0}/500 characters
              </p>
            </div>
          </CardContent>
          <CardFooter className="justify-end">
            <Button type="submit" loading={isUpdatingProfile}>
              Save Changes
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
