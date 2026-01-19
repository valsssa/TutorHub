
import React, { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, Clock, Calendar as CalendarIcon, Check } from 'lucide-react';

interface VisualCalendarProps {
    availability: string[]; // ISO date strings
    mode: 'view' | 'edit';
    onSlotSelect?: (isoDate: string) => void; // For booking (view mode)
    onAvailabilityChange?: (newAvailability: string[]) => void; // For editing (edit mode)
}

export const VisualCalendar: React.FC<VisualCalendarProps> = ({ 
    availability, 
    mode, 
    onSlotSelect, 
    onAvailabilityChange 
}) => {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [selectedDate, setSelectedDate] = useState<Date>(new Date());

    // Generate days for the current month view
    const calendarDays = useMemo(() => {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        
        const days = [];
        const paddingDays = firstDay.getDay(); // 0 is Sunday
        
        // Previous month padding
        for (let i = 0; i < paddingDays; i++) {
            days.push(null);
        }
        
        // Days of current month
        for (let i = 1; i <= lastDay.getDate(); i++) {
            days.push(new Date(year, month, i));
        }
        
        return days;
    }, [currentDate]);

    // Standard time slots for Edit Mode
    const timeSlots = [
        '09:00', '10:00', '11:00', '12:00', '13:00', 
        '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00'
    ];

    const isSlotAvailable = (date: Date, time: string) => {
        const checkStr = `${date.toISOString().split('T')[0]}T${time}`;
        // Loose matching to handle seconds/milliseconds differences if any
        return availability.some(iso => iso.startsWith(checkStr));
    };

    const hasAvailabilityOnDay = (date: Date) => {
        const dateStr = date.toISOString().split('T')[0];
        return availability.some(iso => iso.startsWith(dateStr));
    };

    const handleSlotClick = (time: string) => {
        const fullIso = `${selectedDate.toISOString().split('T')[0]}T${time}:00`;
        
        if (mode === 'edit' && onAvailabilityChange) {
            const exists = isSlotAvailable(selectedDate, time);
            let newList;
            if (exists) {
                // Remove (filtering loosely by prefix)
                const checkStr = `${selectedDate.toISOString().split('T')[0]}T${time}`;
                newList = availability.filter(iso => !iso.startsWith(checkStr));
            } else {
                // Add
                newList = [...availability, fullIso];
            }
            onAvailabilityChange(newList);
        } else if (mode === 'view' && onSlotSelect) {
            if (isSlotAvailable(selectedDate, time)) {
                onSlotSelect(fullIso);
            }
        }
    };

    const changeMonth = (offset: number) => {
        const newDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + offset, 1);
        setCurrentDate(newDate);
    };

    return (
        <div className="flex flex-col md:flex-row gap-6 h-[500px]">
            {/* Left: Calendar Grid */}
            <div className="flex-1 flex flex-col">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-slate-900 dark:text-white text-lg">
                        {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                    </h3>
                    <div className="flex gap-2">
                        <button onClick={() => changeMonth(-1)} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors">
                            <ChevronLeft size={20} />
                        </button>
                        <button onClick={() => changeMonth(1)} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors">
                            <ChevronRight size={20} />
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-7 text-center mb-2">
                    {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
                        <div key={d} className="text-xs font-semibold text-slate-400 uppercase tracking-wider py-2">
                            {d}
                        </div>
                    ))}
                </div>

                <div className="grid grid-cols-7 gap-1 flex-1 content-start">
                    {calendarDays.map((date, idx) => {
                        if (!date) return <div key={`pad-${idx}`} className="aspect-square" />;
                        
                        const isSelected = date.toDateString() === selectedDate.toDateString();
                        const isToday = date.toDateString() === new Date().toDateString();
                        const hasSlots = hasAvailabilityOnDay(date);

                        return (
                            <button
                                key={date.toISOString()}
                                onClick={() => setSelectedDate(date)}
                                className={`
                                    aspect-square rounded-xl flex flex-col items-center justify-center relative transition-all border
                                    ${isSelected 
                                        ? 'bg-emerald-600 text-white border-emerald-600 shadow-md scale-105 z-10' 
                                        : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-slate-100 dark:border-slate-800 hover:border-emerald-400 dark:hover:border-emerald-600'
                                    }
                                    ${isToday && !isSelected ? 'bg-slate-50 dark:bg-slate-800 font-semibold' : ''}
                                `}
                            >
                                <span className="text-sm">{date.getDate()}</span>
                                {hasSlots && !isSelected && (
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1"></span>
                                )}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Right: Time Slots */}
            <div className="w-full md:w-64 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col">
                <div className="mb-4 pb-4 border-b border-slate-200 dark:border-slate-800">
                    <h4 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                        <Clock size={18} className="text-emerald-500" />
                        {selectedDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                    </h4>
                    <p className="text-xs text-slate-500 mt-1">
                        {mode === 'edit' ? 'Tap slots to toggle availability' : 'Select a time to book'}
                    </p>
                </div>

                <div className="flex-1 overflow-y-auto pr-1 space-y-2 custom-scrollbar">
                    {timeSlots.map(time => {
                        const isAvailable = isSlotAvailable(selectedDate, time);
                        
                        if (mode === 'view' && !isAvailable) return null;

                        return (
                            <button
                                key={time}
                                onClick={() => handleSlotClick(time)}
                                className={`
                                    w-full py-3 px-4 rounded-xl flex items-center justify-between transition-all border
                                    ${mode === 'edit' 
                                        ? (isAvailable 
                                            ? 'bg-emerald-100 dark:bg-emerald-900/30 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300' 
                                            : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-400 hover:border-emerald-400')
                                        : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-emerald-500 hover:shadow-md text-slate-700 dark:text-slate-200'
                                    }
                                `}
                            >
                                <span className="font-medium">{time}</span>
                                {mode === 'edit' && isAvailable && <Check size={16} />}
                            </button>
                        );
                    })}
                    
                    {mode === 'view' && !hasAvailabilityOnDay(selectedDate) && (
                        <div className="text-center py-8 text-slate-400 text-sm">
                            No slots available on this date.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
