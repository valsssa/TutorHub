/**
 * Core API client with axios instance and interceptors
 */
import axios, { AxiosError } from "axios";
import Cookies from "js-cookie";
import { createLogger } from "../../logger";
import { getApiBaseUrl } from "@/shared/utils/url";

const logger = createLogger('API');

// API Error Response Interface
export interface ApiErrorResponse {
  detail: string;
  [key: string]: unknown;
}

declare module "axios" {
  export interface AxiosRequestConfig {
    suppressErrorLog?: boolean;
  }
}

// Production API URL
const API_URL = getApiBaseUrl(process.env.NEXT_PUBLIC_API_URL);

logger.info(`API client initialized with base URL: ${API_URL}`);

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_URL,
  timeout: 15000, // Reduced from 30s to 15s for faster failures
  headers: {
    "Content-Type": "application/json",
  },
});

// Add retry logic with exponential backoff
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;

    // Don't retry if no config or already retried max times
    if (!config || config.__retryCount >= MAX_RETRIES) {
      return Promise.reject(error);
    }

    // Only retry on network errors or 5xx server errors
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

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = Cookies.get("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    logger.debug(`Request to ${config.url} with auth token`);
  } else {
    logger.debug(`Request to ${config.url} without auth token`);
  }
  return config;
});

// Handle errors consistently and parse decimal fields
api.interceptors.response.use(
  (response) => {
    logger.debug(`Response from ${response.config.url}: ${response.status}`);
    if (response.data) {
      // Parse decimal fields in response
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
        window.location.pathname !== "/login"
      ) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

/**
 * Parse decimal string fields to numbers
 */
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
