/**
 * Shared utility functions for API responses
 */
import type { User, AvatarApiResponse, AvatarSignedUrl } from "@/types";

/**
 * Normalize user object (handle avatar_url vs avatarUrl)
 */
export function normalizeUser(user: User): User {
  const avatarUrl = user.avatarUrl ?? user.avatar_url ?? null;
  return {
    ...user,
    avatarUrl,
  };
}

/**
 * Transform avatar API response to signed URL format
 */
export function transformAvatarResponse(data: AvatarApiResponse): AvatarSignedUrl {
  return {
    avatarUrl: data.avatar_url,
    expiresAt: data.expires_at,
  };
}
