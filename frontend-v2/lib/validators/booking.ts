import { z } from 'zod';

export const createBookingSchema = z.object({
  tutor_id: z.number().positive('Please select a tutor'),
  subject_id: z.number().positive('Please select a subject'),
  start_time: z.string().min(1, 'Please select a date and time').refine(
    (val) => !isNaN(Date.parse(val)),
    'Invalid date/time'
  ).refine(
    (val) => new Date(val) > new Date(),
    'Session must be scheduled in the future'
  ),
  duration: z.enum(['30', '60', '90', '120'], {
    message: 'Please select a duration',
  }),
  message: z.string().max(500, 'Message must be less than 500 characters').optional(),
  package_id: z.number().positive().optional(),
});

export type CreateBookingFormData = z.infer<typeof createBookingSchema>;

export const cancelBookingSchema = z.object({
  reason: z.string().max(500).optional(),
});

export type CancelBookingFormData = z.infer<typeof cancelBookingSchema>;

export const declineBookingSchema = z.object({
  reason: z.string().min(1, 'Please provide a reason').max(500),
});

export type DeclineBookingFormData = z.infer<typeof declineBookingSchema>;
