
import React, { useState, useRef, useEffect } from 'react';
import { BookOpen, Sun, Moon, MessageSquare, ChevronDown, User, Share2, Users, Video, Calendar, Settings, LogOut as LogOutIcon, Menu, X } from 'lucide-react';
import { UserRole } from '../../domain/types';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigation } from '../../contexts/NavigationContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useData } from '../../contexts/DataContext';

interface NavbarProps {
    onOpenChat: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenChat }) => {
    const { currentUser, logout } = useAuth();
    const { currentView, navigate } = useNavigation();
    const { theme, toggleTheme } = useTheme();
    const { chats } = useData();

    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const unreadMessages = chats.reduce((acc, chat) => acc + chat.unreadCount, 0);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsDropdownOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const handleMenuClick = (action: () => void) => {
        action();
        setIsDropdownOpen(false);
        setIsMobileMenuOpen(false);
    };

    const handleLogout = () => {
        logout();
        navigate('home');
    };

    const renderAvatar = (user: any, size: string = "w-9 h-9", fontSize: string = "text-sm") => {
        const isPlaceholder = !user.avatarUrl || user.avatarUrl.includes('ui-avatars.com') || user.avatarUrl.includes('placeholder');
        
        if (isPlaceholder) {
            return (
                <div className={`${size} rounded-full bg-emerald-100 dark:bg-emerald-900/50 flex items-center justify-center text-emerald-700 dark:text-emerald-300 font-bold ${fontSize} border border-emerald-200 dark:border-emerald-800 shadow-sm`}>
                    {user.name.charAt(0).toUpperCase()}
                </div>
            );
        }
        
        return <img src={user.avatarUrl} alt={user.name} className={`${size} rounded-full border border-slate-200 dark:border-slate-700 object-cover`} />;
    };

    return (
        <nav className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md transition-colors duration-200">
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            <div className="flex items-center gap-2 cursor-pointer" onClick={() => {
                if (!currentUser || currentUser.role === UserRole.STUDENT) navigate('home');
                else if (currentUser && currentUser.role === UserRole.TUTOR) navigate('tutor-dashboard');
                else if (currentUser && (currentUser.role === UserRole.ADMIN || currentUser.role === UserRole.OWNER)) navigate('admin-dashboard');
                else navigate('home');
            }}>
              <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
                <BookOpen className="text-white" size={20} />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-emerald-500 to-emerald-700 dark:from-emerald-400 dark:to-emerald-600 bg-clip-text text-transparent">
                EduConnect
              </span>
            </div>
    
            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-4 sm:gap-6">
               <div className="flex gap-6">
                   {currentUser?.role === UserRole.STUDENT && (
                     <>
                        <button 
                            onClick={() => navigate('student-lessons')}
                            className={`text-sm font-medium transition-colors ${currentView === 'student-lessons' ? 'text-emerald-500' : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'}`}
                        >
                            My Lessons
                        </button>
                        <button 
                            onClick={() => navigate('student-saved-tutors')}
                            className={`text-sm font-medium transition-colors ${currentView === 'student-saved-tutors' ? 'text-emerald-500' : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'}`}
                        >
                            Saved Tutors
                        </button>
                     </>
                   )}
                   {currentUser?.role === UserRole.TUTOR && (
                     <button 
                       onClick={() => navigate('tutor-dashboard')}
                       className={`text-sm font-medium transition-colors ${currentView === 'tutor-dashboard' ? 'text-emerald-500' : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'}`}
                     >
                       Tutor Hub
                     </button>
                   )}
                   {(currentUser?.role === UserRole.ADMIN || currentUser?.role === UserRole.OWNER) && (
                     <button 
                       onClick={() => navigate('admin-dashboard')}
                       className={`text-sm font-medium transition-colors ${currentView === 'admin-dashboard' ? 'text-emerald-500' : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'}`}
                     >
                       Admin Panel
                     </button>
                   )}
               </div>
               
               <div className="h-6 w-px bg-slate-200 dark:bg-slate-800" />
    
               <button 
                    onClick={toggleTheme}
                    className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors rounded-full hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                    {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                </button>
    
                {currentUser ? (
                    <>
                        <button 
                            onClick={onOpenChat}
                            className="p-2 text-slate-500 hover:text-emerald-600 dark:text-slate-400 dark:hover:text-emerald-400 transition-colors rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 relative"
                            title="Messages"
                        >
                            <MessageSquare size={20} />
                            {unreadMessages > 0 && (
                                <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white dark:border-slate-900"></span>
                            )}
                        </button>
                    
                        <div className="relative pl-2 border-l border-slate-200 dark:border-slate-800" ref={dropdownRef}>
                            <button 
                                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                                    className="flex items-center gap-3 p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors focus:outline-none"
                            >
                                    {renderAvatar(currentUser)}
                                    <span className="hidden sm:block text-sm font-bold text-slate-900 dark:text-white max-w-[120px] truncate">
                                        {currentUser.name}
                                    </span>
                                    <ChevronDown size={14} className={`text-slate-400 hidden sm:block transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
                            </button>
                            
                            {isDropdownOpen && (
                                    <div className="absolute right-0 top-full mt-2 w-72 bg-white dark:bg-slate-900 rounded-xl shadow-xl border border-slate-200 dark:border-slate-800 py-2 z-50 animate-in fade-in zoom-in-95 duration-200 origin-top-right">
                                        <div className="px-5 py-4 flex items-center gap-3 border-b border-slate-100 dark:border-slate-800">
                                            {renderAvatar(currentUser, "w-10 h-10", "text-lg")}
                                            <div className="overflow-hidden">
                                                <p className="font-bold text-slate-900 dark:text-white truncate">{currentUser.name}</p>
                                                <p className="text-xs text-slate-500 capitalize">{currentUser.role.toLowerCase()}</p>
                                            </div>
                                        </div>

                                        {currentUser.role === UserRole.TUTOR && (
                                            <div className="px-5 py-3">
                                                <button className="w-full flex items-center justify-center gap-2 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                                                    <Share2 size={16} /> Share profile
                                                </button>
                                            </div>
                                        )}

                                        <div className="py-1">
                                            <button 
                                                onClick={() => handleMenuClick(onOpenChat)} 
                                                className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                                            >
                                                <MessageSquare size={18} /> Messages
                                            </button>

                                            {currentUser.role === UserRole.TUTOR && (
                                                <>
                                                    <button 
                                                        onClick={() => handleMenuClick(() => navigate('tutor-students'))} 
                                                        className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                                                    >
                                                        <Users size={18} /> Students
                                                    </button>
                                                    <button 
                                                        onClick={() => handleMenuClick(() => navigate('tutor-dashboard'))} 
                                                        className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                                                    >
                                                        <Video size={18} /> Classroom
                                                    </button>
                                                </>
                                            )}

                                            {currentUser.role === UserRole.STUDENT && (
                                                <>
                                                    <button 
                                                        onClick={() => handleMenuClick(() => navigate('student-lessons'))} 
                                                        className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                                                    >
                                                        <BookOpen size={18} /> My lessons
                                                    </button>
                                                    <button 
                                                        onClick={() => handleMenuClick(() => navigate('student-saved-tutors'))} 
                                                        className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                                                    >
                                                        <Users size={18} /> Saved tutors
                                                    </button>
                                                </>
                                            )}

                                            <button 
                                                onClick={() => handleMenuClick(() => navigate('referral'))} 
                                                className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                                            >
                                                <Share2 size={18} /> Refer a friend
                                            </button>

                                            <button 
                                                onClick={() => handleMenuClick(() => navigate('settings'))} 
                                                className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                                            >
                                                <Settings size={18} /> Settings
                                            </button>
                                        </div>
                                        
                                        <div className="h-px bg-slate-100 dark:bg-slate-800 my-1 mx-2"></div>
                                        
                                        <button 
                                            onClick={() => handleMenuClick(handleLogout)} 
                                            className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                                        >
                                            <LogOutIcon size={18} /> Log out
                                        </button>
                                    </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex items-center gap-3 pl-4 border-l border-slate-200 dark:border-slate-800">
                        <button 
                            onClick={() => navigate('login')}
                            className="text-sm font-bold text-slate-600 dark:text-slate-300 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                        >
                            Log in
                        </button>
                        <button 
                            onClick={() => navigate('login')} 
                            className="px-4 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-sm font-bold rounded-lg hover:opacity-90 transition-opacity"
                        >
                            Sign up
                        </button>
                    </div>
                )}
            </div>

            {/* Mobile Menu Button */}
            <div className="flex md:hidden items-center gap-4">
                <button 
                    onClick={toggleTheme}
                    className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors rounded-full"
                >
                    {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                </button>
                <button 
                    onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                    className="p-2 text-slate-600 dark:text-slate-300"
                >
                    {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </div>

            {/* Mobile Menu Dropdown */}
            {isMobileMenuOpen && (
                <div className="absolute top-16 left-0 w-full bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-xl md:hidden animate-in slide-in-from-top-2">
                    <div className="p-4 space-y-4">
                        {currentUser ? (
                            <>
                                <div className="flex items-center gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
                                    {renderAvatar(currentUser)}
                                    <div>
                                        <p className="font-bold text-slate-900 dark:text-white">{currentUser.name}</p>
                                        <p className="text-xs text-slate-500">{currentUser.role}</p>
                                    </div>
                                </div>
                                <div className="grid gap-2">
                                    <button onClick={() => handleMenuClick(() => navigate('home'))} className="text-left py-2 font-medium text-slate-700 dark:text-slate-300">Find Tutors</button>
                                    
                                    {currentUser.role === UserRole.STUDENT && (
                                        <>
                                            <button onClick={() => handleMenuClick(() => navigate('student-lessons'))} className="text-left py-2 font-medium text-slate-700 dark:text-slate-300">My Lessons</button>
                                            <button onClick={() => handleMenuClick(() => navigate('student-saved-tutors'))} className="text-left py-2 font-medium text-slate-700 dark:text-slate-300">Saved Tutors</button>
                                        </>
                                    )}
                                    
                                    {currentUser.role === UserRole.TUTOR && (
                                        <>
                                            <button onClick={() => handleMenuClick(() => navigate('tutor-dashboard'))} className="text-left py-2 font-medium text-slate-700 dark:text-slate-300">Dashboard</button>
                                            <button onClick={() => handleMenuClick(() => navigate('tutor-students'))} className="text-left py-2 font-medium text-slate-700 dark:text-slate-300">Students</button>
                                        </>
                                    )}

                                    <button onClick={() => handleMenuClick(onOpenChat)} className="text-left py-2 font-medium text-slate-700 dark:text-slate-300">Messages</button>
                                    <button onClick={() => handleMenuClick(() => navigate('settings'))} className="text-left py-2 font-medium text-slate-700 dark:text-slate-300">Settings</button>
                                    <button onClick={() => handleMenuClick(handleLogout)} className="text-left py-2 font-medium text-red-600">Log Out</button>
                                </div>
                            </>
                        ) : (
                            <div className="flex flex-col gap-3">
                                <button onClick={() => handleMenuClick(() => navigate('home'))} className="text-left py-2 font-medium text-slate-700 dark:text-slate-300">Find Tutors</button>
                                <div className="h-px bg-slate-100 dark:bg-slate-800 my-2"></div>
                                <button 
                                    onClick={() => handleMenuClick(() => navigate('login'))}
                                    className="w-full py-3 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-bold rounded-xl"
                                >
                                    Log in
                                </button>
                                <button 
                                    onClick={() => handleMenuClick(() => navigate('login'))}
                                    className="w-full py-3 bg-emerald-600 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20"
                                >
                                    Sign up
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}
          </div>
        </nav>
    );
};
