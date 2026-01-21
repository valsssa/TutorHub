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
      const { data } = await api.post<User>("/api/auth/register", {
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
        "/api/auth/login",
        params.toString(),
        {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        },
      );

      Cookies.set("token", data.access_token, {
        expires: 7,
        secure: true,
        sameSite: 'strict'
      });

      // Clear cache on login to ensure fresh data
      clearCache();

      logger.info(`Login successful for: ${email}`);
      return data.access_token;
    } catch (error) {
      logger.error(`Login failed for ${email}`, error);
      throw error;
    }
  },

  async getCurrentUser(): Promise<User> {
    logger.debug("Fetching current user");
    try {
      const { data } = await api.get<User>("/api/auth/me");
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
      const { data } = await api.put<User>("/api/auth/me", updates);
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
        const { data } = await api.patch<User>("/api/users/currency", { currency });
        latest = data;
      }

      if (timezone) {
        const { data } = await api.patch<User>("/api/users/preferences", { timezone });
        latest = data;
      }

      if (!latest) {
        const { data } = await api.get<User>("/api/auth/me");
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
