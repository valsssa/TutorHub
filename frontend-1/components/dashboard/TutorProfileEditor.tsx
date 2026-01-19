
import React, { useState, useRef, useEffect } from 'react';
import { Tutor } from '../../domain/types';
import { Save, X, Youtube, Move, Minus, Plus, User, DollarSign, Globe, BookOpen, MessageSquare, Briefcase, Camera, Video, Sparkles, Layout, Upload } from 'lucide-react';
import { Modal } from '../shared/UI';

interface TutorProfileEditorProps {
    tutor: Tutor;
    onSave: (updatedTutor: Tutor) => void;
    onCancel: () => void;
}

export const TutorProfileEditor: React.FC<TutorProfileEditorProps> = ({ tutor, onSave, onCancel }) => {
    const [formData, setFormData] = useState<Tutor>({ ...tutor });
    const [showPhotoModal, setShowPhotoModal] = useState(false);
    const [zoom, setZoom] = useState(1);
    const [activeTab, setActiveTab] = useState('basic');
    
    // Local state for array inputs
    const [topicsString, setTopicsString] = useState(tutor.topics.join(', '));
    const [languagesString, setLanguagesString] = useState(tutor.languages?.join(', ') || '');
    
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (showPhotoModal) setZoom(1);
    }, [showPhotoModal]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: name === 'hourlyRate' ? parseFloat(value) || 0 : value
        }));
    };

    const handleTopicsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setTopicsString(e.target.value);
        const topics = e.target.value.split(',').map(t => t.trim()).filter(Boolean);
        setFormData(prev => ({ ...prev, topics }));
    };

    const handleLanguagesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setLanguagesString(e.target.value);
        const languages = e.target.value.split(',').map(t => t.trim()).filter(Boolean);
        setFormData(prev => ({ ...prev, languages }));
    };
    
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) {
                alert("File size exceeds 5MB");
                return;
            }
            const reader = new FileReader();
            reader.onloadend = () => {
                setFormData(prev => ({ ...prev, imageUrl: reader.result as string }));
                setShowPhotoModal(true);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(formData);
    };

    const tabs = [
        { id: 'basic', label: 'Basic Info', icon: User, description: 'Name, title, and photo' },
        { id: 'about', label: 'About & Bio', icon: BookOpen, description: 'Biography and philosophy' },
        { id: 'expertise', label: 'Expertise', icon: Sparkles, description: 'Rates, subjects, languages' },
        { id: 'media', label: 'Media', icon: Video, description: 'Introduction video' },
    ];

    return (
        <form onSubmit={handleSubmit} className="flex flex-col h-full bg-slate-50 dark:bg-slate-950">
            {/* Header */}
            <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 py-4 sm:px-6 lg:px-8 flex items-center justify-between sticky top-0 z-20">
                <div>
                    <h1 className="text-xl font-bold text-slate-900 dark:text-white">Edit Profile</h1>
                    <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">Update your public tutor profile</p>
                </div>
                <div className="flex gap-3">
                    <button 
                        type="button" 
                        onClick={onCancel}
                        className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                    >
                        Cancel
                    </button>
                    <button 
                        type="submit"
                        className="px-6 py-2 bg-emerald-600 text-white text-sm font-bold rounded-lg hover:bg-emerald-500 transition-all shadow-md shadow-emerald-500/20 flex items-center gap-2"
                    >
                        <Save size={16} /> Save Changes
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-hidden flex flex-col lg:flex-row max-w-7xl mx-auto w-full">
                
                {/* Sidebar Navigation */}
                <div className="lg:w-72 bg-white dark:bg-slate-900 lg:border-r border-b lg:border-b-0 border-slate-200 dark:border-slate-800 flex-shrink-0 z-10 overflow-x-auto lg:overflow-visible">
                    <nav className="p-2 lg:p-4 flex lg:flex-col gap-1 lg:gap-2 min-w-max lg:min-w-0">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                type="button"
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all relative ${
                                    activeTab === tab.id 
                                        ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 font-bold' 
                                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
                                }`}
                            >
                                <tab.icon size={20} className={activeTab === tab.id ? 'text-emerald-500' : 'opacity-70'} />
                                <div>
                                    <div className="text-sm">{tab.label}</div>
                                    <div className="text-[10px] opacity-70 font-normal hidden lg:block">{tab.description}</div>
                                </div>
                                {activeTab === tab.id && (
                                    <div className="absolute left-0 top-1/2 -translate-y-1/2 h-8 w-1 bg-emerald-500 rounded-r-full hidden lg:block" />
                                )}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Main Content Area */}
                <div className="flex-1 overflow-y-auto p-4 sm:p-8">
                    <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
                        
                        {/* BASIC INFO TAB */}
                        {activeTab === 'basic' && (
                            <div className="space-y-8">
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-1">Basic Information</h2>
                                    <p className="text-sm text-slate-500">This information will be displayed on your public profile card.</p>
                                </div>

                                {/* Photo Upload */}
                                <div className="flex items-center gap-6 p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
                                    <div className="relative group shrink-0">
                                        <div className="w-24 h-24 rounded-full overflow-hidden border-2 border-slate-200 dark:border-slate-700">
                                            <img 
                                                src={formData.imageUrl} 
                                                alt="Profile" 
                                                className="w-full h-full object-cover"
                                                onError={(e) => { (e.target as HTMLImageElement).src = 'https://via.placeholder.com/150?text=No+Img' }} 
                                            />
                                        </div>
                                        <button 
                                            type="button"
                                            onClick={() => fileInputRef.current?.click()}
                                            className="absolute bottom-0 right-0 p-2 bg-emerald-600 text-white rounded-full shadow-lg hover:bg-emerald-500 transition-transform hover:scale-105"
                                        >
                                            <Camera size={14} />
                                        </button>
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="font-bold text-slate-900 dark:text-white mb-1">Profile Photo</h3>
                                        <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
                                            Make sure your face is clearly visible. Professional photos build trust.
                                        </p>
                                        <div className="flex gap-3 items-center">
                                            <button 
                                                type="button"
                                                onClick={() => setShowPhotoModal(true)}
                                                className="text-sm text-slate-900 dark:text-white underline decoration-slate-900 dark:decoration-white font-medium hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                                            >
                                                Edit
                                            </button>
                                            <span className="text-slate-300 dark:text-slate-700">|</span>
                                            <button 
                                                type="button"
                                                onClick={() => fileInputRef.current?.click()}
                                                className="text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:underline"
                                            >
                                                Upload New
                                            </button>
                                            {/* Hidden Input */}
                                            <input 
                                                type="file" 
                                                ref={fileInputRef}
                                                onChange={handleFileChange}
                                                accept="image/png, image/jpeg"
                                                className="hidden"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Display Name</label>
                                        <div className="relative">
                                            <User size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                            <input 
                                                type="text" 
                                                name="name" 
                                                value={formData.name} 
                                                onChange={handleChange}
                                                className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                                placeholder="e.g. Dr. Elena Vance"
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Professional Title</label>
                                        <div className="relative">
                                            <Briefcase size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                            <input 
                                                type="text" 
                                                name="title" 
                                                value={formData.title} 
                                                onChange={handleChange}
                                                className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                                placeholder="e.g. PhD in Astrophysics"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ABOUT TAB */}
                        {activeTab === 'about' && (
                            <div className="space-y-8">
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-1">About & Philosophy</h2>
                                    <p className="text-sm text-slate-500">Share your background and teaching style with students.</p>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300 flex justify-between">
                                        Biography
                                        <span className="text-xs font-normal text-slate-400">Markdown supported</span>
                                    </label>
                                    <textarea 
                                        name="bio" 
                                        value={formData.bio} 
                                        onChange={handleChange}
                                        rows={8}
                                        className="w-full p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all leading-relaxed resize-y"
                                        placeholder="Tell students about your experience..."
                                    />
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Teaching Philosophy</label>
                                    <div className="relative">
                                        <MessageSquare size={18} className="absolute top-3.5 left-3.5 text-slate-400" />
                                        <textarea 
                                            name="philosophy" 
                                            value={formData.philosophy} 
                                            onChange={handleChange}
                                            rows={4}
                                            className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all italic resize-y"
                                            placeholder="What is your approach to teaching?"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* EXPERTISE TAB */}
                        {activeTab === 'expertise' && (
                            <div className="space-y-8">
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-1">Expertise & Rates</h2>
                                    <p className="text-sm text-slate-500">Define what you teach and how much you charge.</p>
                                </div>

                                <div className="p-6 bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-900/30 rounded-2xl flex flex-col md:flex-row gap-6 items-start md:items-center">
                                    <div className="flex-1">
                                        <label className="text-xs font-bold text-emerald-800 dark:text-emerald-300 uppercase tracking-wide mb-2 block">Hourly Rate</label>
                                        <div className="relative max-w-[200px]">
                                            <DollarSign size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-emerald-600 dark:text-emerald-400" />
                                            <input 
                                                type="number" 
                                                name="hourlyRate" 
                                                value={formData.hourlyRate} 
                                                onChange={handleChange}
                                                min="0"
                                                step="1"
                                                className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-900 border border-emerald-200 dark:border-emerald-800 rounded-xl text-lg font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all"
                                            />
                                        </div>
                                    </div>
                                    <div className="text-sm text-emerald-800 dark:text-emerald-200 bg-white/50 dark:bg-black/20 p-4 rounded-xl flex-1">
                                        <p><strong>Note:</strong> EduConnect charges a standard 15% platform fee on all transactions.</p>
                                        <p className="mt-1">You will receive approx <span className="font-bold">${(formData.hourlyRate * 0.85).toFixed(2)}</span> per hour.</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Native Language</label>
                                        <div className="relative">
                                            <Globe size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                            <input 
                                                type="text" 
                                                name="nativeLanguage" 
                                                value={formData.nativeLanguage || ''} 
                                                onChange={handleChange}
                                                className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                                placeholder="e.g. English"
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Subjects</label>
                                        <div className="relative">
                                            <Layout size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                            <input 
                                                type="text" 
                                                name="topics" 
                                                value={topicsString} 
                                                onChange={handleTopicsChange}
                                                className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                                placeholder="Math, Physics (comma separated)"
                                            />
                                        </div>
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {formData.topics.map(t => (
                                                <span key={t} className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs rounded-md border border-slate-200 dark:border-slate-700">{t}</span>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Also Speaks</label>
                                        <div className="relative">
                                            <MessageSquare size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                            <input 
                                                type="text" 
                                                name="languages" 
                                                value={languagesString} 
                                                onChange={handleLanguagesChange}
                                                className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                                placeholder="English, Spanish (comma separated)"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* MEDIA TAB */}
                        {activeTab === 'media' && (
                            <div className="space-y-8">
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-1">Media & Introduction</h2>
                                    <p className="text-sm text-slate-500">A video introduction significantly increases booking rates.</p>
                                </div>

                                <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
                                    <div className="space-y-4">
                                        <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Video URL</label>
                                        <div className="relative">
                                            <Youtube size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-red-500" />
                                            <input 
                                                type="url" 
                                                name="videoUrl" 
                                                value={formData.videoUrl || ''} 
                                                onChange={handleChange}
                                                className="w-full pl-10 pr-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                                placeholder="https://www.youtube.com/watch?v=..."
                                            />
                                        </div>
                                        <p className="text-xs text-slate-500">Supported platforms: YouTube, Vimeo</p>
                                    </div>

                                    {formData.videoUrl && (
                                        <div className="mt-6 aspect-video bg-black rounded-xl overflow-hidden relative group flex items-center justify-center">
                                            {/* Mock Embed */}
                                            <div className="text-white flex flex-col items-center gap-2">
                                                <Video size={32} className="opacity-50" />
                                                <span className="text-sm font-medium opacity-70">Preview not available in editor</span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                    </div>
                </div>
            </div>

            {/* Sticky Action Footer */}
            <div className="sticky bottom-0 z-20 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 px-6 py-4 flex justify-end gap-3 safe-area-pb shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
                <button 
                    type="button" 
                    onClick={onCancel}
                    className="px-6 py-2.5 text-sm font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors flex items-center gap-2"
                >
                    <X size={18} /> Cancel
                </button>
                <button 
                    type="submit"
                    className="px-8 py-2.5 bg-emerald-600 text-white text-sm font-bold rounded-xl hover:bg-emerald-500 transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2 active:scale-95"
                >
                    <Save size={18} /> Save Profile
                </button>
            </div>

            {/* Photo Crop Modal */}
            <Modal isOpen={showPhotoModal} onClose={() => setShowPhotoModal(false)} title="Adjust Profile Picture" maxWidth="max-w-xl">
                <div className="flex flex-col gap-6 p-2">
                    <div className="bg-slate-950 rounded-2xl overflow-hidden relative aspect-square w-full max-w-sm mx-auto shadow-inner border border-slate-800">
                        <img 
                            src={formData.imageUrl} 
                            className="w-full h-full object-cover opacity-90 transition-transform duration-100 origin-center" 
                            style={{ transform: `scale(${zoom})` }}
                            alt="Crop target"
                        />
                        <div className="absolute inset-0 pointer-events-none">
                            <div className="absolute inset-0 bg-black/50 mask-circle"></div>
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 border-2 border-white rounded-full shadow-[0_0_0_9999px_rgba(0,0,0,0.5)]"></div>
                        </div>
                        <div className="absolute top-4 right-4 bg-black/60 text-white text-xs px-2 py-1 rounded backdrop-blur-md pointer-events-none flex items-center gap-1">
                            <Move size={12} /> Drag to adjust
                        </div>
                    </div>
                    
                    <div className="space-y-4">
                        <div className="flex items-center gap-4 bg-slate-100 dark:bg-slate-800 p-3 rounded-xl">
                            <Minus size={18} className="text-slate-500 cursor-pointer hover:text-emerald-500" onClick={() => setZoom(z => Math.max(1, z - 0.1))} />
                            <input 
                                type="range" 
                                min="1" 
                                max="3" 
                                step="0.1" 
                                value={zoom}
                                onChange={(e) => setZoom(parseFloat(e.target.value))}
                                className="flex-1 h-2 bg-slate-300 dark:bg-slate-600 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                            />
                            <Plus size={18} className="text-slate-500 cursor-pointer hover:text-emerald-500" onClick={() => setZoom(z => Math.min(3, z + 0.1))} />
                        </div>

                        <div className="flex items-center justify-between">
                            <button 
                                type="button" 
                                onClick={() => fileInputRef.current?.click()}
                                className="flex items-center gap-2 text-sm font-bold text-emerald-600 dark:text-emerald-400 hover:underline"
                            >
                                <Upload size={16} /> Upload New Photo
                            </button>
                        </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                        <button 
                            type="button"
                            onClick={() => setShowPhotoModal(false)}
                            className="px-5 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                        >
                            Cancel
                        </button>
                        <button 
                            type="button"
                            onClick={() => setShowPhotoModal(false)}
                            className="px-8 py-2.5 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-500 transition-colors shadow-lg shadow-emerald-500/20"
                        >
                            Apply
                        </button>
                    </div>
                </div>
            </Modal>
        </form>
    );
};
