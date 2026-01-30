"use client";

import { useState, useRef, useCallback } from "react";
import { FiSend, FiPaperclip, FiX, FiFile, FiImage, FiAlertCircle } from "react-icons/fi";
import Button from "@/components/Button";
import TextArea from "@/components/TextArea";

// Allowed file types matching backend configuration
const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"];
const ALLOWED_DOCUMENT_TYPES = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
];
const ALLOWED_MIME_TYPES = [...ALLOWED_IMAGE_TYPES, ...ALLOWED_DOCUMENT_TYPES];

const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5 MB
const MAX_DOCUMENT_SIZE = 10 * 1024 * 1024; // 10 MB

interface MessageInputProps {
  onSend: (message: string, file?: File) => void;
  onTyping?: () => void;
  disabled?: boolean;
  isLoading?: boolean;
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
 * Validate file type and size
 */
function validateFile(file: File): { valid: boolean; error?: string } {
  if (!ALLOWED_MIME_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: "File type not supported. Allowed: images (JPEG, PNG, GIF, WebP) and documents (PDF, DOC, TXT)",
    };
  }

  const isImage = ALLOWED_IMAGE_TYPES.includes(file.type);
  const maxSize = isImage ? MAX_IMAGE_SIZE : MAX_DOCUMENT_SIZE;
  const maxSizeLabel = isImage ? "5 MB" : "10 MB";

  if (file.size > maxSize) {
    return {
      valid: false,
      error: `File too large. Maximum size: ${maxSizeLabel}`,
    };
  }

  return { valid: true };
}

export default function MessageInput({
  onSend,
  onTyping,
  disabled = false,
  isLoading = false,
}: MessageInputProps) {
  const [message, setMessage] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreviewUrl, setFilePreviewUrl] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = useCallback((file: File) => {
    const validation = validateFile(file);
    if (!validation.valid) {
      setFileError(validation.error || "Invalid file");
      return;
    }

    setFileError(null);
    setSelectedFile(file);

    // Create preview for images
    if (ALLOWED_IMAGE_TYPES.includes(file.type)) {
      const url = URL.createObjectURL(file);
      setFilePreviewUrl(url);
    } else {
      setFilePreviewUrl(null);
    }
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFileSelect(file);
      }
      // Reset input so same file can be selected again
      e.target.value = "";
    },
    [handleFileSelect]
  );

  const clearFile = useCallback(() => {
    setSelectedFile(null);
    if (filePreviewUrl) {
      URL.revokeObjectURL(filePreviewUrl);
      setFilePreviewUrl(null);
    }
    setFileError(null);
  }, [filePreviewUrl]);

  const handleSend = useCallback(() => {
    if ((!message.trim() && !selectedFile) || disabled || isLoading) return;
    onSend(message, selectedFile || undefined);
    setMessage("");
    clearFile();
  }, [message, selectedFile, disabled, isLoading, onSend, clearFile]);

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);

      const file = e.dataTransfer.files?.[0];
      if (file) {
        handleFileSelect(file);
      }
    },
    [handleFileSelect]
  );

  const isImage = selectedFile && ALLOWED_IMAGE_TYPES.includes(selectedFile.type);

  return (
    <div
      className={`p-4 bg-gray-50 border-t border-gray-200 ${
        isDragOver ? "bg-emerald-50 border-emerald-300" : ""
      }`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {/* File preview */}
      {selectedFile && (
        <div className="mb-3 p-2 bg-white rounded-lg border border-gray-200 flex items-center gap-3">
          {isImage && filePreviewUrl ? (
            <img
              src={filePreviewUrl}
              alt="Preview"
              className="w-16 h-16 object-cover rounded"
            />
          ) : (
            <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
              <FiFile className="w-8 h-8 text-gray-400" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {selectedFile.name}
            </p>
            <p className="text-xs text-gray-500">
              {formatFileSize(selectedFile.size)}
            </p>
          </div>
          <button
            onClick={clearFile}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
            title="Remove file"
          >
            <FiX className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* File error */}
      {fileError && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-sm">
          <FiAlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{fileError}</span>
          <button
            onClick={() => setFileError(null)}
            className="ml-auto p-1 hover:bg-red-100 rounded"
          >
            <FiX className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Drag overlay */}
      {isDragOver && (
        <div className="mb-3 p-4 border-2 border-dashed border-emerald-400 rounded-lg bg-emerald-50 text-center">
          <FiImage className="w-8 h-8 mx-auto text-emerald-500 mb-2" />
          <p className="text-sm text-emerald-700">Drop file to attach</p>
        </div>
      )}

      {/* Input area */}
      <div className="flex gap-2">
        {/* File attachment button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isLoading}
          className="flex-shrink-0 p-2 text-gray-500 hover:text-emerald-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Attach file"
        >
          <FiPaperclip className="w-5 h-5" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileChange}
          accept={ALLOWED_MIME_TYPES.join(",")}
          className="hidden"
        />

        {/* Text input */}
        <TextArea
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            if (e.target.value.length > 0 && onTyping) {
              onTyping();
            }
          }}
          placeholder={selectedFile ? "Add a message (optional)..." : "Write your message here..."}
          minRows={2}
          maxRows={6}
          maxLength={2000}
          showCounter={message.length > 1600}
          onKeyPress={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          className="flex-1"
          disabled={disabled}
          autoResize={true}
        />

        {/* Send button */}
        <Button
          variant="primary"
          onClick={handleSend}
          disabled={(!message.trim() && !selectedFile) || disabled || isLoading}
          isLoading={isLoading}
          className="flex-shrink-0"
        >
          <FiSend className="w-4 h-4" />
        </Button>
      </div>

      {/* Help text */}
      <p className="text-xs text-gray-500 mt-2">
        Press Enter to send, Shift+Enter for new line. Attach images (up to 5MB) or documents (up to 10MB).
      </p>
    </div>
  );
}
