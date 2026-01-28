"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import BookingsPageContent from "./BookingsPageContent";

export default function BookingsPage() {
  return (
    <ProtectedRoute showNavbar={false}>
      <BookingsPageContent />
    </ProtectedRoute>
  );
}
