
import React, { useState, useEffect } from 'react';
import { X, MessageSquare, Calendar, FileText, MoreHorizontal, User as UserIcon, SlidersHorizontal, ChevronDown } from 'lucide-react';

interface StudentRow {
    id: string;
    name: string;
    avatar?: string;
    type: 'Subscription' | 'Trial' | 'Cancelled';
    lessonsCompleted?: number;
    lessonsTotal?: number;
    nextLesson?: string;
    suggestedAction?: 'Message student' | null;
}

const MOCK_STUDENTS: StudentRow[] = [
    { id: '1', name: 'Lauren', type: 'Subscription', lessonsCompleted: 7, lessonsTotal: 8, nextLesson: 'Oct 27' },
    { id: '2', name: 'Luis P.', type: 'Subscription', lessonsCompleted: 4, lessonsTotal: 5, nextLesson: 'Oct 27' },
    { id: '3', name: 'Elodie C.', type: 'Cancelled', lessonsCompleted: 14, lessonsTotal: 14, nextLesson: 'Oct 28', suggestedAction: 'Message student' },
    { id: '4', name: 'Mauricio E.', type: 'Subscription', lessonsCompleted: 5, lessonsTotal: 5, nextLesson: 'Nov 1' },
    { id: '5', name: 'Adam', avatar: 'https://i.pravatar.cc/150?u=adam', type: 'Cancelled', lessonsCompleted: 1, lessonsTotal: 1, suggestedAction: 'Message student' },
    { id: '6', name: 'AL AQL, F.', avatar: 'https://i.pravatar.cc/150?u=alaql', type: 'Trial' },
    { id: '7', name: 'alberto m.', avatar: 'https://i.pravatar.cc/150?u=alberto', type: 'Trial' },
    { id: '8', name: 'Alejandro E.', type: 'Cancelled', lessonsCompleted: 0, lessonsTotal: 0, suggestedAction: 'Message student' },
    { id: '9', name: 'Ali E.', avatar: 'https://i.pravatar.cc/150?u=ali', type: 'Trial' },
    { id: '10', name: 'Alla L.', type: 'Trial' },
];

interface TutorStudentsPageProps {
    onMessage: (studentId: string, name: string) => void;
    onSchedule: (studentId: string) => void;
    onViewProfile: (studentId: string) => void;
    onViewHistory: (studentId: string) => void;
    onArchive: (studentId: string) => void;
    onNotes: (studentId: string) => void;
}

export const TutorStudentsPage: React.FC<TutorStudentsPageProps> = ({ 
    onMessage, 
    onSchedule, 
    onViewProfile, 
    onViewHistory, 
    onArchive,
    onNotes 
}) => {
    const [activeFilter, setActiveFilter] = useState<string | null>('Current');
    const [openMenuId, setOpenMenuId] = useState<string | null>(null);

    const handleFilterClick = () => {
        // Placeholder for filter modal logic
        console.log("Open filters");
    };

    const handleRemoveFilter = () => {
        setActiveFilter(null);
    };

    const toggleMenu = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setOpenMenuId(openMenuId === id ? null : id);
    };

    // Close menus when clicking outside
    useEffect(() => {
        const handleClickOutside = () => setOpenMenuId(null);
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, []);

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-6">My students</h1>

            {/* Filter Toolbar */}
            <div className="flex items-center gap-3 mb-6">
                <button 
                    onClick={handleFilterClick}
                    className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-sm font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors active:scale-95"
                >
                    <SlidersHorizontal size={16} />
                    Filters
                </button>
                
                {activeFilter && (
                    <div className="flex items-center gap-2 px-3 py-2 bg-slate-100 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 animate-in fade-in zoom-in-95 duration-200">
                        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{activeFilter}</span>
                        <button 
                            onClick={handleRemoveFilter}
                            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-0.5 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                        >
                            <X size={14} />
                        </button>
                    </div>
                )}
            </div>

            {/* Table */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-visible shadow-sm">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-slate-200 dark:border-slate-800">
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Name</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Type</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Lessons</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Next lesson</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Suggested action</th>
                                <th className="px-6 py-4"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {MOCK_STUDENTS.map((student) => (
                                <tr key={student.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
                                    <td className="px-6 py-4 cursor-pointer" onClick={() => onViewProfile(student.id)}>
                                        <div className="flex items-center gap-3">
                                            {student.avatar ? (
                                                <img src={student.avatar} alt={student.name} className="w-9 h-9 rounded-md object-cover bg-slate-200" />
                                            ) : (
                                                <div className="w-9 h-9 rounded-md bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400">
                                                    <UserIcon size={16} />
                                                </div>
                                            )}
                                            <span className="font-bold text-sm text-slate-900 dark:text-white group-hover:text-emerald-600 transition-colors">{student.name}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex px-2.5 py-1 rounded-md text-xs font-bold ${
                                            student.type === 'Subscription' 
                                                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                                                : student.type === 'Trial'
                                                ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
                                                : 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300'
                                        }`}>
                                            {student.type}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        {student.lessonsTotal !== undefined ? (
                                            <div className="flex items-center gap-3">
                                                <div className="w-12 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                                                    <div 
                                                        className="h-full bg-slate-900 dark:bg-white rounded-full" 
                                                        style={{ width: `${(student.lessonsCompleted! / student.lessonsTotal) * 100}%` }}
                                                    ></div>
                                                </div>
                                                <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                                                    {student.lessonsCompleted}/{student.lessonsTotal}
                                                </span>
                                            </div>
                                        ) : (
                                            <span className="text-slate-400 text-sm">-</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                                        {student.nextLesson || '-'}
                                    </td>
                                    <td className="px-6 py-4">
                                        {student.suggestedAction ? (
                                            <button 
                                                onClick={() => onMessage(student.id, student.name)}
                                                className="text-sm font-bold text-slate-900 dark:text-white underline decoration-slate-300 dark:decoration-slate-600 hover:decoration-slate-900 dark:hover:decoration-white underline-offset-2 transition-all"
                                            >
                                                {student.suggestedAction}
                                            </button>
                                        ) : (
                                            <span className="text-slate-400 text-sm">-</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 relative">
                                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button 
                                                onClick={() => onMessage(student.id, student.name)}
                                                className="p-2 text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                                                title="Message"
                                            >
                                                <MessageSquare size={18} />
                                            </button>
                                            <button 
                                                onClick={() => onSchedule(student.id)}
                                                className="p-2 text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                                                title="Schedule Lesson"
                                            >
                                                <Calendar size={18} />
                                            </button>
                                            <button 
                                                onClick={() => onNotes(student.id)}
                                                className="p-2 text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                                                title="Notes"
                                            >
                                                <FileText size={18} />
                                            </button>
                                            <div className="relative">
                                                <button 
                                                    onClick={(e) => toggleMenu(student.id, e)}
                                                    className={`p-2 rounded-lg transition-colors ${openMenuId === student.id ? 'text-slate-900 dark:text-white bg-slate-100 dark:bg-slate-800' : 'text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'}`}
                                                >
                                                    <MoreHorizontal size={18} />
                                                </button>
                                                {openMenuId === student.id && (
                                                    <div className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-slate-900 rounded-lg shadow-xl border border-slate-200 dark:border-slate-800 py-1 z-50 animate-in fade-in zoom-in-95 duration-200">
                                                        <button 
                                                            onClick={(e) => { e.stopPropagation(); onViewProfile(student.id); setOpenMenuId(null); }}
                                                            className="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                                                        >
                                                            View Profile
                                                        </button>
                                                        <button 
                                                            onClick={(e) => { e.stopPropagation(); onViewHistory(student.id); setOpenMenuId(null); }}
                                                            className="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                                                        >
                                                            History
                                                        </button>
                                                        <div className="h-px bg-slate-100 dark:bg-slate-800 my-1"></div>
                                                        <button 
                                                            onClick={(e) => { e.stopPropagation(); onArchive(student.id); setOpenMenuId(null); }}
                                                            className="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors"
                                                        >
                                                            Archive Student
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
