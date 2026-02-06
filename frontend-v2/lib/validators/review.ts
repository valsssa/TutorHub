import { z } from 'zod';

export const createReviewSchema = z.object({
  rating: z
    .number()
    .min(1, 'Please select a rating')
    .max(5, 'Rating must be between 1 and 5'),
  comment: z
    .string()
    .max(1000, 'Comment must be less than 1000 characters')
    .optional(),
});

export type CreateReviewFormData = z.infer<typeof createReviewSchema>;
