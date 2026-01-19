/**
 * Automatic locale detection for timezone and currency
 */

import { getBrowserTimezone, isValidTimezone } from "./timezone";
import { isValidCurrency, type CurrencyCode } from "./currency";

/**
 * Currency mapping based on country/locale
 */
const LOCALE_TO_CURRENCY: Record<string, CurrencyCode> = {
  // Americas
  "en-US": "USD",
  "en-CA": "CAD",
  "es-MX": "MXN",
  "pt-BR": "BRL",
  "es-AR": "USD", // Argentina uses USD for international
  
  // Europe
  "en-GB": "GBP",
  "de-DE": "EUR",
  "fr-FR": "EUR",
  "it-IT": "EUR",
  "es-ES": "EUR",
  "nl-NL": "EUR",
  "pt-PT": "EUR",
  "pl-PL": "PLN",
  "sv-SE": "SEK",
  "nb-NO": "NOK",
  "da-DK": "DKK",
  "ru-RU": "RUB",
  "de-CH": "CHF",
  "fr-CH": "CHF",
  "it-CH": "CHF",
  
  // Asia
  "ja-JP": "JPY",
  "zh-CN": "CNY",
  "ko-KR": "KRW",
  "hi-IN": "INR",
  "en-IN": "INR",
  "en-SG": "SGD",
  
  // Australia & NZ
  "en-AU": "AUD",
  "en-NZ": "NZD",
  
  // Africa
  "en-ZA": "ZAR",
};

/**
 * Detect user's currency based on browser locale
 */
export function detectCurrency(): CurrencyCode {
  try {
    const locale = navigator.language || "en-US";
    
    // Try exact match
    if (locale in LOCALE_TO_CURRENCY) {
      return LOCALE_TO_CURRENCY[locale];
    }
    
    // Try language-only match (e.g., "en" from "en-US")
    const language = locale.split("-")[0];
    
    // European languages typically use EUR
    if (["de", "fr", "it", "es", "pt", "nl"].includes(language)) {
      return "EUR";
    }
    
    // Default to USD for international compatibility
    return "USD";
  } catch (error) {
    console.warn("Currency detection failed, using USD", error);
    return "USD";
  }
}

/**
 * Detect user's timezone from browser
 */
export function detectTimezone(): string {
  try {
    const timezone = getBrowserTimezone();
    return isValidTimezone(timezone) ? timezone : "UTC";
  } catch (error) {
    console.warn("Timezone detection failed, using UTC", error);
    return "UTC";
  }
}

/**
 * Get detected locale preferences
 */
export interface LocalePreferences {
  currency: CurrencyCode;
  timezone: string;
  locale: string;
}

export function detectLocalePreferences(): LocalePreferences {
  return {
    currency: detectCurrency(),
    timezone: detectTimezone(),
    locale: navigator.language || "en-US",
  };
}

/**
 * Store detected preferences in localStorage
 */
export function saveDetectedPreferences(preferences: LocalePreferences): void {
  try {
    localStorage.setItem("locale_preferences", JSON.stringify(preferences));
  } catch (error) {
    console.warn("Failed to save locale preferences", error);
  }
}

/**
 * Load stored preferences from localStorage
 */
export function loadStoredPreferences(): LocalePreferences | null {
  try {
    const stored = localStorage.getItem("locale_preferences");
    return stored ? JSON.parse(stored) : null;
  } catch (error) {
    console.warn("Failed to load locale preferences", error);
    return null;
  }
}

/**
 * Get preferences (stored or detected)
 */
export function getLocalePreferences(): LocalePreferences {
  const stored = loadStoredPreferences();
  if (stored) return stored;
  
  const detected = detectLocalePreferences();
  saveDetectedPreferences(detected);
  return detected;
}
