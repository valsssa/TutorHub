
# EduConnect Backend Integration Guide

## 0. Document Purpose & Scope
*   **Product:** EduConnect (Online Tutoring Marketplace).
*   **Current State:** High-fidelity React frontend with in-memory mock data (`constants.ts`) and simulated business logic.
*   **Purpose:** This document defines the contract between Frontend and Backend to enable the transition from prototype to production.
*   **Scope:** Covers data schemas, API contracts, state management, and error handling. Out of scope: specific backend language implementation details (Node/Python agnostic).

---

## 1. High-Level System Overview
*   **App Type:** Single Page Application (SPA), Client-Side Rendering (CSR).
*   **User Roles:** Student, Tutor, Admin.
*   **Core Flows:**
    1.  **Discovery:** Search/Filter Tutors.
    2.  **Booking:** Slot selection & Payment simulation.
    3.  **Learning:** Video classroom (simulated).
    4.  **Tutor Ops:** Schedule management & CRM.
*   **Architecture Goal:** Frontend manages UI state; Backend owns data persistence, auth, and business rules.

---

## 2. Technology Stack & Constraints
*   **Frontend:** React 19, TypeScript, Tailwind CSS.
*   **State:** React Context/State (migrating to React Query upon integration).
*   **Auth:** JWT-based stateless authentication expected.
*   **Environment:**
    *   `API_BASE_URL` configurable via env vars.
    *   API Key for Gemini (AI) managed via backend proxy in production.

---

## 3. Design Philosophy & Data Ownership
*   **Source of Truth:** Backend Database (PostgreSQL).
*   **Computed Data:** Frontend handles display logic (e.g., formatting dates, filtering lists locally for speed if dataset is small), but Backend must perform critical calculations (Wallet Balance, Total Earnings, Tutor Rating).
*   **Optimistic UI:** Used for "Save Tutor", "Send Message", and "Book Session". Backend must support rapid responses or handle eventual consistency.

---

## 4. Domain Model
*   **User:** Base identity.
*   **Tutor:** Profile extension with availability and subjects.
*   **Session:** Booking transaction with status (`upcoming`, `completed`, `cancelled`).
*   **VerificationRequest:** Compliance document workflow.
*   **Chat:** Real-time messaging entities.

---

## 5. Data Types & Contracts
*   Refer to `docs/data_types_and_contracts.txt` for exact field definitions.
*   **Critical Format:** Dates must be ISO 8601 strings (UTC).
*   **Currency:** Integers (cents) or Decimals (safe parsing required).

---

## 6. State Management Strategy
*   **Global State:** User Session, Dictionary Data (Subjects, Countries).
*   **Server State:** Lists (Tutors, Sessions), Profile Details.
*   **Cache Strategy:** Stale-while-revalidate.
*   **Invalidation:**
    *   Booking a session -> Invalidates `user_balance` and `tutor_availability`.
    *   Accepting a request -> Invalidates `session_list`.

---

## 7. API Expectations
*   Refer to `docs/api_expectations.txt` for endpoint definitions.
*   **Pagination:** Cursor-based preferred for infinite scroll (Marketplace), Offset-based for tables (Admin).
*   **Latency:** <200ms for GET requests is the target.

---

## 8. Authentication & Authorization
*   **Mechanism:** JWT Access Token (Short-lived) + HttpOnly Cookie Refresh Token.
*   **RBAC:** Enforce role checks on endpoints (e.g., only Tutors can PATCH `/availability`).

---

## 9. Error Handling Contract

**Format:**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested tutor could not be found.",
    "details": { "id": "t99" }
  }
}
```

**Standard Codes:**
*   `400 Bad Request`: Validation failure (missing fields).
*   `401 Unauthorized`: Invalid/Missing token.
*   `403 Forbidden`: Valid token, insufficient permissions.
*   `404 Not Found`: Resource missing.
*   `422 Unprocessable Entity`: Business logic violation (e.g., booking an occupied slot).
*   `500 Internal Server Error`: Generic failure.

**UI Behavior:**
*   Frontend displays the `message` field in a Toast notification for 4xx/5xx errors.
*   Validation errors (400) map to form field error states.

---

## 10. Loading, Empty & Edge States

*   **Loading:** Skeletons used for primary content (Tutor cards, Table rows).
*   **Empty Lists:** Return `[]` (empty array) with `200 OK`. Do NOT return 404 for empty search results.
*   **Nulls:**
    *   `avatarUrl`: Backend sends `null` if none; Frontend displays initial placeholder.
    *   `bio`: Backend sends `null`; Frontend displays fallback text.

---

## 11. Mock Data vs Real Data Mapping

| Frontend Mock Field | Backend Expectation | Notes |
| :--- | :--- | :--- |
| `tutor.isVerified` | `boolean` (computed) | Likely derived from `VerificationRequests` table. |
| `tutor.rating` | `float` (computed) | Aggregated from `Reviews` table. |
| `user.balance` | `decimal` | Transaction ledger sum. |
| `session.price` | `decimal` | Snapshot of tutor rate at booking time. |
| `id` (e.g. "t1") | UUID / Integer | Frontend treats IDs as strings. |

---

## 12. Integration Strategy

**Phase 1: Read-Only (Marketplace)**
1.  Implement `GET /tutors` with filters.
2.  Implement `GET /tutors/:id`.
3.  Replace `constants.MOCK_TUTORS` with API fetch.

**Phase 2: Authentication**
1.  Implement `POST /auth/login` and `/auth/signup`.
2.  Replace `MOCK_USER` with context from API.

**Phase 3: Transactions (Booking)**
1.  Implement `POST /bookings`.
2.  Implement Stripe/Payment integration.

**Phase 4: Real-time**
1.  Implement Chat (WebSockets/Polling).
2.  Implement Notification updates.

---

## 13. Non-Functional Requirements

*   **Performance:**
    *   Marketplace search must return results in < 200ms.
    *   Images must be served via CDN (optimized/resized).
*   **Rate Limiting:**
    *   Public endpoints (Search) need basic rate limiting.
    *   Auth endpoints need strict limiting (brute-force protection).
*   **Timezones:**
    *   All times stored in UTC.
    *   Tutor availability logic must handle timezone conversion correctly.

---

## 14. Open Questions & Assumptions

*   **Video Provider:** Currently simulated. Need to select provider (Zoom, Daily.co, Agora) and define the API flow to generate room tokens.
*   **Search Engine:** Will simple SQL `LIKE` queries suffice, or do we need Algolia/Elasticsearch for the Marketplace?
*   **Payment Split:** How are payouts handled? (Assumed Stripe Connect).
*   **Calendar Sync:** How should Google Calendar authorization be handled? We need an OAuth flow endpoint (`GET /auth/google/calendar`) and webhooks for 2-way synchronization.
