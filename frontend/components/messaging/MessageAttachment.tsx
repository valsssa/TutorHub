"use client";

import { useState, useCallback } from "react";
import { FiDownload, FiFile, FiImage, FiLoader, FiX, FiMaximize2 } from "react-icons/fi";
import type { MessageAttachment as MessageAttachmentType } from "@/types";
import { messages } from "@/lib/api";

interface MessageAttachmentProps {
  attachment: MessageAttachmentType;
  isFromUser: boolean;
}

/**
 * Format file size in human-readable format
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Get file icon based on mime type
 */
function getFileIcon(mimeType: string) {
  if (mimeType.startsWith("image/")) {
    return FiImage;
  }
  return FiFile;
}

export default function MessageAttachment({
  attachment,
  isFromUser,
}: MessageAttachmentProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isLightboxOpen, setIsLightboxOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isImage = attachment.file_category === "image";
  const FileIcon = getFileIcon(attachment.mime_type);

  /**
   * Fetch presigned URL and handle download/preview
   */
  const handleDownload = useCallback(async () => {
    if (isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await messages.getAttachmentDownloadUrl(attachment.id);

      if (isImage) {
        // For images, set URL for preview
        setImageUrl(response.download_url);
      } else {
        // For documents, trigger download
        const link = document.createElement("a");
        link.href = response.download_url;
        link.download = response.filename;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err) {
      console.error("Failed to get attachment URL:", err);
      setError("Failed to load attachment");
    } finally {
      setIsLoading(false);
    }
  }, [attachment.id, isImage, isLoading]);

  /**
   * Open lightbox for full-size image view
   */
  const openLightbox = useCallback(async () => {
    if (!imageUrl) {
      await handleDownload();
    }
    setIsLightboxOpen(true);
  }, [imageUrl, handleDownload]);

  // Render image attachment
  if (isImage) {
    return (
      <>
        <div className="mt-2 max-w-xs">
          {imageUrl ? (
            <div className="relative group cursor-pointer" onClick={openLightbox}>
              <img
                src={imageUrl}
                alt={attachment.original_filename}
                className="rounded-lg max-h-48 object-cover w-full"
                style={{
                  aspectRatio: attachment.width && attachment.height
                    ? `${attachment.width}/${attachment.height}`
                    : "auto",
                }}
              />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors rounded-lg flex items-center justify-center">
                <FiMaximize2 className="text-white opacity-0 group-hover:opacity-100 transition-opacity w-6 h-6" />
              </div>
            </div>
          ) : (
            <button
              onClick={handleDownload}
              disabled={isLoading}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                isFromUser
                  ? "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-100"
                  : "bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200"
              }`}
            >
              {isLoading ? (
                <FiLoader className="w-4 h-4 animate-spin" />
              ) : (
                <FiImage className="w-4 h-4" />
              )}
              <span className="truncate max-w-[150px]">{attachment.original_filename}</span>
              <span className="text-xs opacity-70">({formatFileSize(attachment.file_size)})</span>
            </button>
          )}
          {error && (
            <p className="text-xs text-red-400 mt-1">{error}</p>
          )}
        </div>

        {/* Lightbox for full-size image */}
        {isLightboxOpen && imageUrl && (
          <div
            className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
            onClick={() => setIsLightboxOpen(false)}
          >
            <button
              onClick={() => setIsLightboxOpen(false)}
              className="absolute top-4 right-4 text-white hover:text-gray-300 transition-colors"
            >
              <FiX className="w-8 h-8" />
            </button>
            <img
              src={imageUrl}
              alt={attachment.original_filename}
              className="max-w-full max-h-full object-contain"
              onClick={(e) => e.stopPropagation()}
            />
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white text-sm bg-black/50 px-3 py-1 rounded">
              {attachment.original_filename} ({formatFileSize(attachment.file_size)})
            </div>
          </div>
        )}
      </>
    );
  }

  // Render document attachment
  return (
    <div className="mt-2">
      <button
        onClick={handleDownload}
        disabled={isLoading}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
          isFromUser
            ? "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-100"
            : "bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200"
        }`}
      >
        {isLoading ? (
          <FiLoader className="w-4 h-4 animate-spin" />
        ) : (
          <FileIcon className="w-4 h-4 flex-shrink-0" />
        )}
        <span className="truncate max-w-[150px]">{attachment.original_filename}</span>
        <span className="text-xs opacity-70">({formatFileSize(attachment.file_size)})</span>
        <FiDownload className="w-4 h-4 flex-shrink-0" />
      </button>
      {error && (
        <p className="text-xs text-red-400 mt-1">{error}</p>
      )}
    </div>
  );
}
