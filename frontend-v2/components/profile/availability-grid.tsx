'use client';

import { useState } from 'react';
import { Plus, Trash2, Clock, AlertTriangle } from 'lucide-react';
import { Button, Card, CardContent, CardHeader, CardTitle } from '@/components/ui';

interface TimeSlot {
  id?: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
}

interface AvailabilityGridProps {
  slots: TimeSlot[];
  onChange: (slots: TimeSlot[]) => void;
  disabled?: boolean;
}

const DAYS_OF_WEEK = [
  { value: 0, label: 'Sunday', short: 'Sun' },
  { value: 1, label: 'Monday', short: 'Mon' },
  { value: 2, label: 'Tuesday', short: 'Tue' },
  { value: 3, label: 'Wednesday', short: 'Wed' },
  { value: 4, label: 'Thursday', short: 'Thu' },
  { value: 5, label: 'Friday', short: 'Fri' },
  { value: 6, label: 'Saturday', short: 'Sat' },
];

const TIME_OPTIONS = Array.from({ length: 48 }, (_, i) => {
  const hours = Math.floor(i / 2);
  const minutes = i % 2 === 0 ? '00' : '30';
  const time = `${hours.toString().padStart(2, '0')}:${minutes}`;
  return time;
});

function slotsOverlap(a: { start_time: string; end_time: string }, b: { start_time: string; end_time: string }): boolean {
  return a.start_time < b.end_time && b.start_time < a.end_time;
}

function getEndTimeOptions(startTime: string): string[] {
  return TIME_OPTIONS.filter((time) => time > startTime);
}

interface DaySlotEditorProps {
  day: typeof DAYS_OF_WEEK[number];
  slots: TimeSlot[];
  onAdd: (slot: TimeSlot) => void;
  onRemove: (index: number) => void;
  onUpdate: (index: number, slot: TimeSlot) => void;
  disabled?: boolean;
}

function DaySlotEditor({ day, slots, onAdd, onRemove, onUpdate, disabled }: DaySlotEditorProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [newStart, setNewStart] = useState('09:00');
  const [newEnd, setNewEnd] = useState('17:00');
  const [overlapError, setOverlapError] = useState<string | null>(null);

  const daySlots = slots.filter((s) => s.day_of_week === day.value);

  const checkOverlap = (start: string, end: string, excludeIndex?: number): boolean => {
    const candidate = { start_time: start, end_time: end };
    return daySlots.some((existing, idx) => {
      if (excludeIndex !== undefined) {
        const globalIdx = slots.findIndex(
          (s) => s.day_of_week === existing.day_of_week &&
            s.start_time === existing.start_time &&
            s.end_time === existing.end_time
        );
        if (globalIdx === excludeIndex) return false;
      }
      return slotsOverlap(candidate, existing);
    });
  };

  const handleAdd = () => {
    if (newStart && newEnd && newStart < newEnd) {
      if (checkOverlap(newStart, newEnd)) {
        setOverlapError('This time slot overlaps with an existing slot.');
        return;
      }
      setOverlapError(null);
      onAdd({
        day_of_week: day.value,
        start_time: newStart,
        end_time: newEnd,
      });
      setIsAdding(false);
      setNewStart('09:00');
      setNewEnd('17:00');
    }
  };

  const handleStartChange = (value: string) => {
    setNewStart(value);
    setOverlapError(null);
    if (newEnd <= value) {
      const nextOptions = getEndTimeOptions(value);
      if (nextOptions.length > 0) {
        setNewEnd(nextOptions[0]);
      }
    }
  };

  return (
    <div className="p-3 sm:p-4 rounded-xl bg-slate-50 dark:bg-slate-800">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium text-slate-900 dark:text-white text-sm sm:text-base">
          {day.label}
        </h4>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setIsAdding(!isAdding)}
          disabled={disabled}
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {daySlots.length === 0 && !isAdding && (
        <p className="text-sm text-slate-500">No availability set</p>
      )}

      <div className="space-y-2">
        {daySlots.map((slot) => {
          const globalIndex = slots.findIndex(
            (s) =>
              s.day_of_week === slot.day_of_week &&
              s.start_time === slot.start_time &&
              s.end_time === slot.end_time
          );

          return (
            <div
              key={`${slot.day_of_week}-${slot.start_time}-${slot.end_time}`}
              className="flex flex-wrap sm:flex-nowrap items-center gap-2 bg-white dark:bg-slate-900 rounded-lg p-2"
            >
              <Clock className="h-4 w-4 text-slate-400 flex-shrink-0 hidden sm:block" />
              <select
                value={slot.start_time}
                onChange={(e) =>
                  onUpdate(globalIndex, { ...slot, start_time: e.target.value })
                }
                disabled={disabled}
                className="flex-1 min-w-[70px] text-sm bg-transparent border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1.5 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                {TIME_OPTIONS.map((time) => (
                  <option key={time} value={time}>
                    {time}
                  </option>
                ))}
              </select>
              <span className="text-slate-400 text-sm">to</span>
              <select
                value={slot.end_time}
                onChange={(e) =>
                  onUpdate(globalIndex, { ...slot, end_time: e.target.value })
                }
                disabled={disabled}
                className="flex-1 min-w-[70px] text-sm bg-transparent border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1.5 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                {getEndTimeOptions(slot.start_time).map((time) => (
                  <option key={time} value={time}>
                    {time}
                  </option>
                ))}
              </select>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => onRemove(globalIndex)}
                disabled={disabled}
                className="h-8 w-8 text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 shrink-0"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          );
        })}

        {isAdding && (
          <div className="space-y-2">
            <div className="flex flex-wrap sm:flex-nowrap items-center gap-2 bg-white dark:bg-slate-900 rounded-lg p-2 border-2 border-dashed border-primary-300 dark:border-primary-700">
              <Clock className="h-4 w-4 text-primary-500 flex-shrink-0 hidden sm:block" />
              <select
                value={newStart}
                onChange={(e) => handleStartChange(e.target.value)}
                className="flex-1 min-w-[70px] text-sm bg-transparent border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1.5 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                {TIME_OPTIONS.map((time) => (
                  <option key={time} value={time}>
                    {time}
                  </option>
                ))}
              </select>
              <span className="text-slate-400 text-sm">to</span>
              <select
                value={newEnd}
                onChange={(e) => { setNewEnd(e.target.value); setOverlapError(null); }}
                className="flex-1 min-w-[70px] text-sm bg-transparent border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1.5 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                {getEndTimeOptions(newStart).map((time) => (
                  <option key={time} value={time}>
                    {time}
                  </option>
                ))}
              </select>
              <div className="flex items-center gap-1 shrink-0">
                <Button
                  type="button"
                  size="sm"
                  onClick={handleAdd}
                  disabled={newStart >= newEnd}
                >
                  Add
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => { setIsAdding(false); setOverlapError(null); }}
                >
                  Cancel
                </Button>
              </div>
            </div>
            {overlapError && (
              <p className="flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-400">
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                {overlapError}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function AvailabilityGrid({ slots, onChange, disabled }: AvailabilityGridProps) {
  const handleAdd = (newSlot: TimeSlot) => {
    onChange([...slots, newSlot]);
  };

  const handleRemove = (index: number) => {
    onChange(slots.filter((_, i) => i !== index));
  };

  const handleUpdate = (index: number, updatedSlot: TimeSlot) => {
    const newSlots = [...slots];
    newSlots[index] = updatedSlot;
    onChange(newSlots);
  };

  return (
    <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
      {DAYS_OF_WEEK.map((day) => (
        <DaySlotEditor
          key={day.value}
          day={day}
          slots={slots}
          onAdd={handleAdd}
          onRemove={handleRemove}
          onUpdate={handleUpdate}
          disabled={disabled}
        />
      ))}
    </div>
  );
}

export function AvailabilityPreview({ slots }: { slots: TimeSlot[] }) {
  const groupedSlots = DAYS_OF_WEEK.map((day) => ({
    ...day,
    slots: slots.filter((s) => s.day_of_week === day.value),
  }));

  const hasAnySlots = slots.length > 0;

  if (!hasAnySlots) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <Clock className="h-12 w-12 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">No availability set</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Weekly Availability</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {groupedSlots.map((day) => {
            if (day.slots.length === 0) return null;

            return (
              <div
                key={day.value}
                className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800"
              >
                <h4 className="font-medium text-slate-900 dark:text-white mb-2 text-sm sm:text-base">
                  {day.label}
                </h4>
                <div className="space-y-1">
                  {day.slots.map((slot, idx) => (
                    <div
                      key={idx}
                      className="text-sm text-slate-600 dark:text-slate-400 flex items-center gap-2"
                    >
                      <Clock className="h-3 w-3 shrink-0" />
                      {slot.start_time} - {slot.end_time}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
