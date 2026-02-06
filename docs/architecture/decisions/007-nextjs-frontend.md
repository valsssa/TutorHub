# ADR-007: Next.js for Frontend

## Status

Accepted

## Date

2026-01-29

## Context

EduStream requires a modern web frontend that:
- Provides responsive UI for students and tutors
- Supports role-based access control (student, tutor, admin, owner)
- Delivers fast initial page loads for SEO and user experience
- Integrates with FastAPI backend via REST APIs
- Supports real-time features (notifications, messaging)
- Can be developed efficiently by a small team

Key forces at play:
- **Developer experience**: TypeScript support and strong tooling
- **Performance**: Fast page loads critical for user retention
- **SEO**: Public tutor profiles need search engine visibility
- **Team skills**: Team familiar with React ecosystem
- **Time to market**: MVP requires rapid development

## Decision

We will use **Next.js 14** (later upgraded to 14.2.x) with the App Router for the frontend.

Key configuration choices:
- **App Router** over Pages Router for colocation and layouts
- **Client-side rendering** primary strategy (API routes on backend)
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **React 18** with Suspense boundaries

Architecture patterns:
```
frontend/
├── app/                    # App Router pages and layouts
│   ├── (auth)/            # Auth pages (login, register)
│   ├── admin/             # Admin dashboard
│   ├── owner/             # Owner dashboard
│   ├── tutor/             # Tutor-specific pages
│   ├── tutors/            # Public tutor discovery
│   ├── bookings/          # Booking management
│   ├── messages/          # Messaging
│   └── settings/          # User settings
├── components/            # Reusable React components
├── lib/                   # Utilities, API client, auth helpers
└── types/                 # TypeScript definitions
```

Server components strategy:
- Layout components as Server Components for shared UI
- Page components fetch data on server when beneficial for SEO
- Interactive features use Client Components with `'use client'`
- API calls primarily client-side via axios for consistency

## Consequences

### Positive

- **Fast development**: File-based routing, built-in optimizations
- **Type safety**: End-to-end TypeScript with API type sharing
- **Performance**: Automatic code splitting, image optimization
- **SEO capable**: Server rendering for public pages when needed
- **Strong ecosystem**: Rich library support, active community
- **Developer experience**: Fast refresh, excellent error messages

### Negative

- **Learning curve**: App Router paradigm different from Pages Router
- **Bundle size**: Full React framework larger than lightweight alternatives
- **Complexity**: Server/Client Component boundary requires thought
- **Version churn**: Next.js updates frequently with breaking changes

### Neutral

- Vercel deployment optimized but not required
- API routes available but unused (backend handles all API)
- React Server Components partially adopted

## Alternatives Considered

### Option A: Pages Router (Next.js)

Traditional Next.js routing with `pages/` directory.

**Pros:**
- More documentation and examples available
- Simpler mental model
- Team may have prior experience

**Cons:**
- No layouts without workarounds
- Less flexible data fetching
- Being phased out in favor of App Router

**Why not chosen:** App Router is the future direction; better to adopt now.

### Option B: Create React App (CRA)

Pure client-side React application.

**Pros:**
- Simpler architecture
- No SSR complexity
- Full control over build config

**Cons:**
- No built-in SSR/SSG
- Slower initial page loads
- Manual code splitting setup
- CRA maintenance uncertain

**Why not chosen:** SEO requirements and performance needs favor Next.js.

### Option C: Vite + React

Modern build tool with React.

**Pros:**
- Extremely fast development builds
- Simpler than Next.js
- Flexible configuration

**Cons:**
- No built-in SSR (requires additional setup)
- Less opinionated (more decisions to make)
- Smaller ecosystem than Next.js

**Why not chosen:** Lack of built-in SSR; would require additional framework (Remix, etc.).

### Option D: Remix

Full-stack React framework with nested routing.

**Pros:**
- Excellent data loading patterns
- Progressive enhancement
- Good forms handling

**Cons:**
- Smaller community than Next.js
- Less familiar to team
- Different deployment model

**Why not chosen:** Next.js has larger ecosystem and team familiarity.

### Option E: Vue.js / Nuxt

Vue-based frontend framework.

**Pros:**
- Simpler learning curve
- Good documentation
- Strong TypeScript support

**Cons:**
- Team unfamiliar with Vue
- Smaller ecosystem than React
- Fewer component libraries

**Why not chosen:** Team expertise in React; larger React ecosystem.

## App Router vs Pages Router Decision

The App Router was chosen over Pages Router for:

1. **Layouts**: Shared layouts without prop drilling or context
2. **Colocation**: Components, tests, and styles near routes
3. **Loading states**: Built-in loading.tsx and error.tsx
4. **Future-proof**: Official direction for Next.js development
5. **Server Components**: Potential for reduced JavaScript shipped

Trade-offs accepted:
- Steeper learning curve for new patterns
- Some community resources still reference Pages Router
- Occasional hydration mismatches requiring `'use client'`

## Server Components Strategy

Our approach to Server vs Client Components:

**Server Components (default)**:
- Layout shells and navigation
- Static content rendering
- SEO-critical pages (tutor profiles)

**Client Components (`'use client'`)**:
- Interactive forms
- Real-time features (notifications, messages)
- State-dependent UI (auth-gated content)
- Third-party libraries requiring browser APIs

**Data Fetching**:
- Client-side fetching via axios for most API calls
- Server-side fetching for SEO pages (tutor discovery)
- React Query considered for caching (future enhancement)

## References

- Frontend structure: `frontend/app/`
- Configuration: `frontend/next.config.js`
- Type definitions: `frontend/types/`
- Next.js documentation: https://nextjs.org/docs
- React documentation: https://react.dev/
