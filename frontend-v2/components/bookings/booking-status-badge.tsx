'use client';

import { Badge } from '@/components/ui';
import type { SessionState } from '@/types';

interface BookingStatusBadgeProps {
  status: SessionState;
}

const statusConfig: Record<
  SessionState,
  { label: string; variant: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info' }
> = {
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
