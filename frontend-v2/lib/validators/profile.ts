import { z } from 'zod';

export const editProfileSchema = z.object({
  first_name: z
    .string()
    .min(1, 'First name is required')
    .max(50, 'First name must be 50 characters or less'),
  last_name: z
    .string()
    .min(1, 'Last name is required')
    .max(50, 'Last name must be 50 characters or less'),
  bio: z
    .string()
    .max(1000, 'Bio must be 1000 characters or less')
    .optional()
    .or(z.literal('')),
});

export type EditProfileFormData = z.infer<typeof editProfileSchema>;

export const tutorProfileSchema = z.object({
  first_name: z
    .string()
    .min(1, 'First name is required')
    .max(50, 'First name must be 50 characters or less'),
  last_name: z
    .string()
    .min(1, 'Last name is required')
    .max(50, 'Last name must be 50 characters or less'),
  bio: z
    .string()
    .max(1000, 'Bio must be 1000 characters or less')
    .optional()
    .or(z.literal('')),
  headline: z
    .string()
    .max(150, 'Headline must be 150 characters or less')
    .optional()
    .or(z.literal('')),
  hourly_rate: z
    .number()
    .min(1, 'Hourly rate must be at least $1')
    .max(500, 'Hourly rate cannot exceed $500'),
  subject_ids: z
    .array(z.number())
    .min(1, 'Select at least one subject'),
});

export type TutorProfileFormData = z.infer<typeof tutorProfileSchema>;

export const availabilitySlotSchema = z.object({
  day_of_week: z.number().min(0).max(6),
  start_time: z
    .string()
    .regex(/^([01]\d|2[0-3]):([0-5]\d)$/, 'Invalid time format (HH:MM)'),
  end_time: z
    .string()
    .regex(/^([01]\d|2[0-3]):([0-5]\d)$/, 'Invalid time format (HH:MM)'),
});

export type AvailabilitySlotFormData = z.infer<typeof availabilitySlotSchema>;

export const availabilityFormSchema = z.object({
  slots: z.array(availabilitySlotSchema),
  timezone: z.string().min(1, 'Timezone is required'),
});

export type AvailabilityFormData = z.infer<typeof availabilityFormSchema>;
