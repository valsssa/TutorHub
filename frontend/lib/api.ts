/**
 * API client and utilities
 */
import axios, { AxiosError } from "axios";
import Cookies from "js-cookie";
import { createLogger } from "./logger";
import { getApiBaseUrl } from "@/shared/utils/url";
import type {
  User,
  TutorProfile,
  TutorPublicSummary,
  Subject,
  Booking,
  Review,
  Message,
  MessageThread,
  TutorCertification,
  TutorEducation,
  TutorPricingOption,
  TutorSubject,
  TutorAvailability,
  StudentProfile,
  StudentPackage,
  AvatarApiResponse,
  AvatarSignedUrl,
  FavoriteTutor,
  PaginatedResponse,
} from "@/types";
import type {
  DashboardStats,
  TutorListParams,
  MessageSendResponse,
  UnreadCountResponse,
} from "@/types/api";
import type {
  OwnerDashboard,
  RevenueMetrics,
  GrowthMetrics,
  MarketplaceHealth,
  CommissionTierBreakdown,
} from "@/types/owner";

const logger = createLogger('API');

// API Error Response Interface
export interface ApiErrorResponse {
  detail: string;
  [key: string]: unknown;
}

// Rate Limit Info Interface
export interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset: number; // Unix timestamp
  retryAfter?: number; // Seconds to wait
}

declare module "axios" {
  export interface AxiosRequestConfig {
    suppressErrorLog?: boolean;
  }
}

type RedirectingWindow = Window & { __redirecting?: boolean };

// Rate limit state
let rateLimitWarningShown = false;
let lastRateLimitReset = 0;

// Production API URL
const API_URL = getApiBaseUrl(process.env.NEXT_PUBLIC_API_URL);

logger.info(`API client initialized with base URL: ${API_URL}`);

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  timeout: 15000, // Reduced from 30s to 15s for faster failures
  headers: {
    "Content-Type": "application/json",
  },
});

// Helper function to parse rate limit headers
function parseRateLimitHeaders(headers: Record<string, unknown>): RateLimitInfo | null {
  const limit = (headers['x-ratelimit-limit'] || headers['ratelimit-limit']) as string | undefined;
  const remaining = (headers['x-ratelimit-remaining'] || headers['ratelimit-remaining']) as string | undefined;
  const reset = (headers['x-ratelimit-reset'] || headers['ratelimit-reset']) as string | undefined;
  const retryAfter = headers['retry-after'] as string | undefined;

  if (!limit && !remaining && !reset) {
    return null; // No rate limit headers present
  }

  return {
    limit: limit ? parseInt(limit, 10) : 0,
    remaining: remaining ? parseInt(remaining, 10) : 0,
    reset: reset ? parseInt(reset, 10) : 0,
    retryAfter: retryAfter ? parseInt(retryAfter, 10) : undefined,
  };
}

// Helper function to show rate limit warning
function showRateLimitWarning(rateLimitInfo: RateLimitInfo | null, status: number) {
  // Prevent showing duplicate warnings in quick succession
  const now = Date.now();
  if (rateLimitWarningShown && now - lastRateLimitReset < 5000) {
    return;
  }

  rateLimitWarningShown = true;
  lastRateLimitReset = now;

  // Reset warning flag after 5 seconds
  setTimeout(() => {
    rateLimitWarningShown = false;
  }, 5000);

  if (status === 429) {
    // Rate limit exceeded
    const retryAfter = rateLimitInfo?.retryAfter || 60;
    const minutes = Math.ceil(retryAfter / 60);

    const message = minutes > 1
      ? `⏱️ Rate limit reached. Please wait ${minutes} minutes before trying again.`
      : `⏱️ Rate limit reached. Please wait ${retryAfter} seconds before trying again.`;

    logger.warn(`Rate limit exceeded. Retry after: ${retryAfter}s`);

    // Show browser notification if available
    if (typeof window !== 'undefined' && 'Notification' in window) {
      if (Notification.permission === 'granted') {
        new Notification('Rate Limit Reached', {
          body: message,
          icon: '/favicon.ico',
        });
      }
    }

    // Also log for visibility
    logger.warn(`🚫 ${message}`);

    // Store in localStorage so components can display it
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('rateLimitWarning', JSON.stringify({
        message,
        timestamp: now,
        retryAfter,
      }));

      // Dispatch custom event so components can react
      window.dispatchEvent(new CustomEvent('rateLimit', {
        detail: { message, retryAfter, rateLimitInfo }
      }));
    }
  }
}

// Add retry logic with exponential backoff
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

api.interceptors.response.use(
  (response) => {
    // Parse and log rate limit headers on successful responses
    if (response.headers) {
      const rateLimitInfo = parseRateLimitHeaders(response.headers);
      if (rateLimitInfo && rateLimitInfo.remaining < 10) {
        logger.warn(`Rate limit warning: ${rateLimitInfo.remaining}/${rateLimitInfo.limit} requests remaining`);
      }
    }
    return response;
  },
  async (error) => {
    const config = error.config;

    // Handle authentication errors (401)
    if (error.response?.status === 401) {
      logger.warn("Received 401 Unauthorized, clearing auth data");
      clearAuthData();

      // Redirect to login if we're in browser
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login?expired=true';
      }

      return Promise.reject(error);
    }

    // Handle rate limit errors (429)
    if (error.response?.status === 429) {
      const rateLimitInfo = parseRateLimitHeaders(error.response.headers || {});
      showRateLimitWarning(rateLimitInfo, 429);

      // Enhance error with user-friendly message
      const retryAfter = rateLimitInfo?.retryAfter || 60;
      error.userMessage = `You've made too many requests. Please wait ${Math.ceil(retryAfter / 60)} minute(s) before trying again.`;

      return Promise.reject(error);
    }

    // Don't retry if no config or already retried max times
    if (!config || config.__retryCount >= MAX_RETRIES) {
      return Promise.reject(error);
    }

    // Only retry on network errors or 5xx server errors (not 429)
    const shouldRetry =
      !error.response || // Network error
      (error.response.status >= 500 && error.response.status < 600); // Server error

    if (!shouldRetry) {
      return Promise.reject(error);
    }

    config.__retryCount = config.__retryCount || 0;
    config.__retryCount += 1;

    // Exponential backoff: 1s, 2s, 4s
    const delay = RETRY_DELAY * Math.pow(2, config.__retryCount - 1);

    logger.warn(`Retrying request (${config.__retryCount}/${MAX_RETRIES}) after ${delay}ms: ${config.url}`);

    await new Promise(resolve => setTimeout(resolve, delay));

    return api(config);
  }
);

// Optimized in-memory cache with LRU eviction
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  accessCount: number;
  lastAccessed: number;
}

const cache = new Map<string, CacheEntry<unknown>>();
const DEFAULT_CACHE_TTL = 2 * 60 * 1000; // 2 minutes (reduced for fresher data)
const MAX_CACHE_SIZE = 100; // Reduced to prevent memory bloat

function getCacheKey(url: string, params?: unknown): string {
  return `${url}:${JSON.stringify(params || {})}`;
}

function getFromCache<T>(key: string, ttl: number = DEFAULT_CACHE_TTL): T | null {
  const cached = cache.get(key);
  if (!cached) return null;
  
  const age = Date.now() - cached.timestamp;
  if (age > ttl) {
    cache.delete(key);
    return null;
  }
  
  // Update access stats for LRU
  cached.accessCount++;
  cached.lastAccessed = Date.now();
  return cached.data as T;
}

function setCache(key: string, data: unknown): void {
  // LRU eviction before adding new entry
  if (cache.size >= MAX_CACHE_SIZE) {
    const now = Date.now();
    const entries = Array.from(cache.entries());

    // Remove stale entries first (older than 10 minutes)
    const staleEntries = entries.filter(([, v]) => now - v.timestamp > 10 * 60 * 1000);
    staleEntries.forEach(([k]) => cache.delete(k));

    // If still at limit, remove least recently used
    if (cache.size >= MAX_CACHE_SIZE) {
      // Clone array before sorting to avoid mutating the original
      const sortedByLRU = [...entries].sort((a, b) => a[1].lastAccessed - b[1].lastAccessed);
      // Remove oldest 30%
      const toRemove = Math.ceil(MAX_CACHE_SIZE * 0.3);
      sortedByLRU.slice(0, toRemove).forEach(([k]) => cache.delete(k));
    }
  }

  cache.set(key, {
    data,
    timestamp: Date.now(),
    accessCount: 1,
    lastAccessed: Date.now(),
  });
}

export function clearCache(pattern?: string): void {
  if (pattern) {
    // Clear specific pattern
    const keys = Array.from(cache.keys());
    keys.forEach(key => {
      if (key.includes(pattern)) {
        cache.delete(key);
      }
    });
    logger.info(`Cache cleared for pattern: ${pattern}`);
  } else {
    cache.clear();
    logger.info("Cache cleared");
  }
}

// Helper to check if token is expired
function isTokenExpired(): boolean {
  const tokenExpiry = Cookies.get("token_expiry");
  if (!tokenExpiry) return false;

  const expiryTime = parseInt(tokenExpiry, 10);
  const currentTime = Date.now();

  // Token expired if current time is past expiry
  return currentTime >= expiryTime;
}

// Helper to clear auth data
function clearAuthData() {
  Cookies.remove("token");
  Cookies.remove("token_expiry");
  clearCache(); // Clear all cached data
}

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = Cookies.get("token");

  // Check if token is expired before making request
  if (token && isTokenExpired()) {
    logger.warn("Token expired, clearing auth data");
    clearAuthData();

    // Redirect to login if we're in browser
    if (typeof window !== 'undefined') {
      window.location.href = '/login?expired=true';
    }

    return Promise.reject(new Error('Token expired'));
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    logger.debug(`Request to ${config.url} with auth token`);
  } else {
    logger.debug(`Request to ${config.url} without auth token`);
  }
  return config;
});

// Automatic cache invalidation after mutations
// This replaces 30+ manual clearCache() calls throughout the codebase
api.interceptors.response.use(
  (response) => {
    const method = response.config.method?.toUpperCase();
    const isMutation = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method || '');

    if (isMutation && response.status >= 200 && response.status < 300) {
      // Extract resource type from URL for pattern-based invalidation
      const url = response.config.url || '';

      // Pattern-based invalidation for common resources
      if (url.includes('/users') || url.includes('/profile') || url.includes('/avatar')) {
        clearCache('users');
        clearCache('profile');
      }
      if (url.includes('/tutors') || url.includes('/tutor-profile')) {
        clearCache('tutors');
        clearCache('tutor-profile');
      }
      if (url.includes('/bookings')) {
        clearCache('bookings');
      }
      if (url.includes('/reviews')) {
        clearCache('reviews');
      }
      if (url.includes('/messages')) {
        clearCache('messages');
      }
      if (url.includes('/notifications')) {
        clearCache('notifications');
      }
      if (url.includes('/packages')) {
        clearCache('packages');
      }
      if (url.includes('/favorites')) {
        clearCache('favorites');
      }
      if (url.includes('/admin')) {
        // Admin operations may affect many resources
      }

      logger.debug(`Auto-invalidated cache after ${method} ${url}`);
    }

    return response;
  },
  (error) => {
    // Error handling is done by the existing error interceptor below
    return Promise.reject(error);
  }
);

// Handle errors consistently and parse decimal fields
api.interceptors.response.use(
  (response) => {
    logger.debug(`Response from ${response.config.url}: ${response.status}`);
    if (response.data) {
      parseDecimalFields(response.data);
    }
    return response;
  },
  (error: AxiosError) => {
    const status = error.response?.status;
    const shouldSuppress =
      status === 404 && error.config?.suppressErrorLog;
    const errorMessage = (error.response?.data as ApiErrorResponse)?.detail || error.message;
    if (!shouldSuppress) {
      logger.error(`API Error: ${error.config?.url} - ${status || 'Network Error'}`, { detail: errorMessage });
    }

    if (status === 401) {
      logger.warn("Unauthorized access, redirecting to login");
      Cookies.remove("token");
      if (
        typeof window !== "undefined" &&
        window.location.pathname !== "/login" &&
        window.location.pathname !== "/register"
      ) {
        // Prevent multiple simultaneous redirects
        const redirectingWindow = window as RedirectingWindow;
        if (!redirectingWindow.__redirecting) {
          redirectingWindow.__redirecting = true;
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  },
);

function parseDecimalFields(obj: unknown): void {
  if (Array.isArray(obj)) {
    obj.forEach(parseDecimalFields);
  } else if (obj && typeof obj === "object") {
    const objRecord = obj as Record<string, unknown>;
    for (const [key, value] of Object.entries(objRecord)) {
      if (
        ["hourly_rate", "total_amount", "price", "average_rating"].includes(key)
      ) {
        objRecord[key] = typeof value === "string" ? parseFloat(value) : value;
      } else if (typeof value === "object") {
        parseDecimalFields(value);
      }
    }
  }
}

function normalizeUser(user: User): User {
  const avatarUrl = user.avatar_url ?? user.avatarUrl ?? null;
  const firstName = user.first_name ?? user.firstName ?? null;
  const lastName = user.last_name ?? user.lastName ?? null;
  const preferredLanguage = user.preferred_language ?? user.preferredLanguage ?? null;

  return {
    ...user,
    avatarUrl,
    firstName,
    lastName,
    preferredLanguage,
  };
}

function transformAvatarResponse(data: AvatarApiResponse): AvatarSignedUrl {
  return {
    avatarUrl: data.avatar_url,
    expiresAt: data.expires_at,
  };
}

type CertificationPayload = Omit<TutorCertification, "id">;
type EducationPayload = Omit<TutorEducation, "id">;
type PricingOptionPayload = Omit<TutorPricingOption, "id">;
type SubjectPayload = Omit<TutorSubject, "id" | "subject_name">;
type AvailabilityPayload = Omit<TutorAvailability, "id" | "timezone">;

// ============================================================================
// Authentication
// ============================================================================

export const auth = {
  async register(
    email: string,
    password: string,
    first_name: string,
    last_name: string,
    role: string = "student",
    timezone?: string,
    currency?: string,
  ): Promise<User> {
    logger.info(`Registering user: ${email}, role: ${role}, tz: ${timezone}, cur: ${currency}`);
    try {
      const { data } = await api.post<User>("/api/v1/auth/register", {
        email,
        password,
        first_name,
        last_name,
        role,
        timezone: timezone || "UTC",
        currency: currency || "USD",
      });
      logger.info(`User registered successfully: ${data.email}`);
      return normalizeUser(data);
    } catch (error) {
      logger.error(`Registration failed for ${email}`, error);
      throw error;
    }
  },

  async login(email: string, password: string): Promise<string> {
    logger.info(`Login attempt for: ${email}`);
    try {
      // Use URLSearchParams for proper form encoding (faster than FormData)
      const params = new URLSearchParams();
      params.append("username", email);
      params.append("password", password);

      const { data } = await api.post<{ access_token: string }>(
        "/api/v1/auth/login",
        params.toString(),
        {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        },
      );

      // Token expires in 30 minutes (backend default)
      const expiryTime = Date.now() + (30 * 60 * 1000); // 30 minutes from now

      Cookies.set("token", data.access_token, {
        expires: 7,
        secure: true,
        sameSite: 'strict'
      });

      Cookies.set("token_expiry", expiryTime.toString(), {
        expires: 7,
        secure: true,
        sameSite: 'strict'
      });

      // Clear cache on login to ensure fresh data
      clearCache();

      logger.info(`Login successful for: ${email}, token expires at ${new Date(expiryTime).toISOString()}`);
      return data.access_token;
    } catch (error) {
      logger.error(`Login failed for ${email}`, error);
      throw error;
    }
  },

  async getCurrentUser(): Promise<User> {
    logger.debug("Fetching current user");
    try {
      const { data } = await api.get<User>("/api/v1/auth/me");
      logger.debug(`Current user fetched: ${data.email}, role: ${data.role}`);
      return normalizeUser(data);
    } catch (error) {
      logger.error("Failed to fetch current user", error);
      throw error;
    }
  },

  logout() {
    logger.info("User logging out");
    Cookies.remove("token");
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  },

  async updatePreferences(currency: string, timezone: string): Promise<User> {
    logger.info(`Updating preferences: currency=${currency}, timezone=${timezone}`);
    try {
      let latest: User | null = null;

      if (currency) {
        const { data } = await api.patch<User>("/api/v1/users/currency", { currency });
        latest = data;
      }

      if (timezone) {
        const { data } = await api.patch<User>("/api/v1/users/preferences", { timezone });
        latest = data;
      }

      if (!latest) {
        const { data } = await api.get<User>("/api/v1/auth/me");
        return normalizeUser(data);
      }

      logger.info("Preferences updated successfully");
      return normalizeUser(latest);
    } catch (error) {
      logger.error("Failed to update preferences", error);
      throw error;
    }
  },

  async updateUser(updates: {
    first_name?: string;
    last_name?: string;
    timezone?: string;
    currency?: string;
  }): Promise<User> {
    logger.info(`Updating user: ${Object.keys(updates).join(", ")}`);
    try {
      const { data } = await api.put<User>("/api/v1/auth/me", updates);
      logger.info(`User updated successfully`);
      return normalizeUser(data);
    } catch (error) {
      logger.error("Failed to update user", error);
      throw error;
    }
  },
};

// ============================================================================
// Subjects
// ============================================================================

export const subjects = {
  async list(): Promise<Subject[]> {
    const cacheKey = getCacheKey("/api/v1/subjects");
    const cached = getFromCache<Subject[]>(cacheKey, 10 * 60 * 1000); // Cache subjects for 10 minutes
    if (cached) {
      logger.debug("Subjects loaded from cache");
      return cached;
    }

    logger.debug("Fetching subjects from API");
    const { data } = await api.get<Subject[]>("/api/v1/subjects");
    setCache(cacheKey, data);
    return data;
  },
};

// ============================================================================
// Tutors
// ============================================================================

export const tutors = {
  async list(filters?: {
    subject_id?: number;
    min_rate?: number;
    max_rate?: number;
    min_rating?: number;
    min_experience?: number;
    search_query?: string;
    sort_by?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<TutorPublicSummary>> {
    // Cache tutors list for 1 minute (less than subjects since it changes more often)
    const cacheKey = getCacheKey("/api/v1/tutors", filters);
    const cached = getFromCache<PaginatedResponse<TutorPublicSummary>>(cacheKey, 60 * 1000);
    if (cached && !filters?.search_query) {
      logger.debug("Tutors loaded from cache");
      return cached;
    }

    logger.debug("Fetching tutors from API", { filters });
    const { data } = await api.get<PaginatedResponse<TutorPublicSummary>>("/api/v1/tutors", {
      params: { page: filters?.page || 1, page_size: filters?.page_size || 20, ...filters },
    });

    // Only cache non-search results
    if (!filters?.search_query && data.items.length > 0) {
      setCache(cacheKey, data);
    }

    return data;
  },

  async get(tutorId: number): Promise<TutorProfile> {
    const { data } = await api.get<TutorProfile>(`/api/tutors/${tutorId}`);
    return data;
  },

  async getPublic(tutorId: number): Promise<TutorPublicSummary> {
    const { data } = await api.get<TutorPublicSummary>(`/api/tutors/${tutorId}/public`);
    return data;
  },

  async getMyProfile(): Promise<TutorProfile> {
    const { data } = await api.get<TutorProfile>("/api/v1/tutors/me/profile");
    return data;
  },

  async updateAbout(payload: {
    title: string;
    headline?: string;
    bio?: string;
    experience_years: number;
    languages?: string[];
  }): Promise<TutorProfile> {
    const { data } = await api.patch<TutorProfile>(
      "/api/v1/tutors/me/about",
      payload,
    );
    return data;
  },

  async replaceSubjects(
    subjectsPayload: SubjectPayload[],
  ): Promise<TutorProfile> {
    const { data } = await api.put<TutorProfile>(
      "/api/v1/tutors/me/subjects",
      subjectsPayload,
    );
    return data;
  },

  async replaceCertifications(payload: {
    certifications: CertificationPayload[];
    files?: Record<number, File>;
  }): Promise<TutorProfile> {
    const formData = new FormData();
    formData.append("certifications", JSON.stringify(payload.certifications));

    if (payload.files) {
      Object.entries(payload.files).forEach(([index, file]) => {
        formData.append(`file_${index}`, file);
      });
    }

    const { data } = await api.put<TutorProfile>(
      "/api/v1/tutors/me/certifications",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
    return data;
  },

  async replaceEducation(payload: {
    education: EducationPayload[];
    files?: Record<number, File>;
  }): Promise<TutorProfile> {
    const formData = new FormData();
    formData.append("education", JSON.stringify(payload.education));

    if (payload.files) {
      Object.entries(payload.files).forEach(([index, file]) => {
        formData.append(`file_${index}`, file);
      });
    }

    const { data } = await api.put<TutorProfile>(
      "/api/v1/tutors/me/education",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
    return data;
  },

  async updateDescription(payload: {
    description: string;
  }): Promise<TutorProfile> {
    const { data } = await api.patch<TutorProfile>(
      "/api/v1/tutors/me/description",
      payload,
    );
    return data;
  },

  async updateVideo(payload: { video_url: string }): Promise<TutorProfile> {
    const { data } = await api.patch<TutorProfile>(
      "/api/v1/tutors/me/video",
      payload,
    );
    return data;
  },

  async updatePricing(payload: {
    hourly_rate: number;
    pricing_options: PricingOptionPayload[];
    version: number;
  }): Promise<TutorProfile> {
    const { data } = await api.patch<TutorProfile>(
      "/api/v1/tutors/me/pricing",
      payload,
    );
    return data;
  },

  async replaceAvailability(payload: {
    availability: AvailabilityPayload[];
    timezone: string;
    version: number;
  }): Promise<TutorProfile> {
    const { data } = await api.put<TutorProfile>(
      "/api/v1/tutors/me/availability",
      payload,
    );
    return data;
  },

  async submitForReview(): Promise<TutorProfile> {
    const { data } = await api.post<TutorProfile>("/api/v1/tutors/me/submit", {});
    return data;
  },

  async getReviews(tutorId: number): Promise<Review[]> {
    const { data } = await api.get<Review[]>(`/api/reviews/tutors/${tutorId}`);
    return data;
  },

  async updateProfilePhoto(file: File): Promise<TutorProfile> {
    logger.info("Uploading tutor profile photo");
    const formData = new FormData();
    formData.append("profile_photo", file);
    const { data } = await api.patch<TutorProfile>(
      "/api/v1/tutors/me/photo",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
    return data;
  },
};

// ============================================================================
// Bookings (Enhanced with BookingDTO schema)
// ============================================================================

import type { BookingDTO, BookingListResponse, BookingCreateRequest, BookingCancelRequest, BookingRescheduleRequest } from "@/types/booking";

export const bookings = {
  /**
   * List bookings for current user with pagination and filtering
   */
  async list(params?: {
    status?: string;
    role?: "student" | "tutor";
    page?: number;
    page_size?: number;
  }): Promise<BookingListResponse> {
    const { data } = await api.get<BookingListResponse>("/api/v1/bookings", { params });
    return data;
  },

  /**
   * Get single booking details
   */
  async get(bookingId: number): Promise<BookingDTO> {
    const { data } = await api.get<BookingDTO>(`/api/bookings/${bookingId}`);
    return data;
  },

  /**
   * Create new booking (student only)
   */
  async create(bookingData: BookingCreateRequest): Promise<BookingDTO> {
    const { data } = await api.post<BookingDTO>("/api/v1/bookings", bookingData);
    return data;
  },

  /**
   * Cancel booking with reason
   */
  async cancel(bookingId: number, request: BookingCancelRequest): Promise<BookingDTO> {
    const { data } = await api.post<BookingDTO>(`/api/bookings/${bookingId}/cancel`, request);
    return data;
  },

  /**
   * Reschedule booking to new time
   */
  async reschedule(bookingId: number, request: BookingRescheduleRequest): Promise<BookingDTO> {
    const { data } = await api.post<BookingDTO>(`/api/bookings/${bookingId}/reschedule`, request);
    return data;
  },

  /**
   * Tutor confirms pending booking
   */
  async confirm(bookingId: number, notes_tutor?: string): Promise<BookingDTO> {
    const { data } = await api.post<BookingDTO>(`/api/tutor/bookings/${bookingId}/confirm`, {
      notes_tutor,
    });
    return data;
  },

  /**
   * Tutor declines pending booking
   */
  async decline(bookingId: number, reason?: string): Promise<BookingDTO> {
    const { data } = await api.post<BookingDTO>(`/api/tutor/bookings/${bookingId}/decline`, {
      reason,
    });
    return data;
  },

  /**
   * Tutor marks student as no-show
   */
  async markStudentNoShow(bookingId: number, notes?: string): Promise<BookingDTO> {
    const { data } = await api.post<BookingDTO>(`/api/tutor/bookings/${bookingId}/mark-no-show-student`, {
      notes,
    });
    return data;
  },

  /**
   * Student marks tutor as no-show
   */
  async markTutorNoShow(bookingId: number, notes?: string): Promise<BookingDTO> {
    const { data } = await api.post<BookingDTO>(`/api/tutor/bookings/${bookingId}/mark-no-show-tutor`, {
      notes,
    });
    return data;
  },
};

// ============================================================================
// Reviews
// ============================================================================

export const reviews = {
  async create(
    bookingId: number,
    rating: number,
    comment?: string,
  ): Promise<Review> {
    const { data } = await api.post<Review>("/api/v1/reviews", {
      booking_id: bookingId,
      rating,
      comment,
    });
    return data;
  },
};

// ============================================================================
// Student Packages
// ============================================================================

export const packages = {
  async list(statusFilter?: string): Promise<StudentPackage[]> {
    const { data } = await api.get<StudentPackage[]>("/api/v1/packages", {
      params: statusFilter ? { status_filter: statusFilter } : undefined,
    });
    return data;
  },

  async purchase(packageData: {
    tutor_profile_id: number;
    pricing_option_id: number;
    payment_intent_id?: string;
    agreed_terms?: string;
  }): Promise<StudentPackage> {
    const { data } = await api.post<StudentPackage>("/api/v1/packages", packageData);
    return data;
  },

  async useCredit(packageId: number): Promise<StudentPackage> {
    const { data } = await api.patch<StudentPackage>(
      `/api/packages/${packageId}/use-credit`
    );
    return data;
  },
};

// ============================================================================
// Messages
// ============================================================================

export const messages = {
  async send(
    recipientId: number,
    message: string,
    bookingId?: number,
  ): Promise<Message> {
    try {
      const { data } = await api.post<Message>("/api/v1/messages", {
        recipient_id: recipientId,
        message,
        booking_id: bookingId,
      });
      return data;
    } catch (error: unknown) {
      logger.error('Failed to send message', error);
      throw error;
    }
  },

  async listThreads(limit?: number): Promise<MessageThread[]> {
    const { data } = await api.get<MessageThread[]>("/api/v1/messages/threads", {
      params: limit ? { limit } : undefined,
    });
    return data;
  },

  async getUserBasicInfo(userId: number): Promise<{
    id: number;
    email: string;
    first_name?: string | null;
    last_name?: string | null;
    avatar_url?: string | null;
    role: string;
  }> {
    const { data } = await api.get(`/api/messages/users/${userId}`);
    return data;
  },

  async getThreadMessages(
    otherUserId: number,
    bookingId?: number,
    page: number = 1,
    pageSize: number = 50
  ): Promise<Message[]> {
    const { data } = await api.get<{ messages: Message[] }>(
      `/api/messages/threads/${otherUserId}`,
      {
        params: {
          booking_id: bookingId,
          page,
          page_size: pageSize,
        },
      },
    );
    return data.messages;
  },

  async searchMessages(
    query: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<{ messages: Message[]; total: number; total_pages: number }> {
    const { data } = await api.get("/api/v1/messages/search", {
      params: {
        q: query,
        page,
        page_size: pageSize,
      },
    });
    return data;
  },

  async markRead(messageId: number): Promise<void> {
    await api.patch(`/api/messages/${messageId}/read`);
  },

  async markThreadRead(otherUserId: number, bookingId?: number): Promise<void> {
    await api.patch(`/api/messages/threads/${otherUserId}/read-all`, null, {
      params: bookingId ? { booking_id: bookingId } : undefined,
    });
  },

  async getUnreadCount(): Promise<{ total: number; by_sender: Record<number, number> }> {
    const { data } = await api.get("/api/v1/messages/unread/count");
    return data;
  },

  async editMessage(messageId: number, newMessage: string): Promise<Message> {
    const { data } = await api.patch<Message>(`/api/messages/${messageId}`, {
      message: newMessage,
    });
    return data;
  },

  async deleteMessage(messageId: number): Promise<void> {
    await api.delete(`/api/messages/${messageId}`);
  },
};

// ============================================================================
// Avatars
// ============================================================================

export const avatars = {
  async fetch(): Promise<AvatarSignedUrl> {
    logger.debug("Fetching avatar signed URL");
    const { data } = await api.get<AvatarApiResponse>("/api/v1/users/me/avatar");
    return transformAvatarResponse(data);
  },

  async upload(file: File): Promise<AvatarSignedUrl> {
    logger.info("Uploading user avatar");
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await api.post<AvatarApiResponse>(
      "/api/v1/users/me/avatar",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
    return transformAvatarResponse(data);
  },

  async remove(): Promise<void> {
    logger.info("Deleting user avatar");
    await api.delete("/api/v1/users/me/avatar");
  },

  async uploadForUser(userId: number, file: File): Promise<AvatarSignedUrl> {
    logger.info(`Admin overriding avatar for user ${userId}`);
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await api.patch<AvatarApiResponse>(
      `/api/admin/users/${userId}/avatar`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
    return transformAvatarResponse(data);
  },
};

// ============================================================================
// Students
// ============================================================================

export const students = {
  async getProfile(): Promise<StudentProfile> {
    const { data } = await api.get<StudentProfile>("/api/v1/profile/student/me");
    return data;
  },

  async updateProfile(
    updates: Partial<StudentProfile>,
  ): Promise<StudentProfile> {
    const { data } = await api.patch<StudentProfile>(
      "/api/v1/profile/student/me",
      updates,
    );
    return data;
  },
};

// ============================================================================
// Notifications
// ============================================================================

export interface NotificationItem {
  id: number;
  type: string;
  title: string;
  message: string;
  link?: string | null;
  is_read: boolean;
  created_at: string;
  category?: string | null;
  priority?: number;
  action_url?: string | null;
  action_label?: string | null;
  read_at?: string | null;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  unread_count: number;
}

export interface NotificationPreferences {
  email_enabled: boolean;
  push_enabled: boolean;
  sms_enabled: boolean;
  session_reminders_enabled: boolean;
  booking_requests_enabled: boolean;
  learning_nudges_enabled: boolean;
  review_prompts_enabled: boolean;
  achievements_enabled: boolean;
  marketing_enabled: boolean;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  preferred_notification_time: string | null;
  max_daily_notifications: number;
  max_weekly_nudges: number;
}

export interface NotificationPreferencesUpdate {
  email_enabled?: boolean;
  push_enabled?: boolean;
  sms_enabled?: boolean;
  session_reminders_enabled?: boolean;
  booking_requests_enabled?: boolean;
  learning_nudges_enabled?: boolean;
  review_prompts_enabled?: boolean;
  achievements_enabled?: boolean;
  marketing_enabled?: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  preferred_notification_time?: string;
  max_daily_notifications?: number;
  max_weekly_nudges?: number;
}

export const notifications = {
  async list(options?: { skip?: number; limit?: number; category?: string; unread_only?: boolean }): Promise<NotificationItem[]> {
    const params = new URLSearchParams();
    if (options?.skip) params.append('skip', options.skip.toString());
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.category) params.append('category', options.category);
    if (options?.unread_only) params.append('unread_only', 'true');
    const query = params.toString();
    const { data } = await api.get<NotificationListResponse>(`/api/notifications${query ? `?${query}` : ''}`);
    return data.items;
  },

  async listWithMeta(options?: { skip?: number; limit?: number; category?: string; unread_only?: boolean }): Promise<NotificationListResponse> {
    const params = new URLSearchParams();
    if (options?.skip) params.append('skip', options.skip.toString());
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.category) params.append('category', options.category);
    if (options?.unread_only) params.append('unread_only', 'true');
    const query = params.toString();
    const { data } = await api.get<NotificationListResponse>(`/api/notifications${query ? `?${query}` : ''}`);
    return data;
  },

  async getUnreadCount(): Promise<number> {
    const { data } = await api.get<{ count: number }>("/api/v1/notifications/unread-count");
    return data.count;
  },

  async markAsRead(notificationId: number): Promise<void> {
    await api.patch(`/api/notifications/${notificationId}/read`);
  },

  async markAllAsRead(): Promise<void> {
    await api.patch("/api/v1/notifications/mark-all-read");
  },

  async markRead(notificationId: number): Promise<void> {
    await api.patch(`/api/notifications/${notificationId}/read`);
  },

  async dismiss(notificationId: number): Promise<void> {
    await api.patch(`/api/notifications/${notificationId}/dismiss`);
  },

  async delete(notificationId: number): Promise<void> {
    await api.delete(`/api/notifications/${notificationId}`);
  },

  async getPreferences(): Promise<NotificationPreferences> {
    const { data } = await api.get<NotificationPreferences>("/api/v1/notifications/preferences");
    return data;
  },

  async updatePreferences(preferences: NotificationPreferencesUpdate): Promise<NotificationPreferences> {
    const { data } = await api.put<NotificationPreferences>("/api/v1/notifications/preferences", preferences);
    return data;
  },
};

// ============================================================================
// Admin
// ============================================================================

// Favorites API
export const favorites = {
  async getFavorites(): Promise<FavoriteTutor[]> {
    const { data } = await api.get("/api/v1/favorites");
    return data;
  },

  async addFavorite(tutorProfileId: number): Promise<FavoriteTutor> {
    const { data } = await api.post("/api/v1/favorites", { tutor_profile_id: tutorProfileId });
    return data;
  },

  async removeFavorite(tutorProfileId: number): Promise<void> {
    await api.delete(`/api/favorites/${tutorProfileId}`);
  },

  async checkFavorite(tutorProfileId: number): Promise<FavoriteTutor | null> {
    const response = await api.get(`/api/favorites/${tutorProfileId}`, {
      suppressErrorLog: true,
      validateStatus: (status) => status === 404 || (status >= 200 && status < 300),
    });
    if (response.status === 404) {
      return null;
    }
    return response.data;
  },
};

// ============================================================================
// Availability (Tutor scheduling)
// ============================================================================

export interface AvailabilitySlot {
  id?: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_recurring?: boolean;
}

export interface AvailableSlot {
  start_time: string;
  end_time: string;
  duration_minutes: number;
}

export const availability = {
  async getMyAvailability(): Promise<AvailabilitySlot[]> {
    const { data } = await api.get<AvailabilitySlot[]>("/api/v1/tutors/availability");
    return data;
  },

  async createAvailability(slot: Omit<AvailabilitySlot, "id">): Promise<AvailabilitySlot> {
    const { data } = await api.post<AvailabilitySlot>("/api/v1/tutors/availability", slot);
    return data;
  },

  async deleteAvailability(availabilityId: number): Promise<void> {
    await api.delete(`/api/tutors/availability/${availabilityId}`);
  },

  async createBulkAvailability(slots: Omit<AvailabilitySlot, "id">[]): Promise<{ message: string; count: number }> {
    const { data } = await api.post<{ message: string; count: number }>("/api/v1/tutors/availability/bulk", slots);
    return data;
  },

  async getTutorAvailableSlots(tutorId: number, startDate: string, endDate: string): Promise<AvailableSlot[]> {
    const { data } = await api.get<AvailableSlot[]>(`/api/tutors/${tutorId}/available-slots`, {
      params: { start_date: startDate, end_date: endDate },
    });
    return data;
  },
};

export const admin = {
  async listUsers(): Promise<User[]> {
    const { data } = await api.get<{ items?: User[] }>("/api/v1/admin/users");
    const items = data.items || [];
    return items.map((item) => normalizeUser(item));
  },

  async updateUser(userId: number, updates: Partial<User>): Promise<User> {
    const { data } = await api.put<User>(`/api/admin/users/${userId}`, updates);
    return normalizeUser(data);
  },

  async deleteUser(userId: number) {
    await api.delete(`/api/admin/users/${userId}`);
  },

  async listPendingTutors(page: number = 1, pageSize: number = 20): Promise<{ items: TutorProfile[]; total: number; page: number; page_size: number }> {
    const { data } = await api.get("/api/v1/admin/tutors/pending", {
      params: { page, page_size: pageSize },
    });
    return data;
  },

  async listApprovedTutors(page: number = 1, pageSize: number = 20): Promise<{ items: TutorProfile[]; total: number; page: number; page_size: number }> {
    const { data } = await api.get("/api/v1/admin/tutors/approved", {
      params: { page, page_size: pageSize },
    });
    return data;
  },

  async approveTutor(tutorId: number): Promise<TutorProfile> {
    const { data } = await api.post<TutorProfile>(
      `/api/admin/tutors/${tutorId}/approve`,
      {},
    );
    return data;
  },

  async rejectTutor(
    tutorId: number,
    rejectionReason: string,
  ): Promise<TutorProfile> {
    const { data } = await api.post<TutorProfile>(
      `/api/admin/tutors/${tutorId}/reject`,
      { rejection_reason: rejectionReason },
    );
    return data;
  },

  async getDashboardStats(): Promise<DashboardStats> {
    const cacheKey = getCacheKey("/api/v1/admin/dashboard/stats");
    const cached = getFromCache<DashboardStats>(cacheKey, 30 * 1000); // 30 seconds cache
    if (cached) {
      logger.debug("Dashboard stats loaded from cache");
      return cached;
    }
    const { data } = await api.get("/api/v1/admin/dashboard/stats");
    setCache(cacheKey, data);
    return data;
  },

  async getRecentActivities(limit: number = 50): Promise<any[]> {
    const cacheKey = getCacheKey("/api/v1/admin/dashboard/recent-activities", { limit });
    const cached = getFromCache<any[]>(cacheKey, 15 * 1000); // 15 seconds cache
    if (cached) return cached;
    const { data } = await api.get(`/api/admin/dashboard/recent-activities?limit=${limit}`);
    setCache(cacheKey, data);
    return data;
  },

  async getUpcomingSessions(limit: number = 50): Promise<any[]> {
    const cacheKey = getCacheKey("/api/v1/admin/dashboard/upcoming-sessions", { limit });
    const cached = getFromCache<any[]>(cacheKey, 30 * 1000);
    if (cached) return cached;
    const { data } = await api.get(`/api/admin/dashboard/upcoming-sessions?limit=${limit}`);
    setCache(cacheKey, data);
    return data;
  },

  async getSessionMetrics(): Promise<any[]> {
    const cacheKey = getCacheKey("/api/v1/admin/dashboard/session-metrics");
    const cached = getFromCache<any[]>(cacheKey, 60 * 1000); // 1 minute cache
    if (cached) return cached;
    const { data } = await api.get("/api/v1/admin/dashboard/session-metrics");
    setCache(cacheKey, data);
    return data;
  },

  async getMonthlyRevenue(months: number = 6): Promise<any[]> {
    const cacheKey = getCacheKey("/api/v1/admin/dashboard/monthly-revenue", { months });
    const cached = getFromCache<any[]>(cacheKey, 5 * 60 * 1000); // 5 minutes cache
    if (cached) return cached;
    const { data } = await api.get(`/api/admin/dashboard/monthly-revenue?months=${months}`);
    setCache(cacheKey, data);
    return data;
  },

  async getSubjectDistribution(): Promise<any[]> {
    const cacheKey = getCacheKey("/api/v1/admin/dashboard/subject-distribution");
    const cached = getFromCache<any[]>(cacheKey, 5 * 60 * 1000);
    if (cached) return cached;
    const { data } = await api.get("/api/v1/admin/dashboard/subject-distribution");
    setCache(cacheKey, data);
    return data;
  },

  async getUserGrowth(months: number = 6): Promise<any[]> {
    const cacheKey = getCacheKey("/api/v1/admin/dashboard/user-growth", { months });
    const cached = getFromCache<any[]>(cacheKey, 5 * 60 * 1000);
    if (cached) return cached;
    const { data } = await api.get(`/api/admin/dashboard/user-growth?months=${months}`);
    setCache(cacheKey, data);
    return data;
  },
};

// Owner API
export const owner = {
  async getDashboard(periodDays: number = 30): Promise<OwnerDashboard> {
    const cacheKey = getCacheKey("/api/v1/owner/dashboard", { period_days: periodDays });
    const cached = getFromCache<OwnerDashboard>(cacheKey, 60 * 1000); // 1 min cache
    if (cached) {
      logger.debug("Owner dashboard loaded from cache");
      return cached;
    }
    const { data } = await api.get("/api/v1/owner/dashboard", {
      params: { period_days: periodDays },
    });
    setCache(cacheKey, data);
    return data;
  },

  async getRevenue(periodDays: number = 30): Promise<RevenueMetrics> {
    const cacheKey = getCacheKey("/api/v1/owner/revenue", { period_days: periodDays });
    const cached = getFromCache<RevenueMetrics>(cacheKey, 60 * 1000);
    if (cached) return cached;
    const { data } = await api.get("/api/v1/owner/revenue", {
      params: { period_days: periodDays },
    });
    setCache(cacheKey, data);
    return data;
  },

  async getGrowth(periodDays: number = 30): Promise<GrowthMetrics> {
    const cacheKey = getCacheKey("/api/v1/owner/growth", { period_days: periodDays });
    const cached = getFromCache<GrowthMetrics>(cacheKey, 60 * 1000);
    if (cached) return cached;
    const { data } = await api.get("/api/v1/owner/growth", {
      params: { period_days: periodDays },
    });
    setCache(cacheKey, data);
    return data;
  },

  async getHealth(): Promise<MarketplaceHealth> {
    const cacheKey = getCacheKey("/api/v1/owner/health");
    const cached = getFromCache<MarketplaceHealth>(cacheKey, 2 * 60 * 1000); // 2 min
    if (cached) return cached;
    const { data } = await api.get("/api/v1/owner/health");
    setCache(cacheKey, data);
    return data;
  },

  async getCommissionTiers(): Promise<CommissionTierBreakdown> {
    const cacheKey = getCacheKey("/api/v1/owner/commission-tiers");
    const cached = getFromCache<CommissionTierBreakdown>(cacheKey, 5 * 60 * 1000); // 5 min
    if (cached) return cached;
    const { data } = await api.get("/api/v1/owner/commission-tiers");
    setCache(cacheKey, data);
    return data;
  },
};

// Tutor Student Notes API
export const tutorStudentNotes = {
  async getNote(studentId: number): Promise<{ id: number; notes: string | null } | null> {
    try {
      const { data } = await api.get(`/api/tutor/student-notes/${studentId}`);
      return data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  async updateNote(studentId: number, notes: string): Promise<void> {
    await api.put(`/api/tutor/student-notes/${studentId}`, { notes });
  },

  async deleteNote(studentId: number): Promise<void> {
    await api.delete(`/api/tutor/student-notes/${studentId}`);
  },
};

export default api;
