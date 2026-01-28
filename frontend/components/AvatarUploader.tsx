"use client";

import { ChangeEvent, useMemo, useRef, useState } from "react";
import Image from "next/image";
import clsx from "clsx";
import Button from "@/components/Button";
import LoadingSpinner from "@/components/LoadingSpinner";
import { useToast } from "@/components/ToastContainer";
import { useAvatar, type AvatarController } from "@/lib/useAvatar";

const MAX_SIZE_BYTES = 2_000_000;
const MIN_DIMENSION = 150;
const MAX_DIMENSION = 2000;
const ACCEPTED_TYPES = ["image/jpeg", "image/png"];

interface AvatarUploaderProps {
  initialUrl?: string | null;
  adminUserId?: number;
  onAvatarChange?: (url: string | null) => void;
  className?: string;
  title?: string;
  description?: string;
  controller?: AvatarController;
  allowRemoval?: boolean;
}

export default function AvatarUploader({
  initialUrl = null,
  adminUserId,
  onAvatarChange,
  className,
  title = "Profile photo",
  description = "Upload a square JPG or PNG under 2MB. We’ll resize it automatically.",
  controller,
  allowRemoval,
}: AvatarUploaderProps) {
  const { showError, showSuccess } = useToast();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const defaultController = useAvatar({
    initialUrl,
    adminUserId,
    onChange: onAvatarChange,
  });
  const {
    avatarUrl,
    uploadAvatar,
    removeAvatar,
    uploading,
    deleting,
  } = controller ?? defaultController;

  const resolvedAvatarUrl = useMemo(
    () => {
      if (avatarUrl !== undefined && avatarUrl !== null) {
        return avatarUrl;
      }
      return initialUrl ?? null;
    },
    [avatarUrl, initialUrl],
  );

  const removalEnabled = allowRemoval ?? (adminUserId === undefined);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setValidationMessage(null);
    try {
      await validateFile(file);
      try {
        const response = await uploadAvatar(file);
        showSuccess("Avatar updated successfully");
      } finally {
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to upload avatar";
      setValidationMessage(message);
      showError(message);
    }
  };

  const handleRemove = async () => {
    if (!removalEnabled) {
      return;
    }
    try {
      await removeAvatar();
      showSuccess("Avatar removed");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to remove avatar";
      setValidationMessage(message);
      showError(message);
    }
  };

  return (
    <section
      className={clsx(
        "rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-6 shadow-sm transition-colors",
        className,
      )}
    >
      <div className="flex items-start gap-4">
        <div className="relative h-24 w-24 shrink-0 overflow-hidden rounded-full border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800">
          {resolvedAvatarUrl ? (
            <Image
              src={resolvedAvatarUrl}
              alt="Current avatar"
              width={96}
              height={96}
              className="h-full w-full object-cover"
              priority={false}
              loading="lazy"
              unoptimized
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-sm font-semibold text-slate-500 dark:text-slate-400">
              No photo
            </div>
          )}
          {(uploading || deleting) && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/70 dark:bg-slate-900/70">
              <LoadingSpinner size="sm" />
            </div>
          )}
        </div>

        <div className="flex-1">
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">{title}</h3>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{description}</p>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <label className="inline-flex">
              <input
                ref={fileInputRef}
                type="file"
                className="sr-only"
                accept={ACCEPTED_TYPES.join(",")}
                onChange={handleFileChange}
                data-testid="avatar-file-input"
              />
              <Button
                type="button"
                variant="secondary"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                aria-label="Upload new avatar"
              >
                Choose photo
              </Button>
            </label>

            {removalEnabled && (
              <Button
                type="button"
                variant="ghost"
                onClick={handleRemove}
                disabled={deleting || !resolvedAvatarUrl}
              >
                Remove
              </Button>
            )}
          </div>

          <p
            role="status"
            aria-live="polite"
            className={clsx(
              "mt-3 text-sm",
              validationMessage ? "text-red-600 dark:text-red-400" : "text-slate-500 dark:text-slate-400",
            )}
          >
            {validationMessage ||
              "Choose a square photo. We'll automatically resize it for you."}
          </p>
        </div>
      </div>
    </section>
  );
}

async function validateFile(file: File): Promise<void> {
  if (!ACCEPTED_TYPES.includes(file.type)) {
    throw new Error("Only JPEG and PNG images are supported");
  }
  if (file.size > MAX_SIZE_BYTES) {
    throw new Error("File size must be 2MB or less");
  }

  const dimensions = await readImageDimensions(file);
  if (
    dimensions.width < MIN_DIMENSION ||
    dimensions.height < MIN_DIMENSION
  ) {
    throw new Error("Image must be at least 150×150 pixels");
  }
  if (
    dimensions.width > MAX_DIMENSION ||
    dimensions.height > MAX_DIMENSION
  ) {
    throw new Error("Image cannot exceed 2000×2000 pixels");
  }
}

async function readImageDimensions(file: File): Promise<{
  width: number;
  height: number;
}> {
  return new Promise((resolve, reject) => {
    const image = typeof window !== 'undefined' ? document.createElement('img') : null;
    if (!image) {
      reject(new Error("Cannot create image element"));
      return;
    }
    
    const objectUrl = URL.createObjectURL(file);
    image.onload = () => {
      const { width, height } = image;
      URL.revokeObjectURL(objectUrl);
      resolve({ width, height });
    };
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Cannot read image dimensions"));
    };
    image.src = objectUrl;
  });
}
