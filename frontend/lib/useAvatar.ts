"use client";

import { useCallback, useEffect, useState } from "react";
import { avatars } from "./api";

export interface AvatarUploadResult {
  avatarUrl: string | null;
  expiresAt?: string;
}

export interface AvatarController {
  avatarUrl: string | null;
  setAvatarUrl: (url: string | null) => void;
  uploadAvatar: (file: File) => Promise<AvatarUploadResult>;
  removeAvatar: () => Promise<void>;
  uploading: boolean;
  deleting: boolean;
}

interface UseAvatarOptions {
  initialUrl?: string | null;
  adminUserId?: number;
  onChange?: (url: string | null) => void;
}

export function useAvatar(options: UseAvatarOptions = {}): AvatarController {
  const { initialUrl = null, adminUserId, onChange } = options;
  const [avatarUrl, setAvatarUrl] = useState<string | null>(initialUrl);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    setAvatarUrl(initialUrl ?? null);
  }, [initialUrl]);

  const uploadAvatar = useCallback(
    async (file: File): Promise<AvatarUploadResult> => {
      setUploading(true);
      try {
        const response = adminUserId
          ? await avatars.uploadForUser(adminUserId, file)
          : await avatars.upload(file);
        setAvatarUrl(response.avatarUrl);
        onChange?.(response.avatarUrl);
        return {
          avatarUrl: response.avatarUrl,
          expiresAt: response.expiresAt,
        };
      } finally {
        setUploading(false);
      }
    },
    [adminUserId, onChange],
  );

  const removeAvatar = useCallback(async () => {
    if (adminUserId) {
      // Admin removal handled through overrides only
      onChange?.(null);
      return;
    }

    setDeleting(true);
    try {
      await avatars.remove();
      setAvatarUrl(null);
      onChange?.(null);
    } finally {
      setDeleting(false);
    }
  }, [adminUserId, onChange]);

  return {
    avatarUrl,
    setAvatarUrl,
    uploadAvatar,
    removeAvatar,
    uploading,
    deleting,
  };
}
