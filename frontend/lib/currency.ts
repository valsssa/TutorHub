/**
 * Currency utilities for global application
 */

import { formatCurrency as baseFormatCurrency } from "@/shared/utils/formatters";

export type CurrencyCode = "USD" | "EUR" | "GBP" | "JPY" | "CNY" | "INR" | "CAD" | "AUD" | "CHF" | "SEK" | "NOK" | "DKK" | "PLN" | "RUB" | "BRL" | "MXN" | "ZAR" | "KRW" | "SGD" | "NZD";

export interface CurrencyInfo {
  code: CurrencyCode;
  symbol: string;
  name: string;
  locale: string;
}

export const SUPPORTED_CURRENCIES: Record<CurrencyCode, CurrencyInfo> = {
  USD: { code: "USD", symbol: "$", name: "US Dollar", locale: "en-US" },
  EUR: { code: "EUR", symbol: "€", name: "Euro", locale: "de-DE" },
  GBP: { code: "GBP", symbol: "£", name: "British Pound", locale: "en-GB" },
  JPY: { code: "JPY", symbol: "¥", name: "Japanese Yen", locale: "ja-JP" },
  CNY: { code: "CNY", symbol: "¥", name: "Chinese Yuan", locale: "zh-CN" },
  INR: { code: "INR", symbol: "₹", name: "Indian Rupee", locale: "en-IN" },
  CAD: { code: "CAD", symbol: "C$", name: "Canadian Dollar", locale: "en-CA" },
  AUD: { code: "AUD", symbol: "A$", name: "Australian Dollar", locale: "en-AU" },
  CHF: { code: "CHF", symbol: "Fr", name: "Swiss Franc", locale: "de-CH" },
  SEK: { code: "SEK", symbol: "kr", name: "Swedish Krona", locale: "sv-SE" },
  NOK: { code: "NOK", symbol: "kr", name: "Norwegian Krone", locale: "nb-NO" },
  DKK: { code: "DKK", symbol: "kr", name: "Danish Krone", locale: "da-DK" },
  PLN: { code: "PLN", symbol: "zł", name: "Polish Złoty", locale: "pl-PL" },
  RUB: { code: "RUB", symbol: "₽", name: "Russian Ruble", locale: "ru-RU" },
  BRL: { code: "BRL", symbol: "R$", name: "Brazilian Real", locale: "pt-BR" },
  MXN: { code: "MXN", symbol: "Mex$", name: "Mexican Peso", locale: "es-MX" },
  ZAR: { code: "ZAR", symbol: "R", name: "South African Rand", locale: "en-ZA" },
  KRW: { code: "KRW", symbol: "₩", name: "South Korean Won", locale: "ko-KR" },
  SGD: { code: "SGD", symbol: "S$", name: "Singapore Dollar", locale: "en-SG" },
  NZD: { code: "NZD", symbol: "NZ$", name: "New Zealand Dollar", locale: "en-NZ" },
};

/**
 * Format amount with user's currency preference
 */
export function formatPrice(
  amount: number | string,
  currency: CurrencyCode = "USD",
): string {
  return baseFormatCurrency(amount, currency);
}

/**
 * Get currency symbol
 */
export function getCurrencySymbol(currency: CurrencyCode = "USD"): string {
  return SUPPORTED_CURRENCIES[currency]?.symbol || "$";
}

/**
 * Get currency name
 */
export function getCurrencyName(currency: CurrencyCode = "USD"): string {
  return SUPPORTED_CURRENCIES[currency]?.name || "US Dollar";
}

/**
 * Validate currency code
 */
export function isValidCurrency(code: string): code is CurrencyCode {
  return code in SUPPORTED_CURRENCIES;
}

/**
 * Get list of all supported currencies
 */
export function getAllCurrencies(): CurrencyInfo[] {
  return Object.values(SUPPORTED_CURRENCIES);
}
