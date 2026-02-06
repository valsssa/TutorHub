'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Video,
  Calendar,
  CheckCircle2,
  XCircle,
  Loader2,
  ExternalLink,
  AlertCircle,
  Unplug,
} from 'lucide-react';
import { useAuth } from '@/lib/hooks';
import {
  useZoomStatus,
  useCalendarStatus,
  useConnectCalendar,
  useDisconnectCalendar,
} from '@/lib/hooks/use-integrations';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Button,
  Skeleton,
} from '@/components/ui';

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {[1, 2].map((i) => (
        <Card key={i}>
          <CardHeader>
            <div className="flex items-center gap-4">
              <Skeleton className="h-12 w-12 rounded-xl" />
              <div className="space-y-2">
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-4 w-64" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Skeleton className="h-20 w-full rounded-xl" />
          </CardContent>
          <CardFooter>
            <Skeleton className="h-10 w-32" />
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}

function StatusBadge({
  isConnected,
  isConfigured,
}: {
  isConnected: boolean;
  isConfigured?: boolean;
}) {
  if (isConnected) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
        <CheckCircle2 className="h-3.5 w-3.5" />
        Connected
      </span>
    );
  }
  if (isConfigured === false) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
        <XCircle className="h-3.5 w-3.5" />
        Not Configured
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
      <XCircle className="h-3.5 w-3.5" />
      Not Connected
    </span>
  );
}

function ZoomIntegrationCard() {
  const { data: status, isLoading, error } = useZoomStatus();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3 sm:gap-4">
            <Skeleton className="h-10 w-10 sm:h-12 sm:w-12 rounded-xl" />
            <div className="space-y-2 flex-1 min-w-0">
              <Skeleton className="h-5 w-32 sm:w-40" />
              <Skeleton className="h-4 w-48 sm:w-64" />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-20 w-full rounded-xl" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-blue-100 dark:bg-blue-900/30">
              <Video className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <CardTitle>Zoom</CardTitle>
              <CardDescription>Video conferencing for sessions</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span className="text-sm">Failed to load Zoom status</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="p-2 sm:p-3 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex-shrink-0">
              <Video className="h-5 w-5 sm:h-6 sm:w-6 text-blue-600" />
            </div>
            <div>
              <CardTitle>Zoom</CardTitle>
              <CardDescription>Video conferencing for sessions</CardDescription>
            </div>
          </div>
          <StatusBadge isConnected={status?.is_connected ?? false} isConfigured={status?.is_connected} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {status?.is_connected ? (
          <div className="p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  Zoom is configured
                </p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  Zoom meetings will be automatically created for your sessions.
                  When students book a session, a unique Zoom link will be generated.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  Zoom is not configured
                </p>
                <p className="text-sm text-amber-700 dark:text-amber-300">
                  Zoom integration is configured at the platform level.
                  Contact your administrator if you need Zoom meeting support.
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-2">
          <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
            How it works
          </h4>
          <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-2">
            <li className="flex items-start gap-2">
              <span className="text-primary-600 mt-0.5">1.</span>
              Zoom meetings are automatically created when bookings are confirmed
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-600 mt-0.5">2.</span>
              Unique meeting links are generated for each session
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-600 mt-0.5">3.</span>
              Both you and your student will receive the meeting link
            </li>
          </ul>
        </div>
      </CardContent>
      {status?.is_connected && (
        <CardFooter className="border-t border-slate-100 dark:border-slate-800 pt-4">
          <a
            href="https://zoom.us/meeting"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary-600 hover:text-primary-700 inline-flex items-center gap-1"
          >
            Manage Zoom meetings
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </CardFooter>
      )}
    </Card>
  );
}

function GoogleCalendarCard() {
  const { data: status, isLoading, error } = useCalendarStatus();
  const connectMutation = useConnectCalendar();
  const disconnectMutation = useDisconnectCalendar();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Skeleton className="h-12 w-12 rounded-xl" />
            <div className="space-y-2">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-64" />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-20 w-full rounded-xl" />
        </CardContent>
        <CardFooter>
          <Skeleton className="h-10 w-32" />
        </CardFooter>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-red-100 dark:bg-red-900/30">
              <Calendar className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <CardTitle>Google Calendar</CardTitle>
              <CardDescription>Sync sessions with your calendar</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span className="text-sm">Failed to load calendar status</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const handleConnect = () => {
    connectMutation.mutate();
  };

  const handleDisconnect = () => {
    if (window.confirm('Are you sure you want to disconnect Google Calendar? Your existing calendar events will not be affected.')) {
      disconnectMutation.mutate();
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="p-2 sm:p-3 rounded-xl bg-red-100 dark:bg-red-900/30 flex-shrink-0">
              <Calendar className="h-5 w-5 sm:h-6 sm:w-6 text-red-600" />
            </div>
            <div>
              <CardTitle>Google Calendar</CardTitle>
              <CardDescription>Sync sessions with your calendar</CardDescription>
            </div>
          </div>
          <StatusBadge isConnected={status?.is_connected ?? false} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {status?.is_connected ? (
          <>
            <div className="p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-green-800 dark:text-green-200">
                    Calendar connected
                  </p>
                  {status.calendar_email && (
                    <p className="text-sm text-green-700 dark:text-green-300">
                      Connected as <strong>{status.calendar_email}</strong>
                    </p>
                  )}
                  {status.connected_at && (
                    <p className="text-xs text-green-600 dark:text-green-400">
                      Connected on {new Date(status.connected_at).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
                Features enabled
              </h4>
              <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Session events added to your calendar
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Google Meet links for video sessions
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Calendar reminders for upcoming sessions
                </li>
              </ul>
            </div>
          </>
        ) : (
          <>
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Connect your Google Calendar to automatically sync your tutoring sessions.
                Events will be created in your calendar with all session details.
              </p>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
                Benefits of connecting
              </h4>
              <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-2">
                <li className="flex items-start gap-2">
                  <Calendar className="h-4 w-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Sessions automatically appear in your calendar
                </li>
                <li className="flex items-start gap-2">
                  <Video className="h-4 w-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Use Google Meet as your video provider
                </li>
                <li className="flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Never miss a session with calendar reminders
                </li>
              </ul>
            </div>
          </>
        )}
      </CardContent>
      <CardFooter className="border-t border-slate-100 dark:border-slate-800 pt-4">
        {status?.is_connected ? (
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 w-full">
            <a
              href="https://calendar.google.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary-600 hover:text-primary-700 inline-flex items-center gap-1"
            >
              Open Google Calendar
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDisconnect}
              disabled={disconnectMutation.isPending}
              className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              {disconnectMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Disconnecting...
                </>
              ) : (
                <>
                  <Unplug className="h-4 w-4 mr-2" />
                  Disconnect
                </>
              )}
            </Button>
          </div>
        ) : (
          <Button onClick={handleConnect} disabled={connectMutation.isPending}>
            {connectMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <Calendar className="h-4 w-4 mr-2" />
                Connect Google Calendar
              </>
            )}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}

export default function IntegrationsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoading: isLoadingUser } = useAuth();

  // Handle OAuth callback messages
  const calendarStatus = searchParams.get('calendar');
  const errorStatus = searchParams.get('error');

  // Redirect non-tutors
  useEffect(() => {
    if (!isLoadingUser && user && user.role !== 'tutor') {
      router.push('/settings');
    }
  }, [user, isLoadingUser, router]);

  // Show loading while checking user role
  if (isLoadingUser) {
    return <LoadingSkeleton />;
  }

  // Show nothing if user is not a tutor (will redirect)
  if (!user || user.role !== 'tutor') {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Success/Error messages from OAuth callback */}
      {calendarStatus === 'connected' && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800">
          <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
          <span>Google Calendar connected successfully!</span>
        </div>
      )}

      {errorStatus && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span>
            {errorStatus === 'invalid_state'
              ? 'Authorization expired. Please try connecting again.'
              : errorStatus === 'no_refresh_token'
                ? 'Could not get calendar permissions. Please try again and make sure to grant all requested permissions.'
                : errorStatus === 'oauth_error'
                  ? 'Failed to connect calendar. Please try again.'
                  : 'An error occurred. Please try again.'}
          </span>
        </div>
      )}

      <div className="grid gap-6">
        <ZoomIntegrationCard />
        <GoogleCalendarCard />
      </div>

      {/* Help section */}
      <Card>
        <CardContent className="py-4 sm:py-6">
          <div className="flex items-start gap-3 sm:gap-4">
            <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-slate-500" />
            </div>
            <div className="space-y-1">
              <h4 className="text-sm font-medium text-slate-900 dark:text-white">
                Need help with integrations?
              </h4>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                If you&apos;re having trouble connecting your accounts or have questions about
                how integrations work, please contact support or check our help documentation.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
