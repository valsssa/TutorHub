"use client";

import { FiGlobe } from "react-icons/fi";
import { useLocale } from "@/contexts/LocaleContext";
import { LANGUAGES, CURRENCIES } from "@/lib/locale";
import SettingsCard from "@/components/settings/SettingsCard";

export default function LocalePage() {
  const { locale, currency, setLocale, setCurrency } = useLocale();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          🌐 Language & Currency
        </h2>
        <p className="text-slate-600">
          Choose your preferred language and currency
        </p>
      </div>

      {/* Language */}
      <SettingsCard
        title="Language"
        description="Select your preferred interface language"
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => setLocale(lang.code)}
              className={`
                p-4 rounded-xl border-2 transition-all text-left
                ${
                  locale === lang.code
                    ? "border-sky-500 bg-sky-50"
                    : "border-slate-200 hover:border-sky-300 hover:bg-slate-50"
                }
              `}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{lang.flag}</span>
                  <div>
                    <p className="font-semibold text-slate-900">{lang.nativeLabel}</p>
                    <p className="text-xs text-slate-500">{lang.label}</p>
                  </div>
                </div>
                {locale === lang.code && (
                  <span className="text-sky-600 text-xl">✓</span>
                )}
              </div>
            </button>
          ))}
        </div>
      </SettingsCard>

      {/* Currency */}
      <SettingsCard
        title="Currency"
        description="Choose how prices are displayed"
      >
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {CURRENCIES.map((curr) => (
            <button
              key={curr.code}
              onClick={() => setCurrency(curr.code)}
              className={`
                p-4 rounded-xl border-2 transition-all text-center
                ${
                  currency === curr.code
                    ? "border-sky-500 bg-sky-50"
                    : "border-slate-200 hover:border-sky-300 hover:bg-slate-50"
                }
              `}
            >
              <p className="text-2xl mb-1">{curr.symbol}</p>
              <p className="font-semibold text-slate-900 text-sm">{curr.code}</p>
              <p className="text-xs text-slate-500">{curr.label}</p>
              {currency === curr.code && (
                <span className="text-sky-600 text-lg mt-1 block">✓</span>
              )}
            </button>
          ))}
        </div>
      </SettingsCard>

      {/* Info */}
      <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl">
        <p className="text-sm text-blue-900">
          <strong>💡 Tip:</strong> Your preferences are saved automatically and
          will apply across all devices.
        </p>
      </div>
    </div>
  );
}
