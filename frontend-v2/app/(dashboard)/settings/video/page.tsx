'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Video,
  Check,
  AlertCircle,
  ExternalLink,
  CheckCircle2,
  XCircle,
  Loader2,
} from 'lucide-react';
import { useAuth } from '@/lib/hooks';
import { useVideoSettings, useUpdateVideoSettings, useVideoProviders } from '@/lib/hooks/use-video-settings';
import type { VideoProvider } from '@/lib/api/video-settings';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Button,
  Input,
  Skeleton,
} from '@/components/ui';

const videoSettingsSchema = z.object({
  preferred_video_provider: z.enum(['zoom', 'google_meet', 'teams', 'custom', 'manual']),
  custom_meeting_url_template: z.string().optional().nullable(),
}).refine(
  (data) => {
    // Custom and Teams require a URL
    if (data.preferred_video_provider === 'custom' || data.preferred_video_provider === 'teams') {
      return data.custom_meeting_url_template && data.custom_meeting_url_template.trim() !== '';
    }
    return true;
  },
  {
    message: 'Meeting URL is required for this provider',
    path: ['custom_meeting_url_template'],
  }
).refine(
  (data) => {
    // Validate URL format if provided
    if (data.custom_meeting_url_template && data.custom_meeting_url_template.trim() !== '') {
      try {
        const url = new URL(data.custom_meeting_url_template);
        return url.protocol === 'http:' || url.protocol === 'https:';
      } catch {
        return false;
      }
    }
    return true;
  },
  {
    message: 'Please enter a valid URL (starting with http:// or https://)',
    path: ['custom_meeting_url_template'],
  }
);

type VideoSettingsFormData = z.infer<typeof videoSettingsSchema>;

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-80 mt-2" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-start gap-4 p-4 rounded-xl border border-slate-200 dark:border-slate-700">
              <Skeleton className="h-5 w-5 rounded-full mt-0.5" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-64" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function ProviderStatusBadge({ isAvailable, isConnected }: { isAvailable: boolean; isConnected?: boolean }) {
  if (isConnected) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
        <CheckCircle2 className="h-3 w-3" />
        Connected
      </span>
    );
  }
  if (!isAvailable) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
        <XCircle className="h-3 w-3" />
        Setup Required
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
      <CheckCircle2 className="h-3 w-3" />
      Available
    </span>
  );
}

export default function VideoSettingsPage() {
  const router = useRouter();
  const { user, isLoading: isLoadingUser } = useAuth();
  const { data: settings, isLoading: isLoadingSettings, error: settingsError } = useVideoSettings();
  const { data: providersData, isLoading: isLoadingProviders } = useVideoProviders();
  const updateSettings = useUpdateVideoSettings();

  const [saveSuccess, setSaveSuccess] = useState(false);

  const form = useForm<VideoSettingsFormData>({
    resolver: zodResolver(videoSettingsSchema),
    defaultValues: {
      preferred_video_provider: 'zoom',
      custom_meeting_url_template: null,
    },
  });

  const selectedProvider = form.watch('preferred_video_provider');

  // Redirect non-tutors
  useEffect(() => {
    if (!isLoadingUser && user && user.role !== 'tutor') {
      router.push('/settings');
    }
  }, [user, isLoadingUser, router]);

  // Reset form when settings load
  useEffect(() => {
    if (settings) {
      form.reset({
        preferred_video_provider: settings.preferred_video_provider,
        custom_meeting_url_template: settings.custom_meeting_url_template,
      });
    }
  }, [settings, form]);

  const onSubmit = async (data: VideoSettingsFormData) => {
    setSaveSuccess(false);
    try {
      await updateSettings.mutateAsync({
        preferred_video_provider: data.preferred_video_provider,
        custom_meeting_url_template: data.custom_meeting_url_template || null,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch {
      // Error handled by mutation
    }
  };

  // Show loading while checking user role
  if (isLoadingUser) {
    return <LoadingSkeleton />;
  }

  // Show nothing if user is not a tutor (will redirect)
  if (!user || user.role !== 'tutor') {
    return null;
  }

  if (isLoadingSettings || isLoadingProviders) {
    return <LoadingSkeleton />;
  }

  if (settingsError) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <AlertCircle className="h-10 w-10 text-red-500" />
            <div>
              <p className="font-medium text-slate-900 dark:text-white">
                Failed to load video settings
              </p>
              <p className="text-sm text-slate-500">
                {settingsError instanceof Error ? settingsError.message : 'Please try again later'}
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const providers = providersData?.providers || [];

  const getProviderDetails = (value: VideoProvider) => {
    const provider = providers.find((p) => p.value === value);
    if (provider) return provider;

    // Fallback if providers haven't loaded
    const fallbacks: Record<VideoProvider, { label: string; description: string; requires_setup: boolean; is_available: boolean }> = {
      zoom: { label: 'Zoom', description: 'Automatic Zoom meeting links', requires_setup: false, is_available: settings?.zoom_available ?? false },
      google_meet: { label: 'Google Meet', description: 'Google Meet via connected calendar', requires_setup: true, is_available: settings?.google_calendar_connected ?? false },
      teams: { label: 'Microsoft Teams', description: 'Use your Teams meeting room link', requires_setup: true, is_available: true },
      custom: { label: 'Custom URL', description: 'Use any video platform', requires_setup: true, is_available: true },
      manual: { label: 'Manual', description: 'Provide link for each booking', requires_setup: false, is_available: true },
    };
    return { value, ...fallbacks[value] };
  };

  const showUrlInput = selectedProvider === 'custom' || selectedProvider === 'teams';
  const selectedProviderDetails = getProviderDetails(selectedProvider);

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      {saveSuccess && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400">
          <Check className="h-4 w-4" />
          <span className="text-sm">Video settings saved successfully!</span>
        </div>
      )}

      {updateSettings.isError && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">
            {updateSettings.error instanceof Error
              ? updateSettings.error.message
              : 'Failed to save video settings'}
          </span>
        </div>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
              <Video className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <CardTitle>Video Meeting Provider</CardTitle>
              <CardDescription>
                Choose how you want to conduct video sessions with your students
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Provider Status Overview */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 space-y-2">
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Integration Status
            </p>
            <div className="flex flex-wrap gap-3">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-slate-500">Zoom:</span>
                <ProviderStatusBadge isAvailable={settings?.zoom_available ?? false} />
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-slate-500">Google Calendar:</span>
                <ProviderStatusBadge
                  isAvailable={true}
                  isConnected={settings?.google_calendar_connected}
                />
              </div>
            </div>
            {!settings?.google_calendar_connected && (
              <p className="text-xs text-slate-500 mt-2">
                To use Google Meet, connect your Google Calendar in{' '}
                <a href="/settings/integrations" className="text-primary-600 hover:underline inline-flex items-center gap-1">
                  Integrations <ExternalLink className="h-3 w-3" />
                </a>
              </p>
            )}
          </div>

          {/* Provider Selection */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Select Provider
            </label>
            {(['zoom', 'google_meet', 'teams', 'custom', 'manual'] as VideoProvider[]).map((providerValue) => {
              const provider = getProviderDetails(providerValue);
              const isSelected = selectedProvider === providerValue;
              const isDisabled = !provider.is_available && provider.requires_setup;

              return (
                <label
                  key={providerValue}
                  className={`flex items-start gap-4 p-4 rounded-xl border-2 cursor-pointer transition-all ${
                    isSelected
                      ? 'border-primary-500 bg-primary-50/50 dark:bg-primary-900/10'
                      : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                  } ${isDisabled ? 'opacity-60 cursor-not-allowed' : ''}`}
                >
                  <input
                    type="radio"
                    value={providerValue}
                    disabled={isDisabled}
                    checked={isSelected}
                    onChange={() => {
                      if (!isDisabled) {
                        form.setValue('preferred_video_provider', providerValue);
                        // Clear custom URL when switching away from custom/teams
                        if (providerValue !== 'custom' && providerValue !== 'teams') {
                          form.setValue('custom_meeting_url_template', null);
                        }
                      }
                    }}
                    className="mt-1 h-4 w-4 text-primary-600 border-slate-300 focus:ring-primary-500"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-slate-900 dark:text-white">
                        {provider.label}
                      </span>
                      <ProviderStatusBadge
                        isAvailable={provider.is_available}
                        isConnected={
                          providerValue === 'google_meet' && settings?.google_calendar_connected
                            ? true
                            : undefined
                        }
                      />
                    </div>
                    <p className="text-sm text-slate-500 mt-0.5">
                      {provider.description}
                    </p>
                    {isDisabled && providerValue === 'google_meet' && (
                      <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                        Connect your Google Calendar to use this provider
                      </p>
                    )}
                  </div>
                </label>
              );
            })}
          </div>

          {/* Custom URL Input */}
          {showUrlInput && (
            <div className="space-y-2 pt-2">
              <label
                htmlFor="custom_meeting_url_template"
                className="text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                {selectedProvider === 'teams' ? 'Teams Meeting URL' : 'Custom Meeting URL'}
                <span className="text-red-500 ml-1">*</span>
              </label>
              <Input
                id="custom_meeting_url_template"
                type="url"
                placeholder={
                  selectedProvider === 'teams'
                    ? 'https://teams.microsoft.com/l/meetup-join/...'
                    : 'https://meet.jit.si/your-room or your preferred platform'
                }
                {...form.register('custom_meeting_url_template')}
              />
              {form.formState.errors.custom_meeting_url_template && (
                <p className="text-sm text-red-500">
                  {form.formState.errors.custom_meeting_url_template.message}
                </p>
              )}
              <p className="text-xs text-slate-500">
                {selectedProvider === 'teams'
                  ? 'Enter your personal Teams meeting room link. Students will use this link to join sessions.'
                  : 'Enter your meeting URL. Students will use this link to join all your sessions.'}
              </p>
            </div>
          )}

          {/* Provider-specific info */}
          {selectedProvider === 'manual' && (
            <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
              <p className="text-sm text-amber-800 dark:text-amber-200">
                <strong>Note:</strong> With manual mode, you&apos;ll need to provide a meeting link for each booking.
                Make sure to add the meeting link before the session starts.
              </p>
            </div>
          )}

          {selectedProvider === 'zoom' && settings?.zoom_available && (
            <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                <strong>Zoom:</strong> Meeting links will be automatically generated for each booking.
                No additional setup required.
              </p>
            </div>
          )}

          {selectedProvider === 'google_meet' && settings?.google_calendar_connected && (
            <div className="p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
              <p className="text-sm text-green-800 dark:text-green-200">
                <strong>Google Meet:</strong> Meeting links will be created via your connected Google Calendar.
                Events will automatically include a Meet link.
              </p>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-t border-slate-100 dark:border-slate-800 pt-6">
          <div className="text-sm text-slate-500">
            {settings?.video_provider_configured ? (
              <span className="flex items-center gap-1.5 text-green-600 dark:text-green-400">
                <CheckCircle2 className="h-4 w-4" />
                Video provider configured
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
                <AlertCircle className="h-4 w-4" />
                Setup required
              </span>
            )}
          </div>
          <Button
            type="submit"
            className="w-full sm:w-auto"
            disabled={updateSettings.isPending || (
              !selectedProviderDetails.is_available && selectedProviderDetails.requires_setup
            )}
          >
            {updateSettings.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Settings'
            )}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
