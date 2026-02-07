# EduStream Comprehensive Fix Plan

**Date:** 2026-02-07  
**Scope:** Full codebase analysis — backend, frontend-v2, database, tests, infrastructure  
**Status:** Plan created. Fix phase NOT started.  
**Execution Mode:** minimum 3 tasks in parallel per sprint

---

## Executive Summary

This plan consolidates findings from:
- [2026-02-07 UX/UI Audit](../plans/2026-02-07-ux-ui-audit-report.md) — 143 unique issues
- [2026-01-29 Integration Report](../integration_report.md) — 21 API path mismatches
- [2026-01-29 Contract Diff](../contract_diff.md) — Frontend ↔ Backend mapping
- [2026-02-06 Critical Integration Fixes](../plans/2026-02-06-critical-integration-fixes.md) — 45 tasks
- [2026-02-02 Clean Architecture Refactoring](../todo/CLEAN_ARCHITECTURE_REFACTORING.md) — Phase 0-6
- [UX Experience Gap Report](../ux-experience-gap-report.md)
- [issues.md](../issues.md) — Edge cases (all marked fixed)

| Category | Count | Priority |
|----------|-------|----------|
| **UX/UI Critical** | 6 | P0 |
| **UX/UI High** | 28 | P1 |
| **UX/UI Medium** | 62 | P2 |
| **UX/UI Low** | 47 | P3 |
| **API Integration** | 21 | P0 (if frontend paths wrong) |
| **Integration Fixes** | 45 | P1 |
| **Test Infrastructure** | 3 | P0 |
| **Clean Architecture** | ~40 | P2 |

**Total actionable items:** ~200+ (deduplicated)

---

## Part 1: Test & Infrastructure Fixes (P0)

These block verification of all other fixes. Run in parallel.

### Task Group 1A: Test Infrastructure (3 parallel tasks)

| # | Task | Owner | Files | Est. |
|---|------|-------|-------|------|
| 1A.1 | Update `docker-compose.test.yml` to use `frontend-v2` instead of `frontend` | Infra | `docker-compose.test.yml` | 15m |
| 1A.2 | Make Dockerfile.test use public PyPI when nexus times out, or add fallback | Infra | `backend/Dockerfile.test` | 30m |
| 1A.3 | Fix `scripts/lint-all.sh` for Windows (CRLF line endings) | Infra | `scripts/lint-all.sh` | 10m |

**Details:**
- **1A.1:** test-frontend, frontend-tests, frontend-integration-tests, playwright-tests all reference `./frontend` — change to `./frontend-v2`. Verify frontend-v2 has `Dockerfile.test`/`Dockerfile.playwright` or create.
- **1A.2:** Add `RUN pip install --no-cache-dir ruff` fallback to PyPI if nexus.in.lazarev.cloud is unreachable, or use `PIP_INDEX_URL` env override.
- **1A.3:** Run `dos2unix scripts/lint-all.sh` or add `.gitattributes` with `* text=auto eol=lf` for shell scripts.

---

## Part 2: Critical UX Blockers (P0)

Users cannot complete core tasks. Fix in parallel.

### Task Group 2A: Auth & Navigation (3 parallel tasks)

| # | Task | File | Fix |
|---|------|------|-----|
| 2A.1 | Login page redirect ignores `?redirect=` | `app/(auth)/login/page.tsx` | Read `searchParams.get('redirect')`, validate as relative URL, use as post-login destination |
| 2A.2 | 404 "Go back" uses `javascript:` (XSS + non-functional) | `app/not-found.tsx:30` | Replace `<Link href="javascript:history.back()">` with `<button onClick={() => window.history.back()}>` |
| 2A.3 | Registration "email already exists" shows generic error | `app/(auth)/register/page.tsx` | Detect "already exists" error, show: "An account with this email already exists. [Sign in instead](/login)." |

### Task Group 2B: Forms & Infinite Loops (3 parallel tasks)

| # | Task | File | Fix |
|---|------|------|-----|
| 2B.1 | Booking form no past-date validation | `lib/validators/booking.ts` | Add `.refine((val) => new Date(val) > new Date(), 'Date must be in the future')`; set `min` on datetime-local input |
| 2B.2 | Notification settings infinite re-render | `app/(dashboard)/settings/notifications/page.tsx:148` | Remove `form` from `useEffect` dependency array |
| 2B.3 | Video settings infinite re-render | `app/(dashboard)/settings/video/page.tsx:144-151` | Same — remove `form` from deps |

---

## Part 3: High-Priority UX Fixes (P1)

Broken/confusing features. Execute in parallel groups.

### Task Group 3A: Button & Layout (3 parallel tasks)

| # | Task | File | Fix |
|---|------|------|-----|
| 3A.1 | Button `asChild` broken — no loading/disabled forwarding | `components/ui/button.tsx` | Implement Radix Slot pattern or document as styling-only; fix 15+ usages |
| 3A.2 | Landing CTA: `<Link><Button>` invalid nested HTML | `app/page.tsx` | Use `<Button asChild><Link>` or `buttonVariants()` on Link |
| 3A.3 | Tutor dashboard same nesting | `app/(dashboard)/tutor/page.tsx` | Same as 3A.2 |

### Task Group 3B: Messaging & Notifications (3 parallel tasks)

| # | Task | File | Fix |
|---|------|------|-----|
| 3B.1 | Real-time messages NOT wired into conversation page | `app/(dashboard)/messages/[conversationId]/page.tsx` | Import and use `useRealtimeMessages`; wire `onNewMessage` to append to list |
| 3B.2 | Notification `type` filter not sent to backend | `lib/api/notifications.ts` | Add `if (filters?.type) params.type = filters.type;` |
| 3B.3 | `is_read` vs `read` field inconsistency | `notification-item.tsx`, `notification-bell.tsx`, `notifications/page.tsx` | Standardize on one field; add normalizer at API layer |

### Task Group 3C: Booking & Tutor Profile (3 parallel tasks)

| # | Task | File | Fix |
|---|------|------|-----|
| 3C.1 | Join Session button has no href/onClick | `app/(dashboard)/bookings/[id]/page.tsx:261-265` | Link to `booking.join_url` |
| 3C.2 | Request Reschedule button has no functionality | `app/(dashboard)/bookings/[id]/page.tsx:268-272` | Implement reschedule modal using `useRescheduleBooking` |
| 3C.3 | Load more reviews replaces instead of appending | `app/(dashboard)/tutors/[id]/page.tsx:438-445` | Use `useInfiniteQuery` or accumulate pages in state |

### Task Group 3D: Dead-End Nav & Placeholders (3 parallel tasks)

| # | Task | Routes | Fix |
|---|------|--------|-----|
| 3D.1 | Create placeholder pages for admin 404s | `/admin/users`, `/admin/approvals`, `/admin/reports`, `/admin/tutors` | Create "Coming Soon" pages or hide nav items |
| 3D.2 | Create placeholder pages for owner 404s | `/owner/analytics`, `/owner/admins`, `/owner/financial`, `/owner/config`, `/owner/reports`, `/owner/settings` | Same |
| 3D.3 | Notification bell always shows red dot | `components/layouts/topbar.tsx:89` | Fetch unread count; show badge conditionally |

---

## Part 4: API Integration (P0 if Broken)

**Note:** `frontend-v2` uses `BASE_URL` with `/api/v1`; paths may already be correct. Verify first.

### Task Group 4A: API Path Audit (3 parallel tasks)

| # | Task | Scope | Action |
|---|------|-------|--------|
| 4A.1 | Audit frontend-v2 messages API | `lib/api/messages.ts` | Ensure all paths start with `/api/v1` or use BASE_URL correctly |
| 4A.2 | Audit frontend-v2 notifications API | `lib/api/notifications.ts` | Same |
| 4A.3 | Audit frontend-v2 favorites, admin, student-notes | `lib/api/favorites.ts`, `admin.ts`, `student-notes.ts` | Same |

**If mismatches found:** Add `/v1/` to paths. See [contract_diff.md](../contract_diff.md) for exact list.

---

## Part 5: Critical Integration Fixes (from 2026-02-06 plan)

Execute phases in order; within each phase, run 3+ tasks in parallel.

### Phase 1: DateTime/Timezone (3 parallel)

| Task | File | Action |
|------|------|--------|
| 5.1 | `backend/core/datetime_utils.py` | Create `utc_now()`, `is_aware()`, `ensure_utc()` |
| 5.2 | `backend/modules/bookings/presentation/api.py`, `state_machine.py` | Replace `datetime.utcnow()` with `utc_now()` |
| 5.3 | `backend/core/audit.py`, `feature_flags.py`, `ports/email.py` | Same |

### Phase 2: Booking State Enum (1 task)

| Task | File | Action |
|------|------|--------|
| 5.4 | `backend/modules/bookings/domain/entities.py` | Align default `session_state`/`session_outcome` with DB constraints |

### Phase 3: Frontend Type Alignment (3 parallel per batch)

| Batch | Tasks | Files |
|-------|-------|-------|
| 3a | 5–7 | `types/booking.ts`, `types/user.ts`, `types/booking.ts` (fields) |
| 3b | 8–10 | `types/message.ts`, `types/tutor.ts`, `types/notification.ts` |
| 3c | 11–12 | `types/booking.ts` (DisputeState), `types/api.ts` |

### Phase 4–12: See [2026-02-06-critical-integration-fixes.md](2026-02-06-critical-integration-fixes.md)

---

## Part 6: Medium/Low UX Fixes (P2–P3)

From UX audit, prioritized by impact. Run in batches of 3+.

### Batch 6A: Forms & Validation

- M1: Password hint disappears when error shows
- M2: No loading state on role buttons during registration
- M5: Input missing `aria-describedby` for errors
- M6: Input missing `aria-invalid` when error present

### Batch 6B: Navigation & Layout

- M13: Auth layout brand "EduStream" not link to home
- M14–M15: Register/Forgot password don't redirect authenticated users
- M17: Settings sidebar overlaps nav items

### Batch 6C: Messaging & Notifications

- M35: Message input single-line → textarea
- M39: No pagination on notifications page
- M41: Notification bell dropdown lacks keyboard accessibility

---

## Part 7: Clean Architecture Phase 0 (from CLEAN_ARCHITECTURE_REFACTORING.md)

| Pattern | Status | Remaining |
|---------|--------|-----------|
| 404 error handling | ~21 done | Continue replacements |
| Role-based access | ~13 done | Replace tutor checks |
| Soft-delete filters | ~8 done | Consider SQLAlchemy event |
| Transaction handling | Not started | 40+ try/except blocks |
| Pagination | Not started | 7+ manual calculations |
| Input sanitization | Not started | 30+ patterns |
| DateTime utilities | Not started | 15+ calls |

---

## Execution Matrix

| Sprint | Parallel Groups | Tasks | Est. |
|--------|-----------------|-------|------|
| 1 | 1A (3) + 2A (3) + 2B (3) | 9 | 2–3h |
| 2 | 3A (3) + 3B (3) + 3C (3) | 9 | 3–4h |
| 3 | 3D (3) + 4A (3) + 5.1–5.3 | 9 | 2–3h |
| 4 | 5.4 + Phase 3 batches | 10 | 3–4h |
| 5 | Phases 4–8 from integration plan | 15 | 4–6h |
| 6 | Phases 9–12 from integration plan | 12 | 4–6h |
| 7 | Batch 6A–6C + Part 7 | 15 | 4–6h |
| 8+ | Remaining MEDIUM/LOW | 60+ | Ongoing |

---

## Dependencies & Ordering

```
Part 1 (Test Infra) ────► all other parts (enables verification)
Part 2 (Critical UX) ────► no deps
Part 3 (High UX) ───────► Part 2 (some overlap)
Part 4 (API) ───────────► verify before assuming broken
Part 5 (Integration) ───► Phase 1 before Phase 2; else parallel
Part 6 (Medium/Low) ────► after Part 2–3
Part 7 (Clean Arch) ───► independent; can run alongside
```

---

## Verification Checklist

After each sprint:

- [ ] `docker compose -f docker-compose.test.yml up backend-tests --abort-on-container-exit` passes
- [ ] `docker compose -f docker-compose.test.yml up frontend-tests --abort-on-container-exit` passes (after 1A.1)
- [ ] No new `console.error` or 404s in critical flows
- [ ] Manual smoke: login → dashboard → booking → message → wallet
- [ ] Linting passes (after 1A.3)

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [2026-02-07-ux-ui-audit-report.md](2026-02-07-ux-ui-audit-report.md) | Full 143-issue audit |
| [2026-02-06-critical-integration-fixes.md](2026-02-06-critical-integration-fixes.md) | 45-task integration plan |
| [integration_report.md](../integration_report.md) | 21 API path mismatches |
| [contract_diff.md](../contract_diff.md) | Frontend ↔ Backend mapping |
| [CLEAN_ARCHITECTURE_REFACTORING.md](../todo/CLEAN_ARCHITECTURE_REFACTORING.md) | Phase 0–6 refactor |
| [ux-experience-gap-report.md](../ux-experience-gap-report.md) | Broken flows, missing pages |
| [TODO_PHASE_0_STABILIZATION.md](../TODO_PHASE_0_STABILIZATION.md) | Current phase status |

---

*Generated from deep codebase analysis. Execute with minimum 3 parallel tasks per sprint.*
