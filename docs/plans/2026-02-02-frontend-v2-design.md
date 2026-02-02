# Frontend V2 Design

**Date:** 2026-02-02
**Status:** Approved
**Goal:** Complete frontend rebuild with modern architecture, clean design, and full backend integration

## Summary

Rebuild the EduStream frontend from scratch in a new `frontend-v2/` directory. The new frontend will feature:

- **Visual Design:** Modern SaaS aesthetic (clean, minimal) with friendly touches (rounded corners, warm colors)
- **Component Library:** shadcn/ui with Tailwind CSS
- **State Management:** React Query for server state, Zustand for UI state only
- **Forms:** react-hook-form + Zod validation
- **Architecture:** Domain-split API layer, hooks-based data access, clean separation of concerns

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript (strict mode) |
| Styling | Tailwind CSS + shadcn/ui |
| Server State | TanStack React Query |
| UI State | Zustand |
| Forms | react-hook-form + Zod |
| Icons | Lucide React |
| Charts | Recharts |
| Testing | Vitest + Testing Library + Playwright |

## Project Structure

```
frontend-v2/
├── app/                      # Next.js 15 App Router
│   ├── (auth)/              # Auth pages (login, register, forgot-password)
│   ├── (public)/            # Public pages (landing, tutor discovery)
│   ├── (dashboard)/         # Protected dashboard routes
│   │   ├── student/         # Student-specific pages
│   │   ├── tutor/           # Tutor-specific pages
│   │   ├── admin/           # Admin pages
│   │   └── owner/           # Owner pages
│   ├── layout.tsx           # Root layout with providers
│   └── providers.tsx        # React Query, Zustand, Theme providers
│
├── components/
│   ├── ui/                  # shadcn/ui primitives (button, input, card, etc.)
│   ├── forms/               # Form components with react-hook-form + zod
│   ├── layouts/             # Shell, Sidebar, Navbar, Footer
│   └── features/            # Domain components (booking/, tutor/, messages/)
│
├── lib/
│   ├── api/                 # Domain-split API clients
│   │   ├── client.ts        # Base fetch wrapper
│   │   ├── auth.ts          # Auth endpoints
│   │   ├── tutors.ts        # Tutor endpoints
│   │   ├── bookings.ts      # Booking endpoints
│   │   ├── messages.ts      # Message endpoints
│   │   └── index.ts         # Re-exports
│   ├── hooks/               # React Query hooks per domain
│   │   ├── use-auth.ts
│   │   ├── use-tutors.ts
│   │   ├── use-bookings.ts
│   │   └── use-messages.ts
│   ├── stores/              # Zustand stores (UI state only)
│   │   ├── ui-store.ts      # Sidebar, modals, toasts
│   │   └── filters-store.ts # Search/filter persistence
│   ├── validators/          # Zod schemas
│   └── utils/               # Helpers, formatters
│
├── types/                   # Shared TypeScript types
└── styles/                  # Global styles, Tailwind config
```

## Architecture Principles

### Data Flow Rule

| Data Type | Where it lives |
|-----------|----------------|
| Server data (bookings, tutors, messages) | React Query |
| UI state (modals, sidebar, toasts) | Zustand `ui-store` |
| Persisted preferences (filters, theme) | Zustand with `persist` |
| Form state | react-hook-form (local) |

### API Layer Pattern

1. **API Client** (`lib/api/client.ts`) - Thin fetch wrapper with auth headers
2. **Domain Files** (`lib/api/bookings.ts`) - Endpoint functions per domain
3. **Hooks** (`lib/hooks/use-bookings.ts`) - React Query wrappers with query keys
4. **Components** - Only import from hooks, never directly from API

### Query Key Convention

```typescript
export const bookingKeys = {
  all: ['bookings'] as const,
  lists: () => [...bookingKeys.all, 'list'] as const,
  list: (filters: BookingFilters) => [...bookingKeys.lists(), filters] as const,
  details: () => [...bookingKeys.all, 'detail'] as const,
  detail: (id: number) => [...bookingKeys.details(), id] as const,
};
```

### Mutation Invalidation Rules

| Action | Invalidate |
|--------|------------|
| Create booking | `bookings.lists`, `availability` |
| Cancel booking | `bookings.lists`, `bookings.detail(id)`, `availability` |
| Send message | `messages.thread(id)`, `messages.unreadCount` |
| Update profile | `auth.me`, `tutors.detail(id)` |

## Design System

### Color Palette

- **Primary:** Emerald (warm green - growth, learning)
- **Accent:** Amber (highlights, ratings, warnings)
- **Neutral:** Warm slate

### Visual Characteristics

- Rounded corners (`rounded-xl`, `rounded-2xl`)
- Soft shadows (`shadow-soft`, `shadow-soft-md`)
- Generous whitespace
- Subtle hover transitions
- Dark mode support

### Core UI Components

| Component | Purpose |
|-----------|---------|
| `Button` | Primary, secondary, ghost, outline, danger variants |
| `Input`, `Textarea`, `Select` | Form fields with label and error states |
| `Card` | Content containers with optional hover effect |
| `Modal`, `Sheet` | Overlays and slide-out panels |
| `Avatar` | User images with fallback initials |
| `Badge` | Status indicators |
| `Tabs` | Navigation within pages |
| `Dropdown` | Menus and action lists |
| `Toast` | Notification popups |
| `Skeleton` | Loading placeholders |
| `EmptyState` | Zero-data illustrations |

## Layouts

### Route Groups

```
app/
├── (auth)/         # Centered card layout, no shell
├── (public)/       # Public header + footer
└── (dashboard)/    # AppShell with sidebar + topbar
```

### AppShell Structure

- **Sidebar:** Collapsible, role-based navigation, mobile drawer
- **Topbar:** Theme toggle, notifications, user menu
- **Main:** Content area with consistent padding

### Role-Based Navigation

| Role | Key Nav Items |
|------|---------------|
| Student | Dashboard, Find Tutors, My Bookings, Messages, Packages, Wallet, Saved |
| Tutor | Dashboard, Schedule, Sessions, Messages, Students, Earnings, Analytics |
| Admin | Dashboard, Users, Tutor Approval, Bookings, Reports, Feature Flags |
| Owner | Dashboard, Revenue, Analytics, Admin Panel |

## Page Designs

### Dashboards

All dashboards follow this pattern:
1. Welcome header with quick action buttons
2. Stats row (4 cards with key metrics)
3. Two-column layout (main content + sidebar)
4. Optional chart/graph section

**Student:** Upcoming sessions, wallet balance, recommended tutors
**Tutor:** Pending requests (highlighted), today's schedule, earnings chart
**Admin:** Platform stats, tutor approval queue, activity feed
**Owner:** Revenue metrics, platform analytics

### Public Pages

**Landing:** Hero, how-it-works, featured tutors, stats, CTA
**Tutor Discovery:** Filter sidebar + results grid with pagination
**Tutor Profile:** Profile header, about, reviews + sticky booking sidebar

## Error Handling

### API Errors

```typescript
class ApiError extends Error {
  status: number;
  detail: string;
  code?: string;
}
```

- 401: Redirect to login
- 403: Show forbidden message
- 404: Show not found state
- 422: Display validation errors on form
- 500+: Show generic error with retry button

### React Query Config

- Retry: 2 times for server errors, no retry for client errors
- Stale time: 30 seconds default
- Global error handler for auth failures

### Error Boundaries

Wrap dashboard layout in ErrorBoundary component with fallback UI.

## Loading States

- Use `<Skeleton>` components matching content shape
- Show skeletons immediately (no delay)
- Each list component has a corresponding skeleton variant
- Pattern: `isLoading ? <Skeleton /> : <Content />`

## Testing Strategy

| Layer | Coverage Target | Tools |
|-------|-----------------|-------|
| API hooks | 90% | Vitest + MSW |
| UI components | 80% | Testing Library |
| Forms | 90% | Testing Library + user-event |
| E2E critical paths | 100% | Playwright |

### Test Utilities

- `createTestQueryClient()` - Isolated query client per test
- `renderWithProviders()` - Wrap component with all providers
- MSW handlers for API mocking

## Implementation Approach

**Big bang rebuild** in `frontend-v2/` directory:
1. Build complete new frontend
2. Test thoroughly
3. Swap when ready
4. Remove old `frontend/` directory

## Files to Create

### Foundation (Week 1)
- [ ] Project setup (Next.js, Tailwind, shadcn/ui)
- [ ] `lib/api/client.ts` - Base API client
- [ ] `lib/stores/ui-store.ts` - UI state
- [ ] `app/providers.tsx` - Root providers
- [ ] `components/ui/*` - Core UI components (10-15 components)
- [ ] `components/layouts/*` - AppShell, Sidebar, Topbar

### API & Hooks (Week 1-2)
- [ ] `lib/api/auth.ts`, `tutors.ts`, `bookings.ts`, `messages.ts`, `payments.ts`
- [ ] `lib/hooks/use-auth.ts`, `use-tutors.ts`, `use-bookings.ts`, `use-messages.ts`
- [ ] `lib/validators/*.ts` - Zod schemas for all forms

### Pages (Week 2-3)
- [ ] Auth pages (login, register, forgot-password)
- [ ] Public pages (landing, tutor discovery, tutor profile)
- [ ] Student dashboard + sub-pages
- [ ] Tutor dashboard + sub-pages
- [ ] Admin dashboard + sub-pages
- [ ] Owner dashboard
- [ ] Messages interface
- [ ] Settings pages

### Polish (Week 3-4)
- [ ] Loading skeletons for all lists
- [ ] Error states and empty states
- [ ] Mobile responsiveness testing
- [ ] Dark mode verification
- [ ] E2E test suite

## Success Criteria

1. All existing functionality preserved
2. Consistent visual design across all pages
3. Clean architecture with no direct API calls in components
4. 80%+ test coverage on hooks and components
5. Mobile responsive on all pages
6. Dark mode working throughout
7. Lighthouse performance score > 90
