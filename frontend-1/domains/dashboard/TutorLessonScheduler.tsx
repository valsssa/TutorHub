
import React, { useState } from 'react';
import { User, Calendar, RotateCw, ArrowRight, Clock, ChevronDown } from 'lucide-react';

interface TutorLessonSchedulerProps {
    initialTab?: 'Lesson' | 'Time off' | 'Extra slots';
    onClose: () => void;
}

export const TutorLessonScheduler: React.FC<TutorLessonSchedulerProps> = ({ initialTab = 'Lesson', onClose }) => {
    const [activeTab, setActiveTab] = useState<'Lesson' | 'Time off' | 'Extra slots'>(initialTab);
    const [lessonType, setLessonType] = useState<'Single' | 'Weekly'>('Single');
    
    // Time off state
    const [timeOffTitle, setTimeOffTitle] = useState('Busy');
    const [isAllDay, setIsAllDay] = useState(false);

    return (
        <div className="space-y-6">
            {/* Tabs */}
            <div className="flex border-b border-slate-200 dark:border-slate-700">
                {['Lesson', 'Time off', 'Extra slots'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab as any)}
                        className={`px-4 py-3 text-sm font-medium transition-all relative ${
                            activeTab === tab 
                                ? 'text-slate-900 dark:text-white' 
                                : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                    >
                        {tab}
                        {activeTab === tab && (
                            <span className="absolute bottom-0 left-0 w-full h-0.5 rounded-t-full bg-emerald-500"></span>
                        )}
                    </button>
                ))}
            </div>

            {activeTab === 'Lesson' && (
                <div className="space-y-5 animate-in fade-in duration-300">
                    {/* Student Input */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Student</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                                <User size={18} />
                            </div>
                            <input 
                                type="text" 
                                placeholder="Add student"
                                className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all text-slate-900 dark:text-white placeholder-slate-400"
                            />
                        </div>
                    </div>

                    {/* Lesson Type */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Lesson type</label>
                        <div className="flex gap-3">
                            <button 
                                onClick={() => setLessonType('Single')}
                                className={`flex-1 flex items-center justify-center gap-2 py-2.5 border rounded-xl text-sm font-medium transition-all ${
                                    lessonType === 'Single' 
                                        ? 'border-emerald-500 ring-1 ring-emerald-500 bg-emerald-50/50 dark:bg-emerald-900/20 text-slate-900 dark:text-white' 
                                        : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-600'
                                }`}
                            >
                                <Calendar size={16} /> Single
                            </button>
                            <button 
                                onClick={() => setLessonType('Weekly')}
                                className={`flex-1 flex items-center justify-center gap-2 py-2.5 border rounded-xl text-sm font-medium transition-all ${
                                    lessonType === 'Weekly' 
                                        ? 'border-emerald-500 ring-1 ring-emerald-500 bg-emerald-50/50 dark:bg-emerald-900/20 text-slate-900 dark:text-white' 
                                        : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-600'
                                }`}
                            >
                                <RotateCw size={16} /> Weekly
                            </button>
                        </div>
                    </div>

                    {/* Date and Time */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Date and time</label>
                        <div className="space-y-3">
                            <select className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer">
                                <option>50 minutes (Standard lesson)</option>
                                <option>25 minutes (Trial lesson)</option>
                            </select>
                            
                            <div className="flex items-center gap-3">
                                <div className="relative flex-1">
                                    <input 
                                        type="date" 
                                        className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all"
                                    />
                                </div>
                                <ArrowRight size={16} className="text-slate-400 shrink-0" />
                                <div className="relative w-1/3">
                                    <select className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer text-center">
                                        <option>20:00</option>
                                        <option>21:00</option>
                                        <option>22:00</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Submit Button */}
                    <button 
                        onClick={onClose}
                        className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 mt-4 active:scale-[0.98]"
                    >
                        Schedule lesson
                    </button>
                </div>
            )}

            {activeTab === 'Time off' && (
                <div className="space-y-5 animate-in fade-in duration-300">
                    {/* Title Input */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Title</label>
                        <input 
                            type="text" 
                            value={timeOffTitle}
                            onChange={(e) => setTimeOffTitle(e.target.value)}
                            placeholder="Busy"
                            className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all text-slate-900 dark:text-white placeholder-slate-400"
                        />
                        <p className="text-xs text-slate-500 mt-1.5">Visible only to you</p>
                    </div>

                    {/* Starts */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Starts</label>
                        <div className="flex gap-3">
                            <div className="relative flex-1">
                                <input 
                                    type="date" 
                                    className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all"
                                />
                            </div>
                            <div className={`relative ${isAllDay ? 'hidden' : 'w-1/3'}`}>
                                <select className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer">
                                    <option>20:00</option>
                                    <option>20:30</option>
                                    <option>21:00</option>
                                </select>
                                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                            </div>
                        </div>
                    </div>

                    {/* Ends */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Ends</label>
                        <div className="flex gap-3">
                            <div className="relative flex-1">
                                <input 
                                    type="date" 
                                    className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all"
                                />
                            </div>
                            <div className={`relative ${isAllDay ? 'hidden' : 'w-1/3'}`}>
                                <select className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer">
                                    <option>21:00</option>
                                    <option>21:30</option>
                                    <option>22:00</option>
                                </select>
                                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                            </div>
                        </div>
                    </div>

                    {/* All day checkbox */}
                    <div className="flex items-center gap-2 pt-1">
                        <input 
                            type="checkbox" 
                            id="all-day"
                            checked={isAllDay}
                            onChange={(e) => setIsAllDay(e.target.checked)}
                            className="w-4 h-4 rounded border-slate-300 text-emerald-500 focus:ring-emerald-500"
                        />
                        <label htmlFor="all-day" className="text-sm font-medium text-slate-700 dark:text-slate-300 cursor-pointer select-none">
                            All day
                        </label>
                    </div>

                    {/* Submit Button */}
                    <button 
                        onClick={onClose}
                        className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 mt-4 active:scale-[0.98]"
                    >
                        Book time off
                    </button>
                </div>
            )}

            {activeTab === 'Extra slots' && (
                <div className="space-y-5 animate-in fade-in duration-300">
                    <div>
                        <h3 className="font-bold text-slate-900 dark:text-white text-base">Add extra slots</h3>
                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Choose time slots up to 24 hours long.</p>
                    </div>

                    {/* Starts */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Starts</label>
                        <div className="flex gap-3">
                            <div className="relative flex-1">
                                <input 
                                    type="date" 
                                    className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all"
                                />
                            </div>
                            <div className="relative w-1/3">
                                <select className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer">
                                    <option>20:00</option>
                                    <option>20:30</option>
                                    <option>21:00</option>
                                </select>
                                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                            </div>
                        </div>
                    </div>

                    {/* Ends */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Ends</label>
                        <div className="flex gap-3">
                            <div className="relative flex-1">
                                <input 
                                    type="date" 
                                    className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all"
                                />
                            </div>
                            <div className="relative w-1/3">
                                <select className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer">
                                    <option>21:00</option>
                                    <option>21:30</option>
                                    <option>22:00</option>
                                </select>
                                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                            </div>
                        </div>
                    </div>

                    {/* Submit Button */}
                    <button 
                        onClick={onClose}
                        className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 mt-4 active:scale-[0.98]"
                    >
                        Add
                    </button>
                </div>
            )}
        </div>
    );
};
