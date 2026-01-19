
import React, { useState } from 'react';
import { Search, ChevronDown, SlidersHorizontal, X, Check, Sun, Moon, Sunrise, Sunset, Globe } from 'lucide-react';
import { Tutor, FilterState } from '../../types';
import { SUBJECTS, SORT_OPTIONS } from '../../constants';
import { TutorCard } from './TutorCard';

interface MarketplacePageProps {
    tutors: Tutor[];
    savedTutorIds: string[];
    filters: FilterState;
    setFilters: React.Dispatch<React.SetStateAction<FilterState>>;
    onSearch: (e: React.FormEvent) => void;
    onViewProfile: (tutor: Tutor) => void;
    onToggleSave: (e: React.MouseEvent, id: string) => void;
    onBook: (e: React.MouseEvent, tutor: Tutor) => void;
    onQuickBook: (e: React.MouseEvent, tutor: Tutor) => void;
    onSlotBook: (e: React.MouseEvent, tutor: Tutor, slot: string) => void;
    onMessage: (e: React.MouseEvent, tutor: Tutor) => void;
    aiLoading: boolean;
    onOpenFilter: (filterType: string) => void;
}

const COUNTRY_FLAGS: Record<string, string> = {
    'United States': '🇺🇸',
    'United Kingdom': '🇬🇧',
    'Canada': '🇨🇦',
    'Australia': '🇦🇺',
    'Germany': '🇩🇪',
    'France': '🇫🇷',
    'Serbia': '🇷🇸',
    'Any country': '🌍'
};

const DISPLAY_COUNTRIES = ['Any country', 'Serbia', 'United States', 'United Kingdom', 'Australia', 'Canada', 'Germany', 'France'];

const LANGUAGES_LIST = [
    'Serbian', 'Russian', 'English', 'Serbo-Croatian', 
    'Chinese (Mandarin)', 'French', 'German', 'Spanish', 'Italian', 'Portuguese', 'Japanese', 'Korean'
];

const SUGGESTED_SUBJECTS = [
    'English', 'Spanish', 'French', 'German', 'Japanese', 'Italian', 'Korean', 'Arabic', 'Chinese (Mandarin)', 
    'Mathematics', 'Physics', 'Chemistry', 'Biology', 'History', 'Computer Science', 'Literature', 'Economics'
];

const POPULAR_LANGUAGES = ['Serbian', 'Russian', 'English', 'Serbo-Croatian', 'Chinese (Mandarin)'];

const TIME_CATEGORIES = [
    {
        label: 'Daytime',
        slots: [
            { id: '9-12', label: '9-12', icon: Sun },
            { id: '12-15', label: '12-15', icon: Sun },
            { id: '15-18', label: '15-18', icon: Sun },
        ]
    },
    {
        label: 'Evening and night',
        slots: [
            { id: '18-21', label: '18-21', icon: Sunset },
            { id: '21-24', label: '21-24', icon: Moon },
            { id: '0-3', label: '0-3', icon: Moon },
        ]
    },
    {
        label: 'Morning',
        slots: [
            { id: '3-6', label: '3-6', icon: Moon },
            { id: '6-9', label: '6-9', icon: Sunrise },
        ]
    }
];

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export const MarketplacePage: React.FC<MarketplacePageProps> = ({ 
    tutors, savedTutorIds, filters, setFilters, onSearch, 
    onViewProfile, onToggleSave, onBook, onQuickBook, onSlotBook, onMessage, aiLoading, onOpenFilter
}) => {
  
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [countrySearch, setCountrySearch] = useState('');
  const [languageSearch, setLanguageSearch] = useState('');
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
    
  const clearFilters = () => {
      setFilters({
          searchQuery: '',
          maxPrice: 200,
          subject: '',
          minRating: 0,
          country: 'Any country',
          availability: 'Any time',
          sort: 'Our top picks',
          nativeSpeaker: false
      });
      setSelectedLanguages([]);
  };

  const handleInputChange = (field: keyof FilterState, value: any) => {
      setFilters(prev => ({ ...prev, [field]: value }));
  };

  const filteredCountries = DISPLAY_COUNTRIES.filter(c => 
      c.toLowerCase().includes(countrySearch.toLowerCase())
  );

  const toggleLanguage = (lang: string) => {
      setSelectedLanguages(prev => 
          prev.includes(lang) ? prev.filter(l => l !== lang) : [...prev, lang]
      );
  };

  const getFilteredLanguages = () => {
      if (!languageSearch) return LANGUAGES_LIST;
      return LANGUAGES_LIST.filter(l => l.toLowerCase().includes(languageSearch.toLowerCase()));
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      
      {/* --- Filter Section --- */}
      <div className="mb-8 space-y-4">
          
          {/* Row 1: Primary Filters (White Boxes) */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              
              {/* Subject Input */}
              <div className="relative group">
                   <div 
                        className={`bg-white dark:bg-slate-900 border ${activeDropdown === 'subject' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-200 dark:border-slate-700'} rounded-xl px-4 py-3 hover:border-slate-300 dark:hover:border-slate-600 transition-all cursor-text relative z-20 h-full flex flex-col justify-center`}
                        onClick={() => document.getElementById('subject-input')?.focus()}
                   >
                       <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-0.5">I want to learn</label>
                       <div className="flex items-center">
                           <input 
                                id="subject-input"
                                type="text" 
                                value={filters.subject}
                                onChange={(e) => {
                                    handleInputChange('subject', e.target.value);
                                    if (activeDropdown !== 'subject') setActiveDropdown('subject');
                                }}
                                onFocus={() => setActiveDropdown('subject')}
                                placeholder="Type to search..."
                                className="w-full bg-transparent border-none text-slate-900 dark:text-white font-bold text-sm focus:ring-0 p-0 placeholder-slate-300"
                                autoComplete="off"
                           />
                           {filters.subject ? (
                               <button 
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleInputChange('subject', '');
                                        document.getElementById('subject-input')?.focus();
                                    }} 
                                    className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1"
                               >
                                   <X size={16} />
                               </button>
                           ) : (
                               <ChevronDown size={16} className="text-slate-400" />
                           )}
                       </div>
                   </div>

                   {activeDropdown === 'subject' && (
                        <>
                            <div className="fixed inset-0 z-10" onClick={() => setActiveDropdown(null)} />
                            <div className="absolute top-[calc(100%+8px)] left-0 right-0 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-30 animate-in fade-in zoom-in-95 duration-200 max-h-[350px] overflow-y-auto py-2">
                                {(() => {
                                    const filtered = SUGGESTED_SUBJECTS.filter(s => s.toLowerCase().includes(filters.subject.toLowerCase()));
                                    return filtered.length > 0 ? (
                                        filtered.map(subject => (
                                            <button
                                                key={subject}
                                                onClick={() => {
                                                    handleInputChange('subject', subject);
                                                    setActiveDropdown(null);
                                                }}
                                                className="w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-sm font-medium text-slate-700 dark:text-slate-200"
                                            >
                                                {subject}
                                            </button>
                                        ))
                                    ) : (
                                        <div className="px-4 py-3 text-sm text-slate-400 italic">No matching subjects</div>
                                    );
                                })()}
                            </div>
                        </>
                   )}
              </div>

              {/* Price Input */}
              <div className="relative">
                  <button 
                      onClick={() => setActiveDropdown(activeDropdown === 'price' ? null : 'price')}
                      className={`w-full h-full bg-white dark:bg-slate-900 border ${activeDropdown === 'price' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-200 dark:border-slate-700'} rounded-xl px-4 py-3 hover:border-slate-300 dark:hover:border-slate-600 transition-all cursor-pointer text-left relative z-20 flex flex-col justify-center`}
                  >
                      <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-0.5">Price per lesson</label>
                      <div className="flex items-center justify-between w-full">
                          <span className="text-slate-900 dark:text-white font-bold text-sm truncate">
                              {filters.maxPrice < 200 ? `$1 - $${filters.maxPrice}` : '$Any price'}
                          </span>
                          <ChevronDown size={16} className={`text-slate-400 transition-transform duration-200 ${activeDropdown === 'price' ? 'rotate-180' : ''}`} />
                      </div>
                  </button>

                  {activeDropdown === 'price' && (
                      <>
                        <div className="fixed inset-0 z-10" onClick={() => setActiveDropdown(null)} />
                        <div className="absolute top-[calc(100%+8px)] left-0 right-0 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl p-6 z-30 animate-in fade-in zoom-in-95 duration-200">
                             <div className="text-center font-bold text-2xl text-slate-900 dark:text-white mb-6">
                                {filters.maxPrice < 200 ? `$1 - $${filters.maxPrice}` : 'Any price'}
                             </div>
                             
                             <div className="relative h-8 flex items-center mb-2 px-2">
                                 <div className="absolute left-0 right-0 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
                                 <div 
                                    className="absolute left-0 h-1.5 bg-emerald-500 rounded-full" 
                                    style={{ width: `${(filters.maxPrice / 200) * 100}%` }}
                                 ></div>
                                 <input 
                                    type="range"
                                    min="10" max="200" step="5"
                                    value={filters.maxPrice}
                                    onChange={(e) => handleInputChange('maxPrice', Number(e.target.value))}
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
                                 />
                                 <div 
                                    className="absolute w-6 h-6 bg-white border-2 border-emerald-500 rounded-full shadow-sm z-10 pointer-events-none transition-transform"
                                    style={{ 
                                        left: `calc(${(filters.maxPrice / 200) * 100}% - 12px)` 
                                    }}
                                 ></div>
                             </div>
                             
                             <div className="flex justify-between text-xs text-slate-500 font-medium mt-2">
                                <span>$10</span>
                                <span>$200+</span>
                             </div>
                        </div>
                      </>
                  )}
              </div>

               {/* Country Input */}
               <div className="relative">
                  <button 
                      onClick={() => setActiveDropdown(activeDropdown === 'country' ? null : 'country')}
                      className={`w-full h-full bg-white dark:bg-slate-900 border ${activeDropdown === 'country' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-200 dark:border-slate-700'} rounded-xl px-4 py-3 hover:border-slate-300 dark:hover:border-slate-600 transition-all cursor-pointer text-left relative z-20 flex flex-col justify-center`}
                  >
                       <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-0.5">Country of birth</label>
                       <div className="flex items-center justify-between w-full">
                          <span className="text-slate-900 dark:text-white font-bold text-sm truncate pr-2">
                              {filters.country}
                          </span>
                          <ChevronDown size={16} className={`text-slate-400 transition-transform duration-200 ${activeDropdown === 'country' ? 'rotate-180' : ''}`} />
                      </div>
                  </button>

                  {activeDropdown === 'country' && (
                      <>
                        <div className="fixed inset-0 z-10" onClick={() => setActiveDropdown(null)} />
                        <div className="absolute top-[calc(100%+8px)] left-0 w-[300px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-30 animate-in fade-in zoom-in-95 duration-200 overflow-hidden">
                             <div className="p-3 border-b border-slate-100 dark:border-slate-800">
                                <div className="relative">
                                    <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
                                    <input 
                                        type="text" 
                                        placeholder="Type to search..."
                                        value={countrySearch}
                                        onChange={(e) => setCountrySearch(e.target.value)}
                                        className="w-full pl-9 pr-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:border-emerald-500 transition-colors"
                                        autoFocus
                                    />
                                </div>
                             </div>

                             <div className="max-h-[300px] overflow-y-auto">
                                 {filteredCountries.map(country => {
                                     const isSelected = filters.country === country;
                                     return (
                                         <button
                                             key={country}
                                             onClick={() => {
                                                 const newValue = isSelected ? 'Any country' : country;
                                                 handleInputChange('country', newValue);
                                                 setActiveDropdown(null);
                                             }}
                                             className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors border-b border-slate-100 dark:border-slate-800 last:border-0"
                                         >
                                             <div className="flex items-center gap-3">
                                                 <span className="text-lg">{COUNTRY_FLAGS[country] || '🌍'}</span>
                                                 <span className="text-sm text-slate-700 dark:text-slate-200 font-medium">{country}</span>
                                             </div>
                                             {isSelected && <Check size={16} className="text-emerald-500" />}
                                         </button>
                                     );
                                 })}
                             </div>
                        </div>
                      </>
                  )}
              </div>

              {/* Availability Input */}
              <div className="relative">
                  <button 
                      onClick={() => setActiveDropdown(activeDropdown === 'availability' ? null : 'availability')}
                      className={`w-full h-full bg-white dark:bg-slate-900 border ${activeDropdown === 'availability' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-200 dark:border-slate-700'} rounded-xl px-4 py-3 hover:border-slate-300 dark:hover:border-slate-600 transition-all cursor-pointer text-left relative z-20 flex flex-col justify-center`}
                  >
                       <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-0.5">I'm available</label>
                       <div className="flex items-center justify-between w-full">
                          <span className="text-slate-900 dark:text-white font-bold text-sm truncate pr-2">
                              {filters.availability}
                          </span>
                          <ChevronDown size={16} className={`text-slate-400 transition-transform duration-200 ${activeDropdown === 'availability' ? 'rotate-180' : ''}`} />
                      </div>
                  </button>

                  {activeDropdown === 'availability' && (
                      <>
                        <div className="fixed inset-0 z-10" onClick={() => setActiveDropdown(null)} />
                        <div className="absolute top-[calc(100%+8px)] right-0 w-[320px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-30 animate-in fade-in zoom-in-95 duration-200 p-5 overflow-y-auto max-h-[500px]">
                             
                             <div className="mb-4 font-bold text-slate-900 dark:text-white text-sm">Times</div>
                             
                             {TIME_CATEGORIES.map((category) => (
                                 <div key={category.label} className="mb-4 last:mb-0">
                                     <div className="text-xs text-slate-500 dark:text-slate-400 mb-2">{category.label}</div>
                                     <div className="grid grid-cols-3 gap-2">
                                         {category.slots.map(slot => {
                                             const isSelected = filters.availability.includes(slot.id);
                                             const Icon = slot.icon;
                                             return (
                                                 <button
                                                     key={slot.id}
                                                     onClick={() => {
                                                        const newValue = isSelected ? 'Any time' : slot.id;
                                                        handleInputChange('availability', newValue);
                                                     }}
                                                     className={`flex flex-col items-center justify-center py-2 px-1 rounded-lg border transition-all ${
                                                         isSelected 
                                                            ? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-500 text-emerald-700 dark:text-emerald-400' 
                                                            : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-slate-300 dark:hover:border-slate-600'
                                                     }`}
                                                 >
                                                     <Icon size={18} className="mb-1" />
                                                     <span className="text-xs font-medium">{slot.label}</span>
                                                 </button>
                                             );
                                         })}
                                     </div>
                                 </div>
                             ))}

                             <div className="mt-6 mb-2 font-bold text-slate-900 dark:text-white text-sm">Days</div>
                             <div className="grid grid-cols-4 gap-2">
                                 {DAYS.map(day => {
                                     const isSelected = filters.availability.includes(day);
                                     return (
                                        <button
                                            key={day}
                                            onClick={() => {
                                                const newValue = isSelected ? 'Any time' : day;
                                                handleInputChange('availability', newValue);
                                            }}
                                            className={`py-2 rounded-lg border text-xs font-bold transition-all ${
                                                 isSelected 
                                                    ? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-500 text-emerald-700 dark:text-emerald-400' 
                                                    : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-slate-300 dark:hover:border-slate-600'
                                             }`}
                                        >
                                            {day}
                                        </button>
                                     )
                                 })}
                             </div>
                        </div>
                      </>
                  )}
              </div>
          </div>

          {/* Row 2: Secondary Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
              <button 
                onClick={() => onOpenFilter('Personalization')}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-6 py-3 rounded-xl flex items-center gap-2 transition-colors shadow-lg shadow-emerald-500/20 active:scale-95 whitespace-nowrap"
              >
                  <SlidersHorizontal size={18} />
                  Personalize my results
              </button>

               {/* Also Speaks Dropdown */}
               <div className="relative">
                  <button 
                    onClick={() => setActiveDropdown(activeDropdown === 'languages' ? null : 'languages')}
                    className={`h-full bg-white dark:bg-slate-900 border ${activeDropdown === 'languages' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-200 dark:border-slate-700'} text-slate-700 dark:text-slate-300 font-medium px-4 py-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 whitespace-nowrap z-20 relative`}
                  >
                      Also speaks <ChevronDown size={16} className={`text-slate-400 transition-transform duration-200 ${activeDropdown === 'languages' ? 'rotate-180' : ''}`} />
                  </button>

                  {activeDropdown === 'languages' && (
                      <>
                        <div className="fixed inset-0 z-10" onClick={() => setActiveDropdown(null)} />
                        <div className="absolute top-[calc(100%+8px)] left-0 w-[280px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-30 animate-in fade-in zoom-in-95 duration-200 overflow-hidden">
                             {/* Search Input */}
                             <div className="p-3">
                                <div className="relative">
                                    <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
                                    <input 
                                        type="text" 
                                        placeholder="Type to search..."
                                        value={languageSearch}
                                        onChange={(e) => setLanguageSearch(e.target.value)}
                                        className="w-full pl-9 pr-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:border-emerald-500 transition-colors"
                                        autoFocus
                                    />
                                </div>
                             </div>

                             <div className="max-h-[300px] overflow-y-auto">
                                 {languageSearch ? (
                                     getFilteredLanguages().map(lang => (
                                         <button
                                            key={lang}
                                            onClick={() => toggleLanguage(lang)}
                                            className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer border-b border-slate-50 dark:border-slate-800/50 last:border-0"
                                        >
                                            <span className="text-sm text-slate-700 dark:text-slate-300">{lang}</span>
                                            <div className={`w-5 h-5 rounded border ${selectedLanguages.includes(lang) ? 'bg-emerald-500 border-emerald-500' : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800'} flex items-center justify-center transition-colors`}>
                                                {selectedLanguages.includes(lang) && <Check size={14} className="text-white" />}
                                            </div>
                                        </button>
                                     ))
                                 ) : (
                                     <>
                                         <div className="px-4 py-2 text-xs font-bold text-slate-900 dark:text-white">Popular</div>
                                         {POPULAR_LANGUAGES.map(lang => (
                                            <button
                                                key={lang}
                                                onClick={() => toggleLanguage(lang)}
                                                className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer border-b border-slate-50 dark:border-slate-800/50 last:border-0"
                                            >
                                                <span className="text-sm text-slate-700 dark:text-slate-300">{lang}</span>
                                                <div className={`w-5 h-5 rounded border ${selectedLanguages.includes(lang) ? 'bg-emerald-500 border-emerald-500' : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800'} flex items-center justify-center transition-colors`}>
                                                    {selectedLanguages.includes(lang) && <Check size={14} className="text-white" />}
                                                </div>
                                            </button>
                                         ))}
                                     </>
                                 )}
                             </div>
                        </div>
                      </>
                  )}
               </div>

                {/* Native Speaker Dropdown */}
                <div className="relative">
                  <button 
                    onClick={() => setActiveDropdown(activeDropdown === 'native' ? null : 'native')}
                    className={`h-full bg-white dark:bg-slate-900 border ${activeDropdown === 'native' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-200 dark:border-slate-700'} ${filters.nativeSpeaker ? 'text-emerald-700 bg-emerald-50 border-emerald-500' : 'text-slate-700 dark:text-slate-300'} font-medium px-4 py-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 whitespace-nowrap z-20 relative`}
                  >
                      Native speaker <ChevronDown size={16} className={`text-slate-400 transition-transform duration-200 ${activeDropdown === 'native' ? 'rotate-180' : ''}`} />
                  </button>

                  {activeDropdown === 'native' && (
                      <>
                        <div className="fixed inset-0 z-10" onClick={() => setActiveDropdown(null)} />
                        <div className="absolute top-[calc(100%+8px)] left-0 w-[300px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-30 animate-in fade-in zoom-in-95 duration-200 p-5">
                            <div className="flex items-start justify-between mb-3">
                                <h3 className="font-bold text-slate-900 dark:text-white text-sm pr-4">
                                    Only {filters.subject || 'English'} native speakers
                                </h3>
                                <button 
                                    onClick={() => handleInputChange('nativeSpeaker', !filters.nativeSpeaker)}
                                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${filters.nativeSpeaker ? 'bg-emerald-500' : 'bg-slate-200 dark:bg-slate-700'}`}
                                >
                                    <span 
                                        aria-hidden="true" 
                                        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${filters.nativeSpeaker ? 'translate-x-5' : 'translate-x-0'}`} 
                                    />
                                </button>
                            </div>
                            <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                                We will only show tutors who teach in their native language
                            </p>
                        </div>
                      </>
                  )}
               </div>

               {/* Keyword Search */}
               <div className="flex-1 relative group">
                  <input 
                      type="text"
                      value={filters.searchQuery}
                      onChange={(e) => handleInputChange('searchQuery', e.target.value)}
                      placeholder="Search by name or keyword"
                      className="w-full h-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl py-3 pl-10 pr-4 text-slate-900 dark:text-white focus:outline-none focus:border-slate-400 dark:focus:border-slate-500 transition-colors"
                  />
                  <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-slate-600 dark:group-focus-within:text-slate-300" />
               </div>
          </div>
      </div>

      {/* Grid Header & Sort */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              {tutors.length.toLocaleString()} {filters.subject || 'Teachers'} available
          </h2>
          
          <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500 dark:text-slate-400">Sort by:</span>
              <div className="relative group min-w-[180px]">
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 flex items-center justify-between cursor-pointer hover:border-slate-300 transition-colors">
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{filters.sort}</span>
                      <ChevronDown size={14} className="text-slate-400" />
                  </div>
                  <select 
                    value={filters.sort}
                    onChange={(e) => handleInputChange('sort', e.target.value)}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer appearance-none"
                  >
                      {SORT_OPTIONS.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                  </select>
              </div>
          </div>
      </div>

      {/* Grid */}
      <div>
          {tutors.length === 0 ? (
              <div className="text-center py-20 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 border-dashed">
                  <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400">
                      <Search size={32} />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">No tutors found</h3>
                  <p className="text-slate-500 dark:text-slate-400 max-w-xs mx-auto mb-6">
                      Try adjusting your search terms or filters to find what you're looking for.
                  </p>
                  <button 
                    onClick={clearFilters}
                    className="text-emerald-600 font-bold hover:underline"
                  >
                      Clear all filters
                  </button>
              </div>
          ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {tutors.map(tutor => (
                     <TutorCard 
                         key={tutor.id} 
                         tutor={tutor} 
                         onViewProfile={onViewProfile}
                         onToggleSave={onToggleSave}
                         onBook={onBook}
                         onQuickBook={onQuickBook}
                         onSlotBook={onSlotBook}
                         onMessage={onMessage}
                         isSaved={savedTutorIds.includes(tutor.id)}
                      />
                  ))}
              </div>
          )}
      </div>
    </div>
  );
};
