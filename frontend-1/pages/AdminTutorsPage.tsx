
import React, { useState } from 'react';
import { ChevronLeft, Users, Search, Filter, Star, MoreHorizontal } from 'lucide-react';
import { Tutor } from '../domain/types';
import { Badge } from '../components/shared/UI';

interface AdminTutorsPageProps {
    tutors: Tutor[];
    onBack: () => void;
    onViewProfile: (tutor: Tutor) => void;
}

export const AdminTutorsPage: React.FC<AdminTutorsPageProps> = ({ tutors, onBack, onViewProfile }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [filterVerified, setFilterVerified] = useState('All');

    const filteredTutors = tutors.filter(tutor => {
        const matchesSearch = 
            tutor.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
            tutor.subject.toLowerCase().includes(searchQuery.toLowerCase());
        
        if (filterVerified === 'Verified') return matchesSearch && tutor.isVerified;
        if (filterVerified === 'Unverified') return matchesSearch && !tutor.isVerified;
        return matchesSearch;
    });

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl">
            <button 
                onClick={onBack}
                className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-6 group"
            >
                <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform"/> 
                Back to Dashboard
            </button>

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                        <Users size={32} className="text-purple-500" /> Active Tutors
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Manage all tutor profiles registered on the platform.</p>
                </div>
                
                <div className="flex gap-3">
                    <div className="relative">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                        <input 
                            type="text" 
                            placeholder="Search by name or subject..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 w-64"
                        />
                    </div>
                    <div className="relative">
                        <select 
                            value={filterVerified}
                            onChange={(e) => setFilterVerified(e.target.value)}
                            className="pl-9 pr-8 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none cursor-pointer"
                        >
                            <option>All</option>
                            <option>Verified</option>
                            <option>Unverified</option>
                        </select>
                        <Filter size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                    </div>
                </div>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Tutor</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Status</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Subject</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Rating</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Rate/Hr</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {filteredTutors.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                                        No tutors found.
                                    </td>
                                </tr>
                            ) : (
                                filteredTutors.map((tutor) => (
                                    <tr key={tutor.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
                                        <td className="px-6 py-4 cursor-pointer" onClick={() => onViewProfile(tutor)}>
                                            <div className="flex items-center gap-3">
                                                <img src={tutor.imageUrl} alt={tutor.name} className="w-10 h-10 rounded-full object-cover border border-slate-200 dark:border-slate-700" />
                                                <div>
                                                    <div className="font-bold text-slate-900 dark:text-white text-sm group-hover:text-emerald-600 transition-colors">{tutor.name}</div>
                                                    <div className="text-xs text-slate-500 truncate max-w-[150px]">{tutor.title}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <Badge variant={tutor.isVerified ? 'verified' : 'default'}>
                                                {tutor.isVerified ? 'Verified' : 'Unverified'}
                                            </Badge>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                                            {tutor.subject}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-1 text-sm font-medium text-slate-900 dark:text-white">
                                                <Star size={14} className="fill-amber-500 text-amber-500" />
                                                {tutor.rating} <span className="text-slate-400 font-normal">({tutor.reviews})</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-sm font-bold text-slate-900 dark:text-white">
                                            ${tutor.hourlyRate}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button className="text-slate-400 hover:text-slate-600 dark:hover:text-white p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                                                <MoreHorizontal size={18} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
