'use client';

import { useEffect, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Camera, Trash2, Check, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth, useUploadAvatar, useDeleteAvatar, useUpdateProfile } from '@/lib/hooks';
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
  Skeleton,
} from '@/components/ui';

export default function ProfileSettingsPage() {
  const { user, isLoading: isLoadingUser } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const uploadAvatar = useUploadAvatar();
  const deleteAvatar = useDeleteAvatar();
  const updateProfile = useUpdateProfile();

  const form = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      bio: '',
    },
  });

  // Reset form when user data loads
  useEffect(() => {
    if (user) {
      form.reset({
        first_name: user.first_name ?? '',
        last_name: user.last_name ?? '',
        bio: '', // Bio is not in the User type currently
      });
    }
  }, [user, form]);

  const onSubmit = async (data: ProfileFormData) => {
    setSaveSuccess(false);
    try {
      await updateProfile.mutateAsync({
        first_name: data.first_name,
        last_name: data.last_name,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch {
      // Error handled by mutation
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
    if (!validTypes.includes(file.type)) {
      setUploadError('Please select a JPG, PNG, or GIF image');
      return;
    }

    // Validate file size (2MB max)
    if (file.size > 2 * 1024 * 1024) {
      setUploadError('Image must be less than 2MB');
      return;
    }

    setUploadError(null);
    try {
      await uploadAvatar.mutateAsync(file);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Upload failed');
    }

    // Clear the input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDeleteAvatar = async () => {
    setUploadError(null);
    try {
      await deleteAvatar.mutateAsync();
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Delete failed');
    }
  };

  if (isLoadingUser) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-64 mt-2" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-6">
              <Skeleton className="h-20 w-20 rounded-full" />
              <Skeleton className="h-9 w-32" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-40" />
            <Skeleton className="h-4 w-48 mt-2" />
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid sm:grid-cols-2 gap-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-24 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

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
          <div className="flex flex-col sm:flex-row items-center sm:items-center gap-4 sm:gap-6">
            <div className="relative flex-shrink-0">
              <Avatar
                src={user?.avatar_url}
                name={`${user?.first_name} ${user?.last_name}`}
                size="xl"
              />
              {uploadAvatar.isPending && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full">
                  <Loader2 className="h-6 w-6 text-white animate-spin" />
                </div>
              )}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadAvatar.isPending}
                className="absolute -bottom-1 -right-1 p-2 rounded-full bg-primary-500 text-white hover:bg-primary-600 transition-colors shadow-md disabled:opacity-50"
              >
                <Camera className="h-4 w-4" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/gif"
                className="hidden"
                onChange={handleFileSelect}
              />
            </div>
            <div className="space-y-2 text-center sm:text-left">
              <div className="flex gap-2 justify-center sm:justify-start">
                <Button
                  variant="outline"
                  size="sm"
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadAvatar.isPending}
                >
                  {uploadAvatar.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    'Upload new picture'
                  )}
                </Button>
                {user?.avatar_url && !user.avatar_url.includes('default') && (
                  <Button
                    variant="ghost"
                    size="sm"
                    type="button"
                    onClick={handleDeleteAvatar}
                    disabled={deleteAvatar.isPending}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    {deleteAvatar.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </Button>
                )}
              </div>
              <p className="text-xs text-slate-500">
                JPG, PNG or GIF. Max size 2MB.
              </p>
              {uploadError && (
                <p className="text-xs text-red-500 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {uploadError}
                </p>
              )}
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
            {saveSuccess && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400">
                <Check className="h-4 w-4" />
                <span className="text-sm">Profile updated successfully!</span>
              </div>
            )}

            {updateProfile.isError && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm">
                  {updateProfile.error instanceof Error
                    ? updateProfile.error.message
                    : 'Failed to update profile'}
                </span>
              </div>
            )}

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
            <Button type="submit" loading={updateProfile.isPending}>
              Save Changes
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
