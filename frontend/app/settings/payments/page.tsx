"use client";

import { FiCreditCard, FiDollarSign } from "react-icons/fi";
import SettingsCard from "@/components/settings/SettingsCard";

export default function PaymentsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          💰 Payments & Billing
        </h2>
        <p className="text-slate-600">
          Manage your payment methods and transaction history
        </p>
      </div>

      <SettingsCard title="Payment Methods">
        <div className="text-center py-8">
          <FiCreditCard className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-600">Payment integration coming soon</p>
        </div>
      </SettingsCard>
    </div>
  );
}
