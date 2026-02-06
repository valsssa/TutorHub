# Frontend Architecture

## 1. Technology Stack

### Core Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 15.x | React framework with SSR |
| React | 18.2 | UI library |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 3.4 | Utility-first styling |
| Axios | 1.12 | HTTP client |
| Framer Motion | 12.x | Animations |

### Decision Rationale

| Choice | Why Selected | Alternatives Considered |
|--------|--------------|------------------------|
| Next.js | SSR for SEO, App Router, industry standard | Remix, Astro |
| TypeScript | Type safety, better DX, error catching | Plain JavaScript |
| Tailwind | Rapid UI development, consistency | CSS Modules, styled-components |
| Axios | Interceptors, retry logic | Fetch API, ky |

## 2. Directory Structure

```
frontend/
+-- app/                          # Next.js App Router
|   +-- (public)/                 # Public route group
|   |   +-- login/page.tsx
|   |   +-- register/page.tsx
|   +-- admin/                    # Admin dashboard
|   +-- owner/                    # Owner analytics
|   +-- dashboard/                # User dashboard
|   +-- bookings/                 # Booking management
|   +-- messages/                 # Messaging
|   +-- tutors/                   # Tutor search & detail
|   +-- tutor/                    # Tutor-specific pages
|   +-- settings/                 # Settings subsections
|   +-- layout.tsx                # Root layout
+-- components/                   # React components (~95 files)
|   +-- admin/                    # Admin components
|   +-- bookings/                 # Booking components
|   +-- dashboards/               # Dashboard components
|   +-- messaging/                # Chat UI
|   +-- modals/                   # Modal dialogs
|   +-- owner/                    # Owner components
|   +-- settings/                 # Settings components
|   +-- *.tsx                     # Shared components
+-- contexts/                     # React Context providers
|   +-- ThemeContext.tsx
|   +-- LocaleContext.tsx
|   +-- TimezoneContext.tsx
+-- hooks/                        # Custom React hooks
|   +-- useAuth.ts
|   +-- useApi.ts
|   +-- useWebSocket.ts
|   +-- useMessaging.ts
+-- lib/                          # Utilities
|   +-- api.ts                    # API client (1542 lines)
|   +-- auth.ts
|   +-- timezone.ts
|   +-- locale.ts
+-- types/                        # TypeScript definitions
|   +-- index.ts
|   +-- booking.ts
|   +-- api.ts
|   +-- owner.ts
+-- middleware.ts                 # Next.js middleware (CSP, security)
```

## 3. Routing Architecture

### Route Groups

```
Public Routes (unauthenticated)
  /login, /register
  /, /become-a-tutor, /affiliate-program
  /privacy, /terms, /cookie-policy
  /help-center, /support

Protected Routes (any authenticated user)
  /dashboard        # Role-aware dashboard
  /profile          # User profile
  /settings/*       # Settings pages
  /messages         # Messaging

Student Routes
  /tutors           # Tutor search
  /tutors/[id]      # Tutor detail
  /tutors/[id]/book # Booking wizard
  /bookings         # Booking history
  /bookings/[id]/review
  /saved-tutors     # Favorites
  /packages         # Purchased packages
  /wallet           # Wallet/credits

Tutor Routes
  /tutor/profile    # Profile editor
  /tutor/onboarding # Signup flow
  /tutor/schedule   # Schedule management
  /tutor/earnings   # Earnings dashboard
  /tutor/students   # Student list

Admin Routes
  /admin            # Admin panel

Owner Routes
  /owner            # Owner analytics
```

### Protected Route Pattern

```typescript
// components/ProtectedRoute.tsx
export function ProtectedRoute({
  children,
  requiredRole,
}: {
  children: React.ReactNode;
  requiredRole?: string;
}) {
  const { user, loading, isAdmin, isTutor, isStudent, isOwner } = useAuth();

  if (loading) return <LoadingSpinner />;

  if (!user) {
    redirect('/login');
    return null;
  }

  if (requiredRole && user.role !== requiredRole) {
    redirect('/unauthorized');
    return null;
  }

  return <>{children}</>;
}
```

## 4. State Management

### Strategy: React Context + Hooks

No Redux or Zustand - the application state is simple enough for Context:

```typescript
// Root layout wraps app with providers
<ThemeProvider>
  <LocaleProvider>
    <TimezoneProvider>
      <ToastProvider>
        {children}
      </ToastProvider>
    </TimezoneProvider>
  </LocaleProvider>
</ThemeProvider>
```

### State Categories

| Category | Storage | Persistence | Example |
|----------|---------|-------------|---------|
| Auth State | useAuth hook | Cookies | User, roles |
| UI State | React Context | localStorage | Theme, timezone |
| Server State | API cache | Memory (LRU) | Tutor lists |
| Form State | useState | None | Form inputs |
| Real-time | useWebSocket | None | Messages |

### Context Implementations

```typescript
// contexts/ThemeContext.tsx
interface ThemeContextType {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

// contexts/LocaleContext.tsx
interface LocaleContextType {
  locale: string;
  currency: string;
  setLocale: (locale: string) => void;
  setCurrency: (currency: string) => void;
  formatPrice: (amount: number) => string;
}

// contexts/TimezoneContext.tsx
interface TimezoneContextType {
  userTimezone: string;
  setUserTimezone: (tz: string) => void;
}
```

## 5. API Client

### Architecture

**File**: `lib/api.ts` (1542 lines, 40+ endpoints)

```typescript
// Features
- In-memory LRU cache (100 max, 2min TTL)
- Rate limit tracking with localStorage sync
- Exponential backoff retry (max 3, 1s/2s/4s)
- Auto cache invalidation on mutations
- Token expiry checking
- Decimal field parsing

// Structure
const api = {
  auth: { register, login, getCurrentUser, ... },
  tutors: { list, get, getMyProfile, updateAbout, ... },
  bookings: { list, get, create, cancel, confirm, ... },
  messages: { send, listThreads, markRead, ... },
  notifications: { list, markAsRead, ... },
  admin: { listUsers, approveTutor, ... },
  owner: { getDashboard, getRevenue, ... },
  // ... more namespaces
};
```

### Request Interceptors

```typescript
// Add auth token
axios.interceptors.request.use((config) => {
  const token = Cookies.get('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Check token expiry before request
const tokenExpiry = localStorage.getItem('token_expiry');
if (tokenExpiry && Date.now() > parseInt(tokenExpiry)) {
  clearAuth();
  redirect('/login?expired=true');
}
```

### Response Handling

```typescript
// Handle rate limits
if (response.status === 429) {
  showRateLimitWarning();
  localStorage.setItem('rate_limited', 'true');
}

// Parse rate limit headers
const remaining = response.headers['x-ratelimit-remaining'];
const limit = response.headers['x-ratelimit-limit'];

// Retry logic
const retry = async (fn, retries = 3, delay = 1000) => {
  try {
    return await fn();
  } catch (error) {
    if (retries > 0 && shouldRetry(error)) {
      await sleep(delay);
      return retry(fn, retries - 1, delay * 2);
    }
    throw error;
  }
};
```

### Cache Strategy

```typescript
const cache = new Map<string, CacheEntry>();

interface CacheEntry {
  data: unknown;
  timestamp: number;
  ttl: number;
}

// TTL by endpoint type
const TTL_CONFIG = {
  subjects: 10 * 60 * 1000,    // 10 minutes (static)
  tutors: 60 * 1000,           // 1 minute
  bookings: 30 * 1000,         // 30 seconds
  currentUser: 10 * 60 * 1000, // 10 minutes
  default: 2 * 60 * 1000,      // 2 minutes
};

// Auto-invalidation on mutations
const invalidatePatterns = {
  bookings: ['bookings', 'tutor/bookings'],
  tutors: ['tutors', 'tutor/profile'],
  users: ['users', 'profile'],
};
```

## 6. Custom Hooks

### useAuth

```typescript
interface UseAuthReturn {
  user: User | null;
  loading: boolean;
  error: string | null;
  logout: () => void;
  refetch: () => Promise<void>;
  isAdmin: boolean;
  isTutor: boolean;
  isStudent: boolean;
  isOwner: boolean;
}

function useAuth(options?: {
  requiredRole?: string;
  redirectTo?: string;
}): UseAuthReturn;
```

### useApi

```typescript
interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  execute: (...args: any[]) => Promise<T | null>;
  reset: () => void;
}

function useApi<T>(apiFunction: (...args: any[]) => Promise<T>): UseApiReturn<T>;

// Usage
const { data, loading, execute } = useApi(api.tutors.list);
useEffect(() => { execute({ page: 1 }); }, []);
```

### useWebSocket

```typescript
interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (data: any) => void;
  sendTyping: (recipientId: number) => void;
  sendMessageDelivered: (messageId: number, senderId: number) => void;
  sendMessageRead: (messageId: number, senderId: number) => void;
  checkPresence: (userIds: number[]) => void;
}

function useWebSocket(): UseWebSocketReturn;
```

### useMessaging

```typescript
interface UseMessagingReturn {
  messages: Message[];
  setMessages: (updater: (prev: Message[]) => Message[]) => void;
  clearMessages: () => void;
  typingUsers: Set<number>;
  isConnected: boolean;
  handleTyping: () => void;
}

function useMessaging(props: {
  recipientId: number;
  bookingId?: number;
}): UseMessagingReturn;
```

## 7. Component Patterns

### Component Organization

```typescript
// Feature component with local state
export function BookingCard({ booking }: { booking: BookingDTO }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const { formatPrice } = useLocale();

  return (
    <div className="rounded-lg border p-4">
      {/* Component content */}
    </div>
  );
}

// Page component with data fetching
export default function BookingsPage() {
  const { data: bookings, loading } = useApi(api.bookings.list);

  if (loading) return <SkeletonLoader />;

  return (
    <div className="space-y-4">
      {bookings?.map((booking) => (
        <BookingCard key={booking.id} booking={booking} />
      ))}
    </div>
  );
}
```

### Reusable UI Components

```
Button.tsx       - Primary action button
Input.tsx        - Form input with validation
TextArea.tsx     - Multi-line input
Select.tsx       - Dropdown select
Modal.tsx        - Dialog modal
Toast.tsx        - Toast notifications
Avatar.tsx       - User avatar display
Badge.tsx        - Status badges
Pagination.tsx   - Page navigation
LoadingSpinner   - Loading indicator
SkeletonLoader   - Content placeholder
```

## 8. Real-Time Features

### WebSocket Connection

```typescript
// lib/websocket.ts
class WebSocketClient {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnects = 5;

  connect(userId: number) {
    this.socket = new WebSocket(`${WS_URL}/ws/${userId}`);

    this.socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.socket.onclose = () => {
      this.reconnect();
    };
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnects) {
      setTimeout(() => {
        this.reconnectAttempts++;
        this.connect(this.userId);
      }, Math.pow(2, this.reconnectAttempts) * 1000);
    }
  }
}
```

### Message Types

```typescript
type WebSocketMessage =
  | { type: 'new_message'; data: Message }
  | { type: 'typing'; data: { user_id: number } }
  | { type: 'message_delivered'; data: { message_id: number } }
  | { type: 'message_read'; data: { message_id: number } }
  | { type: 'presence'; data: { user_id: number; online: boolean } }
  | { type: 'availability_updated'; data: { tutor_id: number } };
```

## 9. Security

### CSP Headers (middleware.ts)

```typescript
const cspDirectives = {
  'default-src': ["'self'"],
  'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
  'style-src': ["'self'", "'unsafe-inline'"],
  'img-src': ["'self'", 'data:', 'blob:', '*.amazonaws.com'],
  'connect-src': ["'self'", API_URL, WS_URL],
  'frame-src': ['youtube.com', 'vimeo.com', 'zoom.us'],
};
```

### Cookie Security

```typescript
// Secure cookie settings
Cookies.set('token', token, {
  secure: true,           // HTTPS only
  sameSite: 'strict',     // CSRF protection
  expires: 1/48,          // 30 minutes
});
```

## 10. Performance

### Bundle Optimization

```javascript
// next.config.js
module.exports = {
  experimental: {
    optimizePackageImports: ['lucide-react', 'date-fns'],
  },
};
```

### Code Splitting

```typescript
// Dynamic imports for heavy components
const AdminDashboard = dynamic(() => import('@/components/admin/AdminDashboard'), {
  loading: () => <SkeletonLoader />,
});
```

### Image Optimization

```typescript
// Using Next.js Image component
import Image from 'next/image';

<Image
  src={avatarUrl}
  alt="User avatar"
  width={100}
  height={100}
  placeholder="blur"
  blurDataURL={placeholderBase64}
/>
```
