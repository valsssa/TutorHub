"use client";

import { useCallback, useState } from "react";
import { tutors } from "./api";
import type { TutorProfile } from "@/types";
import type { AvatarController } from "./useAvatar";

interface UseTutorPhotoOptions {
  initialUrl?: string | null;
  onUploaded?: (profile: TutorProfile) => void;
}

export function useTutorPhoto(
  options: UseTutorPhotoOptions = {},
): AvatarController {
  const { initialUrl = null, onUploaded } = options;
  const [avatarUrl, setAvatarUrl] = useState<string | null>(initialUrl);
  const [uploading, setUploading] = useState(false);

  const uploadAvatar = useCallback(
    async (file: File) => {
      setUploading(true);
      try {
        const profile = await tutors.updateProfilePhoto(file);
        const newUrl = profile.profile_photo_url ?? null;
        setAvatarUrl(newUrl);
        onUploaded?.(profile);
        return {
          avatarUrl: newUrl,
          expiresAt: undefined,
        };
      } finally {
        setUploading(false);
      }
    },
    [onUploaded],
  );

  const removeAvatar = useCallback(async () => {
    // Tutor profile photos cannot be removed, only replaced
    throw new Error("Tutor profile photos cannot be removed");
  }, []);

  return {
    avatarUrl,
    setAvatarUrl,
    uploadAvatar,
    removeAvatar,
    uploading,
    deleting: false,
  };
}
