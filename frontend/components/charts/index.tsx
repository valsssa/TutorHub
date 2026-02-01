"use client";

import dynamic from "next/dynamic";

// Lazy load chart components to reduce initial bundle size
// These will only be loaded when actually rendered

export const LazyEarningsChart = dynamic(
  () => import("./EarningsChart"),
  {
    ssr: false,
    loading: () => (
      <div className="h-64 bg-slate-100 dark:bg-slate-800 rounded animate-pulse flex items-center justify-center">
        <span className="text-slate-400">Loading chart...</span>
      </div>
    ),
  }
);

// Add more lazy chart exports as needed
export const LazyAnalyticsCharts = dynamic(
  () => import("./AnalyticsCharts"),
  {
    ssr: false,
    loading: () => (
      <div className="h-64 bg-slate-100 dark:bg-slate-800 rounded animate-pulse flex items-center justify-center">
        <span className="text-slate-400">Loading analytics...</span>
      </div>
    ),
  }
);
