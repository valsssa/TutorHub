/**
 * Authentication API
 */
import Cookies from "js-cookie";
import type { User } from "@/types";
import { api } from "./core/client";
import { clearCache } from "./core/cache";
import { normalizeUser } from "./core/utils";
import { createLogger } from "../logger";

const logger = createLogger('AuthAPI');

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

      const { data } = await api.post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
        expires_in: number;
      }>(
        "/api/v1/auth/login",
        params.toString(),
        {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        },
      );

      // Calculate token expiry from expires_in (seconds)
      const expiryTime = Date.now() + (data.expires_in * 1000);

      // Store access token
      Cookies.set("token", data.access_token, {
        expires: 7,
        secure: true,
        sameSite: 'strict'
      });

      // Store token expiry for proactive refresh
      Cookies.set("token_expiry", expiryTime.toString(), {
        expires: 7,
        secure: true,
        sameSite: 'strict'
      });

      // Store refresh token securely
      Cookies.set("refresh_token", data.refresh_token, {
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
    Cookies.remove("token_expiry");
    clearCache(); // Clear cache on logout
    if (typeof window !== "undefined") {
      window.location.href = "/";
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
};
