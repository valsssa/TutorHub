"use client";

import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";
import clsx from "clsx";

interface BreadcrumbItem {
  /** Display label */
  label: string;
  /** URL path - if undefined, item is not clickable (current page) */
  href?: string;
  /** Icon to display before label */
  icon?: React.ReactNode;
}

interface BreadcrumbProps {
  /** Breadcrumb items */
  items: BreadcrumbItem[];
  /** Show home icon as first item */
  showHome?: boolean;
  /** Home URL (default: /) */
  homeHref?: string;
  /** Separator between items */
  separator?: React.ReactNode;
  /** Size variant */
  size?: "sm" | "md";
  /** Additional className */
  className?: string;
}

export default function Breadcrumb({
  items,
  showHome = true,
  homeHref = "/dashboard",
  separator,
  size = "md",
  className,
}: BreadcrumbProps) {
  const sizeClasses = {
    sm: "text-xs",
    md: "text-sm",
  };

  const allItems: BreadcrumbItem[] = showHome
    ? [{ label: "Home", href: homeHref, icon: <Home className="w-4 h-4" /> }, ...items]
    : items;

  return (
    <nav
      aria-label="Breadcrumb"
      className={clsx("flex items-center", sizeClasses[size], className)}
    >
      <ol className="flex items-center flex-wrap gap-1" role="list">
        {allItems.map((item, index) => {
          const isLast = index === allItems.length - 1;

          return (
            <li key={index} className="flex items-center">
              {/* Item */}
              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  className={clsx(
                    "flex items-center gap-1.5 font-medium transition-colors",
                    "text-slate-500 dark:text-slate-400",
                    "hover:text-emerald-600 dark:hover:text-emerald-400"
                  )}
                >
                  {item.icon}
                  <span className={index === 0 && showHome ? "sr-only sm:not-sr-only" : ""}>
                    {item.label}
                  </span>
                </Link>
              ) : (
                <span
                  className={clsx(
                    "flex items-center gap-1.5 font-medium",
                    isLast
                      ? "text-slate-900 dark:text-white"
                      : "text-slate-500 dark:text-slate-400"
                  )}
                  aria-current={isLast ? "page" : undefined}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </span>
              )}

              {/* Separator */}
              {!isLast && (
                <span
                  className="mx-2 text-slate-300 dark:text-slate-600"
                  aria-hidden="true"
                >
                  {separator || <ChevronRight className="w-4 h-4" />}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// Helper to generate breadcrumb items from pathname
export function generateBreadcrumbItems(
  pathname: string,
  customLabels?: Record<string, string>
): BreadcrumbItem[] {
  const segments = pathname.split("/").filter(Boolean);
  const items: BreadcrumbItem[] = [];
  let currentPath = "";

  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i];
    currentPath += `/${segment}`;

    // Check for custom label or generate from segment
    const label =
      customLabels?.[currentPath] ||
      customLabels?.[segment] ||
      formatSegmentLabel(segment);

    // Last item doesn't have href (current page)
    const isLast = i === segments.length - 1;

    items.push({
      label,
      href: isLast ? undefined : currentPath,
    });
  }

  return items;
}

// Format a URL segment into a readable label
function formatSegmentLabel(segment: string): string {
  // Handle dynamic segments like [id]
  if (segment.startsWith("[") && segment.endsWith("]")) {
    return segment.slice(1, -1).replace(/-/g, " ");
  }

  // Convert kebab-case to Title Case
  return segment
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
