"use client";

import { ReactNode } from "react";
import { AlertTriangle, Info, CheckCircle, XCircle, LucideIcon } from "lucide-react";
import Modal from "./Modal";
import Button from "./Button";
import clsx from "clsx";

type ConfirmDialogVariant = "danger" | "warning" | "info" | "success";

interface ConfirmDialogProps {
  /** Whether the dialog is open */
  isOpen: boolean;
  /** Called when dialog should close */
  onClose: () => void;
  /** Called when user confirms */
  onConfirm: () => void | Promise<void>;
  /** Dialog title */
  title: string;
  /** Dialog message/description */
  message: string | ReactNode;
  /** Variant affects icon and button styling */
  variant?: ConfirmDialogVariant;
  /** Confirm button text */
  confirmText?: string;
  /** Cancel button text */
  cancelText?: string;
  /** Whether confirm action is loading */
  isLoading?: boolean;
  /** Disable confirm button */
  confirmDisabled?: boolean;
  /** Custom icon */
  icon?: LucideIcon;
  /** Additional content below message */
  children?: ReactNode;
}

const variantConfig: Record<
  ConfirmDialogVariant,
  {
    icon: LucideIcon;
    iconBg: string;
    iconColor: string;
    confirmVariant: "danger" | "primary" | "secondary";
  }
> = {
  danger: {
    icon: AlertTriangle,
    iconBg: "bg-red-100 dark:bg-red-900/30",
    iconColor: "text-red-600 dark:text-red-400",
    confirmVariant: "danger",
  },
  warning: {
    icon: AlertTriangle,
    iconBg: "bg-amber-100 dark:bg-amber-900/30",
    iconColor: "text-amber-600 dark:text-amber-400",
    confirmVariant: "primary",
  },
  info: {
    icon: Info,
    iconBg: "bg-blue-100 dark:bg-blue-900/30",
    iconColor: "text-blue-600 dark:text-blue-400",
    confirmVariant: "primary",
  },
  success: {
    icon: CheckCircle,
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    confirmVariant: "primary",
  },
};

export default function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  variant = "danger",
  confirmText = "Confirm",
  cancelText = "Cancel",
  isLoading = false,
  confirmDisabled = false,
  icon,
  children,
}: ConfirmDialogProps) {
  const config = variantConfig[variant];
  const IconComponent = icon || config.icon;

  const handleConfirm = async () => {
    await onConfirm();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <div className="flex flex-col-reverse sm:flex-row gap-3">
          <Button
            variant="ghost"
            onClick={onClose}
            disabled={isLoading}
            className="flex-1"
          >
            {cancelText}
          </Button>
          <Button
            variant={config.confirmVariant}
            onClick={handleConfirm}
            isLoading={isLoading}
            disabled={confirmDisabled}
            className="flex-1"
          >
            {confirmText}
          </Button>
        </div>
      }
    >
      <div className="flex flex-col items-center text-center sm:flex-row sm:items-start sm:text-left gap-4">
        {/* Icon */}
        <div
          className={clsx(
            "w-12 h-12 rounded-full flex items-center justify-center shrink-0",
            config.iconBg
          )}
        >
          <IconComponent className={clsx("w-6 h-6", config.iconColor)} />
        </div>

        {/* Content */}
        <div className="space-y-2">
          {typeof message === "string" ? (
            <p className="text-slate-600 dark:text-slate-400">{message}</p>
          ) : (
            message
          )}
          {children}
        </div>
      </div>
    </Modal>
  );
}

// Pre-configured confirm dialogs for common use cases
export function DeleteConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  itemName = "this item",
  isLoading,
}: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  itemName?: string;
  isLoading?: boolean;
}) {
  return (
    <ConfirmDialog
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      title="Delete Confirmation"
      message={`Are you sure you want to delete ${itemName}? This action cannot be undone.`}
      variant="danger"
      confirmText="Delete"
      isLoading={isLoading}
    />
  );
}

export function LogoutConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  isLoading,
}: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  isLoading?: boolean;
}) {
  return (
    <ConfirmDialog
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      title="Sign Out"
      message="Are you sure you want to sign out? You'll need to sign in again to access your account."
      variant="warning"
      confirmText="Sign Out"
      isLoading={isLoading}
    />
  );
}

export function UnsavedChangesDialog({
  isOpen,
  onClose,
  onConfirm,
  onSave,
  isSaving,
}: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  onSave?: () => void | Promise<void>;
  isSaving?: boolean;
}) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Unsaved Changes"
      size="sm"
      footer={
        <div className="flex flex-col sm:flex-row gap-3">
          <Button variant="ghost" onClick={onClose} className="flex-1">
            Keep Editing
          </Button>
          <Button variant="secondary" onClick={onConfirm} className="flex-1">
            Discard Changes
          </Button>
          {onSave && (
            <Button
              variant="primary"
              onClick={onSave}
              isLoading={isSaving}
              className="flex-1"
            >
              Save Changes
            </Button>
          )}
        </div>
      }
    >
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center shrink-0">
          <AlertTriangle className="w-6 h-6 text-amber-600 dark:text-amber-400" />
        </div>
        <p className="text-slate-600 dark:text-slate-400">
          You have unsaved changes. Would you like to save them before leaving?
        </p>
      </div>
    </Modal>
  );
}
