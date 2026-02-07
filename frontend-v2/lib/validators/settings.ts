import { z } from 'zod';
import { passwordSchema } from './auth';

export const profileSchema = z.object({
  first_name: z
    .string()
    .min(1, 'First name is required')
    .max(50, 'First name must be less than 50 characters'),
  last_name: z
    .string()
    .min(1, 'Last name is required')
    .max(50, 'Last name must be less than 50 characters'),
  bio: z
    .string()
    .max(500, 'Bio must be less than 500 characters')
    .optional()
    .nullable(),
});

export type ProfileFormData = z.infer<typeof profileSchema>;

export const passwordChangeSchema = z
  .object({
    current_password: z.string().min(1, 'Current password is required'),
    new_password: passwordSchema,
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  })
  .refine((data) => data.current_password !== data.new_password, {
    message: 'New password must be different from current password',
    path: ['new_password'],
  });

export type PasswordChangeFormData = z.infer<typeof passwordChangeSchema>;

export const notificationPreferencesSchema = z.object({
  email_enabled: z.boolean(),
  push_enabled: z.boolean(),
  session_reminders_enabled: z.boolean(),
  booking_requests_enabled: z.boolean(),
  review_prompts_enabled: z.boolean(),
  marketing_enabled: z.boolean(),
});

export type NotificationPreferencesFormData = z.infer<typeof notificationPreferencesSchema>;

export const accountSettingsSchema = z.object({
  timezone: z.string().min(1, 'Timezone is required'),
});

export type AccountSettingsFormData = z.infer<typeof accountSettingsSchema>;
