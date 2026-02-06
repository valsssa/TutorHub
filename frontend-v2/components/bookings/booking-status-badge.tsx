'use client';

import { Badge } from '@/components/ui';
import type { SessionState } from '@/types';

interface BookingStatusBadgeProps {
  status: SessionState;
}

const statusConfig: Record<
  string,
  { label: string; variant: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info' }
> = {
  // Legacy lowercase states
  pending_tutor: { label: 'Awaiting Tutor', variant: 'warning' },
  pending_student: { label: 'Awaiting You', variant: 'info' },
  confirmed: { label: 'Confirmed', variant: 'success' },
  in_progress: { label: 'In Progress', variant: 'primary' },
  completed: { label: 'Completed', variant: 'success' },
  cancelled: { label: 'Cancelled', variant: 'danger' },
  expired: { label: 'Expired', variant: 'default' },
  no_show: { label: 'No Show', variant: 'danger' },
  // New uppercase states
  REQUESTED: { label: 'Requested', variant: 'warning' },
  SCHEDULED: { label: 'Scheduled', variant: 'info' },
  ACTIVE: { label: 'Active', variant: 'primary' },
  ENDED: { label: 'Ended', variant: 'success' },
  EXPIRED: { label: 'Expired', variant: 'default' },
  CANCELLED: { label: 'Cancelled', variant: 'danger' },
};

export function BookingStatusBadge({ status }: BookingStatusBadgeProps) {
  const config = statusConfig[status] ?? { label: status, variant: 'default' as const };

  return <Badge variant={config.variant}>{config.label}</Badge>;
}
