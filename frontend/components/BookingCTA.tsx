"use client";

import { useRouter } from "next/navigation";
import { FiCalendar, FiArrowRight } from "react-icons/fi";
import Button from "./Button";

interface BookingCTAProps {
  tutorId: number;
  tutorName: string;
  messageCount: number;
}

export default function BookingCTA({ tutorId, tutorName, messageCount }: BookingCTAProps) {
  const router = useRouter();

  if (messageCount < 3) {
    return null; // Don't show CTA until 3+ messages exchanged
  }

  return (
    <div className="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-200 rounded-lg p-4 mb-4">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center">
          <FiCalendar className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-gray-900 mb-1">
            Ready to book a lesson?
          </h4>
          <p className="text-sm text-gray-600 mb-3">
            You&apos;ve been chatting with {tutorName}. Book your first lesson to get started!
          </p>
          <Button
            variant="primary"
            size="sm"
            onClick={() => router.push(`/tutors/${tutorId}`)}
            className="flex items-center gap-2"
          >
            <span>View Profile & Book</span>
            <FiArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
