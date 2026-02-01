"use client";

import { useState, useMemo } from "react";
import { ChevronLeft, ChevronRight, X } from "lucide-react";

interface CalendarWeekViewProps {
  onClose?: () => void;
  timezone?: string;
}

export default function CalendarWeekView({ 
  onClose, 
  timezone = "GMT" 
}: CalendarWeekViewProps) {
  const [view, setView] = useState<"Day" | "Week">("Week");
  const [currentDate, setCurrentDate] = useState(new Date());

  // Helper to get start of week (Monday)
  const getStartOfWeek = (d: Date) => {
    const date = new Date(d);
    const day = date.getDay();
    const diff = date.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(date.setDate(diff));
  };

  // Generate days dynamically
  const days = useMemo(() => {
    if (view === "Day") {
      return [
        {
          name: currentDate.toLocaleDateString("en-US", { weekday: "short" }),
          date: currentDate.getDate(),
          fullDate: currentDate,
          isToday: currentDate.toDateString() === new Date().toDateString(),
        },
      ];
    }

    const start = getStartOfWeek(currentDate);
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      return {
        name: d.toLocaleDateString("en-US", { weekday: "short" }),
        date: d.getDate(),
        fullDate: d,
        isToday: d.toDateString() === new Date().toDateString(),
      };
    });
  }, [currentDate, view]);

  const dateRangeString = useMemo(() => {
    if (view === "Day") {
      return currentDate.toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      });
    }

    const start = getStartOfWeek(currentDate);
    const end = new Date(start);
    end.setDate(end.getDate() + 6);

    if (
      start.getMonth() === end.getMonth() &&
      start.getFullYear() === end.getFullYear()
    ) {
      return `${start.toLocaleDateString("en-US", { month: "short", day: "numeric" })} – ${end.getDate()}, ${end.getFullYear()}`;
    }
    if (start.getFullYear() === end.getFullYear()) {
      return `${start.toLocaleDateString("en-US", { month: "short", day: "numeric" })} – ${end.toLocaleDateString("en-US", { month: "short", day: "numeric" })}, ${end.getFullYear()}`;
    }
    return `${start.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })} – ${end.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`;
  }, [currentDate, view]);

  const handlePrev = () => {
    const newDate = new Date(currentDate);
    if (view === "Day") {
      newDate.setDate(newDate.getDate() - 1);
    } else {
      newDate.setDate(newDate.getDate() - 7);
    }
    setCurrentDate(newDate);
  };

  const handleNext = () => {
    const newDate = new Date(currentDate);
    if (view === "Day") {
      newDate.setDate(newDate.getDate() + 1);
    } else {
      newDate.setDate(newDate.getDate() + 7);
    }
    setCurrentDate(newDate);
  };

  const handleToday = () => {
    setCurrentDate(new Date());
    setView("Day");
  };

  const hours = Array.from(
    { length: 24 },
    (_, i) => `${i.toString().padStart(2, "0")}:00`
  );

  // Constants for consistent grid sizing
  const HOUR_HEIGHT = 60; // Height in pixels for each hour row
  const TIME_COLUMN_WIDTH = 60; // Width in pixels for time column
  
  // Generate grid template classes based on view
  const gridColsClass = view === "Day" 
    ? "grid-cols-[60px_minmax(0,1fr)]"
    : `grid-cols-[60px_repeat(${days.length},_minmax(0,1fr))]`;

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-white dark:bg-slate-900 overflow-hidden">
      {/* Calendar Navigation - Google Calendar Style */}
      <div className="px-4 py-2.5 flex flex-wrap justify-between items-center gap-3 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
        <div className="flex items-center gap-3 order-1 sm:order-1">
          {/* Navigation Arrows */}
          <div className="flex items-center gap-1">
            <button
              onClick={handlePrev}
              className="p-2.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center touch-manipulation"
              aria-label="Previous"
            >
              <ChevronLeft size={20} className="text-slate-600 dark:text-slate-400" />
            </button>
            <button
              onClick={handleNext}
              className="p-2.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center touch-manipulation"
              aria-label="Next"
            >
              <ChevronRight size={20} className="text-slate-600 dark:text-slate-400" />
            </button>
          </div>
          {/* Date Range */}
          <h2 className="text-lg font-medium text-slate-900 dark:text-white whitespace-nowrap">
            {dateRangeString}
          </h2>
        </div>

        <div className="flex items-center gap-2 order-2 sm:order-2 ml-auto sm:ml-0">
          {/* View Toggle */}
          <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
            <button
              onClick={handleToday}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all min-h-[36px] touch-manipulation ${
                view === "Day"
                  ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Today
            </button>
            <button
              onClick={() => setView("Week")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all min-h-[36px] touch-manipulation ${
                view === "Week"
                  ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Week
            </button>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 min-w-[44px] min-h-[44px] flex items-center justify-center touch-manipulation"
              title="Close"
              aria-label="Close"
            >
              <X size={20} />
            </button>
          )}
        </div>
      </div>

      {/* Calendar Grid - Google Calendar Style */}
      <div className="flex-1 overflow-auto bg-white dark:bg-slate-900 relative">
        <div
          className={view === "Day" ? "w-full" : "min-w-[600px] md:min-w-[800px]"}
        >
          {/* Header Row - Google Calendar Style */}
          <div
            className={`grid ${gridColsClass} border-b border-slate-200 dark:border-slate-700 sticky top-0 bg-white dark:bg-slate-900 z-30 shadow-sm`}
          >
            {/* Timezone Column - Locked width */}
            <div 
              className="sticky left-0 z-40 bg-white dark:bg-slate-900 text-xs font-medium text-slate-500 dark:text-slate-400 border-r border-slate-200 dark:border-slate-700 text-center flex items-center justify-center"
              style={{ width: `${TIME_COLUMN_WIDTH}px`, minWidth: `${TIME_COLUMN_WIDTH}px`, maxWidth: `${TIME_COLUMN_WIDTH}px` }}
            >
              {timezone}
            </div>
            {/* Day Headers */}
            {days.map((day, i) => (
              <div
                key={i}
                className="px-2 py-3 text-center border-r border-slate-200 dark:border-slate-700 last:border-r-0 bg-white dark:bg-slate-900"
              >
                <div className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5 uppercase tracking-wide">
                  {day.name}
                </div>
                <div
                  className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium transition-colors ${
                    day.isToday
                      ? "bg-blue-600 text-white dark:bg-blue-500"
                      : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  {day.date}
                </div>
              </div>
            ))}
          </div>

          {/* Grid Body - Google Calendar Style */}
          <div className="relative">
            {hours.map((time, i) => (
              <div
                key={i}
                className={`grid ${gridColsClass} border-b border-slate-100 dark:border-slate-800`}
                style={{ height: `${HOUR_HEIGHT}px`, minHeight: `${HOUR_HEIGHT}px` }}
              >
                {/* Time Label - Google Calendar Style - Locked width */}
                <div 
                  className="sticky left-0 z-20 bg-white dark:bg-slate-900 text-xs text-slate-500 dark:text-slate-400 text-right border-r border-slate-200 dark:border-slate-700 pr-2 flex items-start justify-end pt-1"
                  style={{ width: `${TIME_COLUMN_WIDTH}px`, minWidth: `${TIME_COLUMN_WIDTH}px`, maxWidth: `${TIME_COLUMN_WIDTH}px` }}
                >
                  <span>{time}</span>
                </div>

                {/* Day Cells - Google Calendar Style */}
                {days.map((day, j) => (
                  <div
                    key={j}
                    className="border-r border-slate-100 dark:border-slate-800 last:border-r-0 relative group cursor-pointer bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                  >
                    {/* Subtle hover indicator */}
                    <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                      <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-blue-500 dark:bg-blue-400"></div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
