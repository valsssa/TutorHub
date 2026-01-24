# API-Database Compatibility TODO

**Generated:** January 24, 2026  
**Based on:** `docs/API_DATABASE_COMPATIBILITY_ANALYSIS.md`  
**Current Compatibility:** 87%  
**Target Compatibility:** 95%+

---

## Table of Contents

1. [High Priority Fixes](#high-priority-fixes)
2. [Medium Priority Enhancements](#medium-priority-enhancements)
3. [Low Priority / Nice to Have](#low-priority--nice-to-have)
4. [Documentation Updates](#documentation-updates)
5. [Field Name Fixes](#field-name-fixes)
6. [Missing API Endpoints](#missing-api-endpoints)

---

## High Priority Fixes

### 1. Booking Status Inconsistencies

**Status:** 🔴 Not Started  
**Priority:** High  
**Estimated Effort:** 2-4 hours

**Tasks:**
- [ ] Update API documentation to document all 8 booking statuses:
  - `PENDING`
  - `CONFIRMED`
  - `CANCELLED_BY_STUDENT`
  - `CANCELLED_BY_TUTOR`
  - `NO_SHOW_STUDENT`
  - `NO_SHOW_TUTOR`
  - `COMPLETED`
  - `REFUNDED`
- [ ] Remove `"upcoming"` from status documentation (it's a filter, not a status)
- [ ] Update frontend to handle separate cancellation statuses
- [ ] Add validation in backend to enforce status values
- [ ] Update API response examples in `docs/API_REFERENCE.md`

**Files to Update:**
- `docs/API_REFERENCE.md` - Booking endpoints section
- `backend/modules/bookings/presentation/api.py` - Status validation
- `frontend/lib/api.ts` - Booking types
- `frontend/types/index.ts` - BookingStatus enum

**Acceptance Criteria:**
- All 8 statuses documented in API reference
- Frontend correctly displays cancellation reasons
- Backend validates status against database constraint

---

### 2. Student Profile Field Mismatches

**Status:** 🔴 Not Started  
**Priority:** High  
**Estimated Effort:** 3-5 hours

**Tasks:**
- [ ] **Decision Required:** Choose one approach:
  - Option A: Fix API to use `grade_level` instead of `education_level`
  - Option B: Add `education_level` column to `student_profiles` table
- [ ] **Decision Required:** Choose one approach:
  - Option A: Add `preferred_learning_style` column to `student_profiles` table
  - Option B: Remove `preferred_learning_style` from API documentation
- [ ] Update `GET /api/students/me` endpoint to return correct field names
- [ ] Update frontend to use correct field names
- [ ] Document that `timezone` comes from `users` table, not `student_profiles`
- [ ] Add migration if adding new columns (Option B for either field)

**Files to Update:**
- `backend/modules/students/presentation/api.py` - Field mapping
- `backend/schemas.py` - StudentProfileResponse schema
- `frontend/lib/api.ts` - Student profile types
- `docs/API_REFERENCE.md` - Student endpoints section
- `database/migrations/XXX_fix_student_profile_fields.sql` (if adding columns)

**Acceptance Criteria:**
- API returns fields matching database schema
- Frontend displays correct field values
- Documentation accurately reflects data source

---

### 3. Teaching Philosophy Field

**Status:** 🔴 Not Started  
**Priority:** High  
**Estimated Effort:** 1-2 hours

**Tasks:**
- [ ] Add `teaching_philosophy` field to `PATCH /api/tutors/me/about` endpoint
- [ ] Update `TutorAboutUpdate` schema to include `teaching_philosophy`
- [ ] Update tutor profile response to include `teaching_philosophy`
- [ ] Update frontend tutor profile form to include teaching philosophy textarea
- [ ] Document field in API reference

**Files to Update:**
- `backend/modules/tutor_profile/presentation/api.py` - About endpoint
- `backend/schemas.py` - TutorAboutUpdate schema
- `frontend/app/tutor/profile/page.tsx` - Profile form
- `docs/API_REFERENCE.md` - Tutor endpoints section

**Acceptance Criteria:**
- Tutors can update teaching philosophy via API
- Field appears in tutor profile responses
- Frontend form includes teaching philosophy input

---

### 4. Payment Endpoints Implementation

**Status:** 🔴 Not Started  
**Priority:** High  
**Estimated Effort:** 16-24 hours

**Tasks:**
- [ ] Create payment service module
- [ ] Implement `POST /api/payments` - Initiate payment
  - [ ] Create PaymentCreate schema
  - [ ] Integrate with Stripe/Adyen/PayPal
  - [ ] Store payment record in `payments` table
  - [ ] Handle payment status updates
- [ ] Implement `GET /api/payments/{payment_id}` - Payment status
- [ ] Implement `POST /api/refunds` - Request refund
  - [ ] Create RefundCreate schema
  - [ ] Process refund through payment provider
  - [ ] Update booking status if applicable
- [ ] Implement `GET /api/tutors/payouts` - Tutor payout history
- [ ] Add payment webhook handlers for provider callbacks
- [ ] Document all payment endpoints in API reference
- [ ] Add payment tests

**Files to Create:**
- `backend/modules/payments/presentation/api.py`
- `backend/modules/payments/application/services.py`
- `backend/modules/payments/infrastructure/repositories.py`
- `backend/modules/payments/schemas.py`
- `backend/tests/test_payments.py`

**Files to Update:**
- `backend/schemas.py` - Payment schemas
- `docs/API_REFERENCE.md` - Payment endpoints section
- `frontend/lib/api.ts` - Payment API client
- `frontend/types/index.ts` - Payment types

**Acceptance Criteria:**
- All payment endpoints functional
- Payment records stored correctly
- Refunds processed correctly
- Tutor payouts tracked
- Comprehensive test coverage

---

### 5. Endpoint Path Documentation Fix

**Status:** 🔴 Not Started  
**Priority:** High  
**Estimated Effort:** 30 minutes

**Tasks:**
- [ ] Update `docs/API_REFERENCE.md` to change `GET /api/tutors/me` to `GET /api/tutors/me/profile`
- [ ] Verify all other endpoint paths match actual implementation
- [ ] Update frontend API client if needed
- [ ] Update any integration tests

**Files to Update:**
- `docs/API_REFERENCE.md` - Tutor endpoints section
- `frontend/lib/api.ts` - Verify endpoint paths

**Acceptance Criteria:**
- All documented endpoints match actual implementation
- Frontend uses correct endpoint paths

---

## Medium Priority Enhancements

### 6. Enhanced Tutor Subjects API

**Status:** 🔴 Not Started  
**Priority:** Medium  
**Estimated Effort:** 4-6 hours

**Tasks:**
- [ ] Update `PUT /api/tutors/me/subjects` to accept proficiency and experience
- [ ] Create new schema: `TutorSubjectUpdate` with:
  - `subject_id` (required)
  - `proficiency_level` (optional, default: 'B2')
  - `years_experience` (optional)
- [ ] Update endpoint to handle new schema format
- [ ] Update frontend to collect proficiency and experience per subject
- [ ] Update API documentation

**Files to Update:**
- `backend/modules/tutor_profile/presentation/api.py` - Subjects endpoint
- `backend/schemas.py` - TutorSubjectUpdate schema
- `frontend/app/tutor/profile/page.tsx` - Subjects form
- `docs/API_REFERENCE.md` - Tutor subjects endpoint

**Acceptance Criteria:**
- API accepts proficiency_level and years_experience
- Frontend form collects this data
- Data stored correctly in `tutor_subjects` table

---

### 7. Tutor Certification Details Enhancement

**Status:** 🔴 Not Started  
**Priority:** Medium  
**Estimated Effort:** 4-6 hours

**Tasks:**
- [ ] Update `PUT /api/tutors/me/certifications` schema to match database:
  - Change `title` → `name`
  - Change `issuer` → `issuing_organization`
  - Change `year` → `issue_date` (full date, not just year)
  - Add `expiration_date`
  - Add `credential_id`
  - Add `credential_url`
  - Add `document_url`
- [ ] Update endpoint implementation
- [ ] Update frontend certification form
- [ ] Add file upload for document_url
- [ ] Update API documentation

**Files to Update:**
- `backend/modules/tutor_profile/presentation/api.py` - Certifications endpoint
- `backend/schemas.py` - Certification schemas
- `frontend/app/tutor/profile/page.tsx` - Certifications form
- `docs/API_REFERENCE.md` - Certifications endpoint

**Acceptance Criteria:**
- API field names match database schema
- All certification fields can be submitted
- Document uploads work correctly

---

### 8. Session Materials Endpoints

**Status:** 🔴 Not Started  
**Priority:** Medium  
**Estimated Effort:** 6-8 hours

**Tasks:**
- [ ] Implement `GET /api/bookings/{booking_id}/materials` - List materials
- [ ] Implement `POST /api/bookings/{booking_id}/materials` - Upload material
  - [ ] Multipart file upload
  - [ ] Store file in secure storage
  - [ ] Create record in `session_materials` table
  - [ ] Virus scanning integration
- [ ] Implement `GET /api/bookings/{booking_id}/materials/{material_id}` - Download material
- [ ] Implement `DELETE /api/bookings/{booking_id}/materials/{material_id}` - Delete material
- [ ] Add authorization checks (tutor or student for booking)
- [ ] Document endpoints in API reference
- [ ] Add tests

**Files to Create:**
- `backend/modules/session_materials/presentation/api.py`
- `backend/modules/session_materials/application/services.py`
- `backend/modules/session_materials/infrastructure/repositories.py`
- `backend/modules/session_materials/schemas.py`
- `backend/tests/test_session_materials.py`

**Files to Update:**
- `docs/API_REFERENCE.md` - Session materials endpoints
- `frontend/lib/api.ts` - Session materials API client
- `frontend/app/bookings/[id]/page.tsx` - Materials display

**Acceptance Criteria:**
- All CRUD operations work for session materials
- File uploads secure and scanned
- Authorization properly enforced
- Materials visible in booking details

---

### 9. Student Package Management

**Status:** 🔴 Not Started  
**Priority:** Medium  
**Estimated Effort:** 8-12 hours

**Tasks:**
- [ ] Implement `GET /api/students/packages` - List purchased packages
  - [ ] Filter by status (active, expired, used)
  - [ ] Include tutor and pricing option details
- [ ] Implement `POST /api/students/packages` - Purchase new package
  - [ ] Validate pricing option exists
  - [ ] Create payment intent
  - [ ] Create package record after payment
- [ ] Implement `GET /api/students/packages/{package_id}` - Package details
- [ ] Implement `PATCH /api/students/packages/{package_id}` - Update package (limited fields)
- [ ] Update booking creation to use packages
- [ ] Document endpoints in API reference
- [ ] Add tests

**Files to Create:**
- `backend/modules/student_packages/presentation/api.py`
- `backend/modules/student_packages/application/services.py`
- `backend/modules/student_packages/infrastructure/repositories.py`
- `backend/modules/student_packages/schemas.py`
- `backend/tests/test_student_packages.py`

**Files to Update:**
- `backend/modules/bookings/presentation/api.py` - Package usage
- `docs/API_REFERENCE.md` - Student packages endpoints
- `frontend/lib/api.ts` - Packages API client
- `frontend/app/student/packages/page.tsx` - Packages list

**Acceptance Criteria:**
- Students can purchase and view packages
- Bookings can use package sessions
- Package status tracked correctly
- Expiration handled properly

---

### 10. Notification Preferences API

**Status:** 🔴 Not Started  
**Priority:** Medium  
**Estimated Effort:** 4-6 hours

**Tasks:**
- [ ] Implement `GET /api/notifications/preferences` - Get user preferences
- [ ] Implement `PUT /api/notifications/preferences` - Update preferences
  - [ ] Quiet hours (start_time, end_time)
  - [ ] Channel preferences (in_app, email, push, sms)
  - [ ] Category preferences
- [ ] Update notification service to respect preferences
- [ ] Document endpoints in API reference
- [ ] Add frontend settings page

**Files to Create:**
- `backend/modules/notifications/preferences/api.py`
- `backend/modules/notifications/preferences/schemas.py`

**Files to Update:**
- `backend/modules/notifications/service.py` - Respect preferences
- `docs/API_REFERENCE.md` - Notification preferences endpoints
- `frontend/app/settings/notifications/page.tsx` - Preferences UI

**Acceptance Criteria:**
- Users can view and update notification preferences
- Notifications respect user preferences
- Quiet hours enforced

---

### 11. Tutor Pricing Options CRUD

**Status:** 🔴 Not Started  
**Priority:** Medium  
**Estimated Effort:** 6-8 hours

**Tasks:**
- [ ] Implement `GET /api/tutors/me/pricing-options` - List pricing options
- [ ] Implement `POST /api/tutors/me/pricing-options` - Create pricing option
- [ ] Implement `PUT /api/tutors/me/pricing-options/{option_id}` - Update pricing option
- [ ] Implement `DELETE /api/tutors/me/pricing-options/{option_id}` - Delete pricing option
- [ ] Validate pricing option data (duration, price, etc.)
- [ ] Document endpoints in API reference
- [ ] Add frontend pricing options management UI
- [ ] Add tests

**Files to Create:**
- `backend/modules/tutor_pricing/presentation/api.py`
- `backend/modules/tutor_pricing/application/services.py`
- `backend/modules/tutor_pricing/schemas.py`
- `backend/tests/test_tutor_pricing.py`

**Files to Update:**
- `docs/API_REFERENCE.md` - Pricing options endpoints
- `frontend/app/tutor/profile/pricing/page.tsx` - Pricing options UI

**Acceptance Criteria:**
- Tutors can manage pricing options
- Options validated correctly
- Options appear in tutor profile

---

## Low Priority / Nice to Have

### 12. Advanced Notification Features

**Status:** 🔴 Not Started  
**Priority:** Low  
**Estimated Effort:** 8-12 hours

**Tasks:**
- [ ] Implement `GET /api/admin/notifications/templates` - List templates (admin only)
- [ ] Implement `GET /api/admin/notifications/queue` - View notification queue (admin only)
- [ ] Add filtering and pagination
- [ ] Document endpoints

**Files to Create:**
- `backend/modules/notifications/admin/api.py`

**Files to Update:**
- `docs/API_REFERENCE.md` - Admin notification endpoints

---

### 13. Tutor Metrics Dashboard API

**Status:** 🔴 Not Started  
**Priority:** Low  
**Estimated Effort:** 6-8 hours

**Tasks:**
- [ ] Implement `GET /api/tutors/me/metrics` - Tutor's own metrics
- [ ] Implement `GET /api/admin/tutors/{tutor_id}/metrics` - Admin view
- [ ] Implement `GET /api/admin/dashboard/tutor-metrics` - Aggregated metrics
- [ ] Calculate metrics from existing data
- [ ] Document endpoints

**Files to Create:**
- `backend/modules/tutor_metrics/presentation/api.py`
- `backend/modules/tutor_metrics/application/services.py`
- `backend/modules/tutor_metrics/schemas.py`

**Files to Update:**
- `docs/API_REFERENCE.md` - Tutor metrics endpoints
- `frontend/app/tutor/dashboard/metrics/page.tsx` - Metrics display

---

### 14. Subject Localization Support

**Status:** 🔴 Not Started  
**Priority:** Low  
**Estimated Effort:** 4-6 hours

**Tasks:**
- [ ] Add `Accept-Language` header support to `GET /api/subjects`
- [ ] Query `subject_localizations` table based on user's `preferred_language`
- [ ] Return localized names when available
- [ ] Fallback to English if translation missing
- [ ] Document localization behavior

**Files to Update:**
- `backend/modules/subjects/presentation/api.py` - Localization logic
- `docs/API_REFERENCE.md` - Localization notes

---

### 15. Message Attachment Metadata

**Status:** 🔴 Not Started  
**Priority:** Low  
**Estimated Effort:** 2-4 hours

**Tasks:**
- [ ] Expose `is_scanned` and `scan_result` in attachment responses
- [ ] Expose `width`, `height`, `duration_seconds` for media files
- [ ] Update `MessageAttachmentResponse` schema
- [ ] Document security features

**Files to Update:**
- `backend/schemas.py` - MessageAttachmentResponse
- `docs/API_REFERENCE.md` - Attachment metadata

---

### 16. Audit Log Enhancements

**Status:** 🔴 Not Started  
**Priority:** Low  
**Estimated Effort:** 2-3 hours

**Tasks:**
- [ ] Add `table_name` and `record_id` to audit log API response
- [ ] Add filtering by `table_name`, `action`, `changed_by`
- [ ] Update `GET /api/audit/logs` endpoint
- [ ] Consider renaming fields to match database:
  - `user_id` → `changed_by`
  - `created_at` → `changed_at`

**Files to Update:**
- `backend/modules/admin/presentation/api.py` - Audit log endpoint
- `backend/schemas.py` - Audit log response schema
- `docs/API_REFERENCE.md` - Audit log endpoint

---

## Documentation Updates

### 17. Update API Reference Documentation

**Status:** 🔴 Not Started  
**Priority:** High  
**Estimated Effort:** 8-12 hours

**Tasks:**
- [ ] Add all missing endpoints to `docs/API_REFERENCE.md`:
  - Payment endpoints
  - Student package endpoints
  - Session materials endpoints
  - Tutor pricing options endpoints
  - Notification preferences endpoints
- [ ] Update existing endpoint documentation:
  - Fix endpoint paths
  - Add missing fields
  - Clarify field mappings
- [ ] Add examples for all endpoints
- [ ] Document error responses
- [ ] Add rate limiting information

**Files to Update:**
- `docs/API_REFERENCE.md` - Complete rewrite/update

---

## Field Name Fixes

### 18. Fix Field Name Mismatches

**Status:** 🔴 Not Started  
**Priority:** Medium  
**Estimated Effort:** 4-6 hours

**Tasks:**
- [ ] **Document aliases** (no code change needed):
  - [ ] Document `start_at` → `start_time` mapping
  - [ ] Document `price_student` → `total_amount` mapping
  - [ ] Document `data` → `metadata` mapping
- [ ] **Fix in API** (code changes required):
  - [ ] Fix `title` → `name` in tutor certifications
  - [ ] Fix `issuer` → `issuing_organization` in tutor certifications
  - [ ] Fix `education_level` → `grade_level` in student profiles
  - [ ] Fix `user_id` → `changed_by` in audit logs (optional)
  - [ ] Fix `created_at` → `changed_at` in audit logs (optional)

**Files to Update:**
- `backend/schemas.py` - Field names
- `backend/modules/tutor_profile/presentation/api.py` - Certifications
- `backend/modules/students/presentation/api.py` - Student profile
- `backend/modules/admin/presentation/api.py` - Audit logs
- `docs/API_REFERENCE.md` - Document aliases

---

## Missing API Endpoints

### 19. Add Missing Database Fields to API Responses

**Status:** 🔴 Not Started  
**Priority:** Medium  
**Estimated Effort:** 6-8 hours

**Tasks:**
- [ ] Add missing fields to tutor profile responses:
  - [ ] `teaching_philosophy` (High priority)
  - [ ] `profile_status` (High priority)
  - [ ] `pricing_model` (High priority)
  - [ ] `instant_book_enabled` (Medium priority)
  - [ ] `badges` (Medium priority)
  - [ ] `is_identity_verified` (Medium priority)
  - [ ] `profile_completeness_score` (Low priority)
- [ ] Add missing fields to booking responses:
  - [ ] `platform_fee_pct` (High priority)
  - [ ] `join_url` (High priority)
  - [ ] `student_tz` (Medium priority)
  - [ ] `tutor_tz` (Medium priority)
- [ ] Add missing fields to tutor subjects:
  - [ ] `proficiency_level` (Medium priority)
  - [ ] `years_experience` (Medium priority)
- [ ] Add missing fields to user responses:
  - [ ] `preferred_language` (Low priority - already returned, just document)
  - [ ] `locale` (Low priority - already returned, just document)

**Files to Update:**
- `backend/schemas.py` - Response schemas
- `backend/modules/tutor_profile/presentation/api.py` - Profile responses
- `backend/modules/bookings/presentation/api.py` - Booking responses
- `docs/API_REFERENCE.md` - Response examples

---

## Implementation Guidelines

### Code Quality Standards

- ✅ All new endpoints must have:
  - Type hints (100% coverage)
  - Docstrings
  - Rate limiting
  - Error handling
  - Logging
  - Tests (unit + integration)

- ✅ All schema changes must:
  - Match database column names where possible
  - Include validation
  - Have Pydantic models
  - Be documented in API reference

- ✅ All database changes must:
  - Include migration files
  - Update `database/init.sql`
  - Update models in `backend/models/`
  - Be tested

### Testing Requirements

- Unit tests for all service logic
- Integration tests for all endpoints
- E2E tests for critical flows
- Test coverage target: 80%+

### Documentation Requirements

- Update `docs/API_REFERENCE.md` for all new/changed endpoints
- Update `docs/API_DATABASE_COMPATIBILITY_ANALYSIS.md` after changes
- Add examples to all endpoint documentation
- Document error responses

---

## Progress Tracking

**Last Updated:** January 24, 2026

### Summary

- **Total Tasks:** 19
- **Completed:** 0
- **In Progress:** 0
- **Not Started:** 19
- **Blocked:** 0

### By Priority

- **High Priority:** 5 tasks
- **Medium Priority:** 6 tasks
- **Low Priority:** 5 tasks
- **Documentation:** 1 task
- **Field Fixes:** 1 task
- **Missing Endpoints:** 1 task

---

## Notes

- All tasks should be completed in Docker containers (never run services directly)
- Follow architectural principles from `CLAUDE.md` and `AGENTS.md`
- Run full test suite before committing changes
- Update compatibility analysis document after each major change

---

**Maintained By:** Development Team  
**Review Frequency:** Weekly during active development
