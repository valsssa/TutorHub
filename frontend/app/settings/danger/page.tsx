"use client";

import { useState } from "react";
import { FiAlertTriangle, FiTrash2 } from "react-icons/fi";
import { useRouter } from "next/navigation";
import SettingsCard from "@/components/settings/SettingsCard";
import Button from "@/components/Button";
import { useToast } from "@/components/ToastContainer";

export default function DangerPage() {
  const router = useRouter();
  const { showError, showSuccess } = useToast();
  const [deleteConfirm, setDeleteConfirm] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (deleteConfirm !== "DELETE") {
      showError("Please type DELETE to confirm");
      return;
    }

    setIsDeleting(true);
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));
      showSuccess("Account deletion initiated");
      router.push("/login");
    } catch (error) {
      showError("Failed to delete account");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-red-600 mb-2 flex items-center gap-2">
          <FiAlertTriangle />
          Danger Zone
        </h2>
        <p className="text-slate-600">
          Irreversible and destructive actions
        </p>
      </div>

      {/* Delete Account */}
      <SettingsCard title="Delete Account">
        <div className="space-y-4">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-900 mb-2">
              <strong>Warning:</strong> This action cannot be undone.
            </p>
            <ul className="text-sm text-red-800 space-y-1 list-disc list-inside">
              <li>All your data will be permanently deleted</li>
              <li>Your bookings will be cancelled</li>
              <li>You will lose access to messages and history</li>
            </ul>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Type <code className="bg-slate-100 px-2 py-0.5 rounded text-red-600">DELETE</code> to confirm
            </label>
            <input
              type="text"
              value={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.value)}
              className="w-full px-3 py-2 border border-red-300 rounded-lg focus:ring-2 focus:ring-red-400 focus:border-transparent"
              placeholder="Type DELETE"
            />
          </div>

          <Button
            variant="ghost"
            onClick={handleDelete}
            disabled={deleteConfirm !== "DELETE" || isDeleting}
            className="w-full bg-red-600 hover:bg-red-700 text-white disabled:bg-slate-200 disabled:text-slate-400"
          >
            <FiTrash2 className="w-4 h-4 mr-2" />
            {isDeleting ? "Deleting..." : "Permanently Delete My Account"}
          </Button>
        </div>
      </SettingsCard>
    </div>
  );
}
