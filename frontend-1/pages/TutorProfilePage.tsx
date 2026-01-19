
import React, { useState, useRef } from 'react';
import { 
    ChevronLeft, ChevronRight, ChevronDown, Shield, Star, MapPin, Award, MessageCircle, 
    CheckCircle, Play, Clock, Globe, Zap, Calendar, Heart, PenLine, Quote, Share, Info
} from 'lucide-react';
import { Tutor } from '../domain/types';

interface TutorProfilePageProps {
    tutor: Tutor;
    onBack: () => void;
    backLabel?: string;
    onBook: () => void;
    onBookSlot?: (tutor: Tutor, slot: string) => void;
    onMessage: (tutor: Tutor) => void;
    isOwnProfile?: boolean;
    onEdit?: () => void;
    onViewFullSchedule?: () => void;
    onToggleSave: (e: React.MouseEvent, id: string) => void;
    isSaved: boolean;
}

export const TutorProfilePage: React.FC<TutorProfilePageProps> = ({ 
    tutor, onBack, backLabel, onBook, onBookSlot, onMessage, isOwnProfile = false, onEdit, onViewFullSchedule, onToggleSave, isSaved
}) => {
    const [isBioExpanded, setIsBioExpanded] = useState(false);
    
    // Schedule Section State
    const [scheduleDuration, setScheduleDuration] = useState<25 | 50>(50);
    const [scheduleDate, setScheduleDate] = useState(new Date());
    const [isScheduleExpanded, setIsScheduleExpanded] = useState(false);

    // Ref for scrolling to schedule
    const scheduleRef = useRef<HTMLDivElement>(null);

    const scrollToSchedule = () => {
        scheduleRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    const handleShare = async () => {
        // Use current URL or fallback to a generic one if local/invalid
        let url = window.location.href;
        if (!url.startsWith('http')) {
            url = `https://educonnect.app/tutor/${tutor.id}`;
        }

        const shareData = {
            title: `Check out ${tutor.name} on EduConnect`,
            text: `I found a great tutor, ${tutor.name}!`,
            url: url
        };

        if (navigator.share) {
            try {
                await navigator.share(shareData);
            } catch (err) {
                console.warn("Share API failed or was cancelled, falling back to clipboard", err);
                try {
                    await navigator.clipboard.writeText(url);
                    alert("Link copied to clipboard!");
                } catch (clipErr) {
                    console.error("Clipboard failed", clipErr);
                }
            }
        } else {
            try {
                await navigator.clipboard.writeText(url);
                alert("Link copied to clipboard!");
            } catch (err) {
                console.error("Clipboard failed", err);
            }
        }
    };

    const handlePrevWeek = () => {
        const newDate = new Date(scheduleDate);
        newDate.setDate(newDate.getDate() - 7);
        setScheduleDate(newDate);
    };

    const handleNextWeek = () => {
        const newDate = new Date(scheduleDate);
        newDate.setDate(newDate.getDate() + 7);
        setScheduleDate(newDate);
    };

    const firstName = tutor.name.split(' ')[0];
    const initial = tutor.name.split(' ')[1]?.charAt(0);
    const displayName = initial ? `${firstName} ${initial}.` : firstName;

    // Generate days for schedule
    const scheduleDays = Array.from({ length: 7 }, (_, i) => {
        const d = new Date(scheduleDate);
        d.setDate(d.getDate() + i);
        return d;
    });

    const formatDateRange = (start: Date, end: Date) => {
        const startMonth = start.toLocaleDateString('en-US', { month: 'short' });
        const endMonth = end.toLocaleDateString('en-US', { month: 'short' });
        const startYear = start.getFullYear();
        const endYear = end.getFullYear();
        const startDay = start.getDate();
        const endDay = end.getDate();

        if (startYear !== endYear) {
            return `${startMonth} ${startDay}, ${startYear} – ${endMonth} ${endDay}, ${endYear}`;
        } else if (startMonth !== endMonth) {
            return `${startMonth} ${startDay} – ${endMonth} ${endDay}, ${startYear}`;
        } else {
            return `${startMonth} ${startDay} – ${endDay}, ${startYear}`;
        }
    };

    const handleSlotClick = (dayIndex: number, timeStr: string) => {
        const date = new Date(scheduleDays[dayIndex]);
        const [hours, minutes] = timeStr.split(':').map(Number);
        date.setHours(hours, minutes, 0, 0);
        
        if (onBookSlot) {
            onBookSlot(tutor, date.toISOString());
        } else {
            onBook();
        }
    };

    // Mock slots generation for demo
    const getSlotsForDay = (dayIndex: number) => {
        // Extended set of slots
        const allSlots = [
            "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", 
            "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", 
            "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", 
            "15:00", "15:30", "16:00", "16:30", "17:00", "17:30",
            "18:00", "18:30", "19:00", "19:30", "20:00", "20:30"
        ];
        
        // Create deterministic pattern based on day index
        // Shift start time based on day to make it look realistic
        const shift = (dayIndex * 2) % 8; 
        // Number of available slots varies
        const count = 12 + (dayIndex % 5);
        
        const daySlots = allSlots.slice(shift, shift + count);
        
        if (isScheduleExpanded) {
            return daySlots;
        }
        return daySlots.slice(0, 5); // Show top 5 by default
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 pb-24 md:pb-8">
            {/* Breadcrumb / Nav */}
            <div className="container mx-auto px-4 py-6 max-w-7xl">
                <button 
                    onClick={onBack} 
                    className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium group"
                >
                    <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform"/> 
                    {backLabel || 'Back to Marketplace'}
                </button>
            </div>

            <div className="container mx-auto px-4 max-w-7xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                
                {/* --- LEFT COLUMN: Main Content (Trust & Information) --- */}
                <div className="lg:col-span-8 space-y-8">
                    
                    {/* Hero Header */}
                    <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
                        <div className="flex flex-col sm:flex-row gap-6 items-start">
                            <div className="relative">
                                <img 
                                    src={tutor.imageUrl} 
                                    alt={tutor.name} 
                                    className="w-24 h-24 sm:w-32 sm:h-32 rounded-2xl object-cover border-4 border-slate-50 dark:border-slate-800 shadow-lg" 
                                />
                                <div className="absolute -bottom-2 -right-2 w-6 h-6 bg-emerald-500 rounded-full border-[3px] border-white dark:border-slate-900 flex items-center justify-center shadow-sm" title="Online">
                                    <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
                                </div>
                            </div>
                            
                            <div className="flex-1">
                                <div className="flex flex-wrap items-center gap-2 mb-2">
                                    <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">{tutor.name}</h1>
                                    {tutor.isVerified && (
                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold uppercase tracking-wide border border-emerald-200 dark:border-emerald-800">
                                            <Shield size={12} className="fill-emerald-500/20" /> Verified Expert
                                        </span>
                                    )}
                                </div>
                                <p className="text-lg text-slate-600 dark:text-slate-300 font-medium mb-4">{tutor.title}</p>
                                
                                {/* Quick Stats Row */}
                                <div className="flex flex-wrap gap-4 sm:gap-8 text-sm text-slate-600 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800 pt-4">
                                    <div className="flex items-center gap-2">
                                        <div className="p-1.5 bg-amber-100 dark:bg-amber-900/30 rounded-full text-amber-600 dark:text-amber-400">
                                            <Star size={16} fill="currentColor"/>
                                        </div>
                                        <div>
                                            <p className="font-bold text-slate-900 dark:text-white">{tutor.rating}</p>
                                            <p className="text-xs">Rating</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-full text-blue-600 dark:text-blue-400">
                                            <Clock size={16} />
                                        </div>
                                        <div>
                                            <p className="font-bold text-slate-900 dark:text-white">1,240</p>
                                            <p className="text-xs">Hours Taught</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="p-1.5 bg-purple-100 dark:bg-purple-900/30 rounded-full text-purple-600 dark:text-purple-400">
                                            <Globe size={16} />
                                        </div>
                                        <div>
                                            <p className="font-bold text-slate-900 dark:text-white">
                                                {tutor.languages && tutor.languages.length > 0 ? tutor.languages.join(', ') : (tutor.nativeLanguage || 'English')}
                                            </p>
                                            <p className="text-xs">Languages</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Video Introduction Placeholder */}
                    <div 
                        className="bg-slate-900 rounded-3xl overflow-hidden aspect-video relative group cursor-pointer shadow-lg"
                        onClick={() => tutor.videoUrl && window.open(tutor.videoUrl, '_blank')}
                    >
                        <img 
                            src="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=2070&auto=format&fit=crop" 
                            alt="Video Thumbnail" 
                            className="w-full h-full object-cover opacity-60 group-hover:opacity-40 transition-opacity duration-300"
                        />
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300 border border-white/50">
                                <Play size={32} className="text-white fill-white ml-1" />
                            </div>
                        </div>
                        <div className="absolute bottom-4 left-4">
                            <p className="text-white font-semibold">Meet {tutor.name.split(' ')[0]}</p>
                            <p className="text-white/80 text-sm">{tutor.videoUrl ? 'Click to watch introduction' : '1 min introduction'}</p>
                        </div>
                    </div>

                    {/* About & Bio (Moved Here) */}
                    <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">About Me</h2>
                        <div className={`prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-300 relative transition-all duration-500 ease-in-out ${isBioExpanded ? '' : 'max-h-[140px] overflow-hidden'}`}>
                            <p className="mb-4 leading-relaxed whitespace-pre-line">{tutor.bio}</p>
                            {!isBioExpanded && (
                                <div className="absolute bottom-0 left-0 w-full h-20 bg-gradient-to-t from-white dark:from-slate-900 to-transparent"></div>
                            )}
                        </div>
                        <button 
                            onClick={() => setIsBioExpanded(!isBioExpanded)}
                            className="mt-2 text-emerald-600 dark:text-emerald-400 font-bold hover:underline focus:outline-none"
                        >
                            {isBioExpanded ? 'Show less' : 'Show more'}
                        </button>
                    </div>

                    {/* Expertise Tags */}
                    <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Teaches</h2>
                        <div className="flex flex-wrap gap-2">
                            {tutor.topics.map(topic => (
                                <span key={topic} className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-lg font-medium text-sm hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors cursor-default">
                                    {topic}
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* Languages Spoken (I speak) */}
                    {(tutor.languages && tutor.languages.length > 0) && (
                        <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">I speak</h2>
                            <div className="flex flex-wrap gap-3">
                                {tutor.languages.map(lang => (
                                    <span key={lang} className={`px-4 py-2 rounded-lg font-medium text-sm cursor-default border flex items-center gap-2 ${
                                        tutor.nativeLanguage === lang 
                                        ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800' 
                                        : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700'
                                    }`}>
                                        {lang}
                                        {tutor.nativeLanguage === lang && (
                                            <span className="text-[10px] uppercase font-bold tracking-wider opacity-80 bg-emerald-100 dark:bg-emerald-900/40 px-1.5 py-0.5 rounded border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200">Native</span>
                                        )}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                     {/* Teaching Philosophy (Separated) */}
                     <div className="bg-emerald-50 dark:bg-emerald-900/10 rounded-3xl p-8 border border-emerald-100 dark:border-emerald-800/50 shadow-sm relative">
                        <Quote size={40} className="absolute top-6 right-6 text-emerald-200 dark:text-emerald-800/50 rotate-180" />
                        <h2 className="text-xl font-bold text-emerald-900 dark:text-emerald-100 mb-4">Teaching Philosophy</h2>
                        <div className="text-lg italic text-emerald-800 dark:text-emerald-200 leading-relaxed relative z-10">
                            "{tutor.philosophy}"
                        </div>
                    </div>

                    {/* Educational Background */}
                    <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6">Educational Background</h2>
                        <div className="space-y-6">
                            {tutor.education.map((edu, idx) => (
                                <div key={idx} className="flex gap-4">
                                    <div className="mt-1">
                                        <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                                            <Award size={20} />
                                        </div>
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-slate-900 dark:text-white">{edu}</h3>
                                        <p className="text-slate-500 text-sm">Verified Credential</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Schedule Section */}
                    <div ref={scheduleRef} className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm scroll-mt-24">
                        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Schedule</h2>

                        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl flex gap-3 mb-6 items-start">
                            <Info size={20} className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                            <p className="text-sm text-blue-800 dark:text-blue-200 font-medium">
                                Choose the time for your first lesson. The timings are displayed in your local timezone.
                            </p>
                        </div>

                        <div className="flex p-1 bg-slate-100 dark:bg-slate-800 rounded-xl mb-6">
                            <button
                                onClick={() => setScheduleDuration(25)}
                                className={`flex-1 py-2.5 text-sm font-bold rounded-lg transition-all ${scheduleDuration === 25 ? 'bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'}`}
                            >
                                25 mins
                            </button>
                            <button
                                onClick={() => setScheduleDuration(50)}
                                className={`flex-1 py-2.5 text-sm font-bold rounded-lg transition-all ${scheduleDuration === 50 ? 'bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'}`}
                            >
                                50 mins
                            </button>
                        </div>

                        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 mb-6">
                            <div className="flex items-center gap-4 w-full sm:w-auto">
                                <div className="flex gap-1">
                                    <button 
                                        onClick={handlePrevWeek}
                                        className="p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-slate-500 dark:text-slate-400 transition-colors"
                                    >
                                        <ChevronLeft size={20}/>
                                    </button>
                                    <button 
                                        onClick={handleNextWeek}
                                        className="p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-slate-500 dark:text-slate-400 transition-colors"
                                    >
                                        <ChevronRight size={20}/>
                                    </button>
                                </div>
                                <span className="font-bold text-slate-900 dark:text-white text-lg sm:text-lg">
                                    {formatDateRange(scheduleDays[0], scheduleDays[6])}
                                </span>
                            </div>
                            <div className="w-full sm:w-auto relative">
                                <select className="w-full sm:w-auto bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg pl-3 pr-8 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 focus:outline-none appearance-none cursor-pointer hover:border-emerald-500 transition-colors shadow-sm">
                                    <option>Europe/Belgrade (GMT +1:00)</option>
                                    <option>America/New_York (GMT -5:00)</option>
                                    <option>Asia/Tokyo (GMT +9:00)</option>
                                </select>
                                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                            </div>
                        </div>

                        <div className="grid grid-cols-7 gap-2 mb-8 overflow-x-auto pb-2">
                            {scheduleDays.map((day, i) => (
                                <div key={i} className="min-w-[40px] flex flex-col">
                                    {/* Updated border color to match site palette (emerald) */}
                                    <div className={`text-center pb-3 border-b-2 ${i < 5 ? 'border-emerald-500' : 'border-transparent'} mb-3`}>
                                        <div className="text-xs text-slate-500 dark:text-slate-400 font-medium mb-1 uppercase">
                                            {day.toLocaleDateString('en-US', { weekday: 'short' })}
                                        </div>
                                        <div className="text-sm font-bold text-slate-900 dark:text-white">
                                            {day.getDate()}
                                        </div>
                                    </div>
                                    <div className="flex flex-col gap-2 items-center">
                                        {getSlotsForDay(i).map(time => (
                                            <button 
                                                key={time} 
                                                onClick={() => handleSlotClick(i, time)}
                                                className="text-xs font-bold text-slate-900 dark:text-white hover:text-emerald-600 dark:hover:text-emerald-400 underline decoration-2 decoration-slate-200 dark:decoration-slate-700 hover:decoration-emerald-500 underline-offset-4 py-1.5 rounded transition-all"
                                            >
                                                {time}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>

                        <button 
                            onClick={() => setIsScheduleExpanded(!isScheduleExpanded)}
                            className="w-full py-3.5 border border-slate-200 dark:border-slate-700 rounded-xl font-bold text-slate-900 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-sm"
                        >
                            {isScheduleExpanded ? 'Show less' : 'View full schedule'}
                        </button>
                    </div>

                    {/* Student Testimonials */}
                    <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Student Testimonials</h2>
                            <div className="text-sm text-slate-500">Based on {tutor.reviews} reviews</div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                             {/* Score */}
                             <div className="flex flex-col items-center justify-center p-6 bg-slate-50 dark:bg-slate-800/50 rounded-2xl">
                                 <div className="text-5xl font-bold text-slate-900 dark:text-white mb-2">{tutor.rating}</div>
                                 <div className="flex gap-1 text-amber-500 mb-2">
                                     {[1,2,3,4,5].map(i => <Star key={i} size={20} fill="currentColor" />)}
                                 </div>
                                 <p className="text-slate-500 font-medium">Overall Rating</p>
                             </div>

                             {/* Bars */}
                             <div className="space-y-2 flex flex-col justify-center">
                                 {[5,4,3,2,1].map((stars, i) => (
                                     <div key={stars} className="flex items-center gap-3">
                                         <span className="text-xs font-bold text-slate-500 w-3">{stars}</span>
                                         <div className="flex-1 h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                             <div 
                                                className="h-full bg-emerald-500 rounded-full" 
                                                style={{width: i === 0 ? '85%' : i === 1 ? '10%' : '2%'}}
                                             ></div>
                                         </div>
                                     </div>
                                 ))}
                             </div>
                        </div>

                        <div className="space-y-6">
                            {tutor.reviewsList.map(review => (
                                <div key={review.id} className="border-b border-slate-100 dark:border-slate-800 last:border-0 pb-6 last:pb-0">
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-600 flex items-center justify-center font-bold text-slate-600 dark:text-slate-300">
                                                {review.studentName.charAt(0)}
                                            </div>
                                            <div>
                                                <h4 className="font-semibold text-slate-900 dark:text-white text-sm">{review.studentName}</h4>
                                                <div className="flex text-amber-500 text-[10px] gap-0.5">
                                                    {[...Array(5)].map((_, i) => (
                                                        <Star key={i} size={10} fill={i < review.rating ? "currentColor" : "none"} className={i < review.rating ? "" : "text-slate-300 dark:text-slate-600"}/>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                        <span className="text-xs text-slate-400">{new Date(review.date).toLocaleDateString()}</span>
                                    </div>
                                    <p className="text-slate-600 dark:text-slate-300 text-sm mt-2">{review.comment}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>

                {/* --- RIGHT COLUMN: Sticky Sidebar (Conversion Engine) --- */}
                <div className="lg:col-span-4 relative">
                    <div className="sticky top-24 space-y-4">
                        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-xl shadow-slate-200/50 dark:shadow-black/20">
                            
                            {/* Header: Rating & Price - Recreated 3-col View */}
                            <div className="grid grid-cols-3 gap-4 mb-6 pb-6 border-b border-slate-100 dark:border-slate-800">
                                {/* Rating */}
                                <div>
                                    <div className="flex items-center gap-1 font-bold text-xl text-slate-900 dark:text-white">
                                        <Star size={20} className="fill-slate-900 dark:fill-white text-slate-900 dark:text-white" />
                                        {tutor.rating}
                                    </div>
                                    <div className="text-xs font-medium text-slate-500 mt-1">{tutor.reviews} reviews</div>
                                </div>
                                
                                {/* Lessons */}
                                <div>
                                    <div className="font-bold text-xl text-slate-900 dark:text-white">1,060</div>
                                    <div className="text-xs font-medium text-slate-500 mt-1">lessons</div>
                                </div>

                                {/* Price */}
                                <div>
                                    <div className="font-bold text-xl text-slate-900 dark:text-white">${tutor.hourlyRate}</div>
                                    <div className="text-xs font-medium text-slate-500 mt-1">50-min lesson</div>
                                </div>
                            </div>

                            {/* CTAs */}
                            <div className="space-y-3">
                                {isOwnProfile ? (
                                    <>
                                        <div className="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 p-3 rounded-lg text-sm text-center mb-2">
                                             You are viewing your own profile.
                                        </div>
                                        <button 
                                            onClick={onEdit}
                                            className="w-full bg-slate-900 dark:bg-slate-700 hover:bg-slate-800 text-white font-bold py-4 rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
                                        >
                                            <PenLine size={20} /> Edit Profile
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <button 
                                            onClick={scrollToSchedule}
                                            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white text-lg font-bold py-3 rounded-lg shadow-sm transition-all hover:-translate-y-0.5 flex items-center justify-center gap-2 border border-emerald-600 active:scale-[0.98]"
                                        >
                                            <Zap size={20} fill="currentColor" /> Book trial lesson
                                        </button>
                                        <button 
                                            onClick={() => onMessage(tutor)}
                                            className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-bold py-3 rounded-lg hover:border-emerald-500 hover:text-emerald-600 dark:hover:border-emerald-500 dark:hover:text-emerald-400 transition-colors flex items-center justify-center gap-2 active:scale-[0.98]"
                                        >
                                            <MessageCircle size={20} /> Send message
                                        </button>
                                        <button 
                                            onClick={(e) => onToggleSave(e, tutor.id)}
                                            className={`w-full bg-white dark:bg-slate-800 border ${isSaved ? 'border-emerald-500 text-emerald-600' : 'border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white'} font-bold py-3 rounded-lg hover:border-emerald-500 hover:text-emerald-600 dark:hover:border-emerald-500 dark:hover:text-emerald-400 transition-colors flex items-center justify-center gap-2 active:scale-[0.98]`}
                                        >
                                            <Heart size={20} className={isSaved ? "fill-current" : ""} /> {isSaved ? 'Saved to my list' : 'Save to my list'}
                                        </button>
                                        <button 
                                            onClick={handleShare}
                                            className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-bold py-3 rounded-lg hover:border-emerald-500 hover:text-emerald-600 dark:hover:border-emerald-500 dark:hover:text-emerald-400 transition-colors flex items-center justify-center gap-2 active:scale-[0.98]"
                                        >
                                            <Share size={20} /> Share tutor
                                        </button>
                                    </>
                                )}
                            </div>

                            {/* Free Switch Promo */}
                            {!isOwnProfile && (
                                <div className="mt-6 bg-[#E0F2F1] dark:bg-emerald-900/20 rounded-xl p-4 flex items-start gap-4">
                                    <div className="relative shrink-0 mt-1">
                                        <div className="w-12 h-12 rounded-lg overflow-hidden border-2 border-white dark:border-slate-700 shadow-sm relative z-10">
                                            <img src={tutor.imageUrl} alt="" className="w-full h-full object-cover"/>
                                        </div>
                                        {/* Abstract cards behind */}
                                        <div className="absolute top-0 left-0 w-full h-full bg-white dark:bg-slate-700 rounded-lg border border-slate-200 dark:border-slate-600 rotate-6 scale-90 -z-10"></div>
                                        <div className="absolute top-0 left-0 w-full h-full bg-white dark:bg-slate-700 rounded-lg border border-slate-200 dark:border-slate-600 -rotate-6 scale-90 -z-20"></div>
                                        
                                        <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[9px] font-bold px-1.5 py-0.5 rounded shadow-sm whitespace-nowrap z-20 text-slate-900 dark:text-white">
                                            Free switch
                                        </div>
                                    </div>
                                    <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                                        If {displayName} isn't a match, get 2 more free trials to find the right tutor.
                                    </p>
                                </div>
                            )}

                            {/* Popularity Stats */}
                            <div className="pt-6 space-y-4">
                                <div>
                                    <h4 className="flex items-center gap-2 font-bold text-slate-900 dark:text-white text-sm mb-1">
                                        <TrendingUpIcon className="text-slate-900 dark:text-white" /> Popular
                                    </h4>
                                    <p className="text-xs text-slate-600 dark:text-slate-400">
                                        2 new contacts and 10 lesson bookings in the last 48 hours
                                    </p>
                                </div>
                                
                                <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
                                    <Clock size={16} className="text-slate-900 dark:text-white" /> Usually responds in 2 hrs
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

            </div>

            {/* --- MOBILE STICKY FOOTER (Visible only on small screens) --- */}
            {!isOwnProfile && (
                <div className="lg:hidden fixed bottom-0 left-0 w-full bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 p-4 shadow-2xl z-50 pb-safe">
                    <div className="flex gap-4 items-center">
                        <div className="flex-1">
                            <p className="text-xs text-slate-500">Hourly Rate</p>
                            <p className="text-xl font-bold text-slate-900 dark:text-white">${tutor.hourlyRate}</p>
                        </div>
                        <button 
                            onClick={scrollToSchedule}
                            className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-8 py-3 rounded-lg shadow-sm border border-emerald-700 active:scale-95 transition-all"
                        >
                            Book Now
                        </button>
                    </div>
                </div>
            )}
            
            {isOwnProfile && (
                <div className="lg:hidden fixed bottom-0 left-0 w-full bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 p-4 shadow-2xl z-50 pb-safe">
                    <button 
                        onClick={onEdit}
                        className="w-full bg-slate-900 dark:bg-slate-700 text-white font-bold py-3 rounded-xl shadow-lg"
                    >
                        Edit Profile
                    </button>
                </div>
            )}
        </div>
    );
};

// Helper Icon for "Popular"
const TrendingUpIcon = ({className}: {className?: string}) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
        <polyline points="17 6 23 6 23 12"></polyline>
    </svg>
);
