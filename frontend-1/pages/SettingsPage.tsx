
import React, { useState, useRef } from 'react';
import { Upload, HelpCircle, Facebook, Lock, Mail, CreditCard, Calendar, Bell, Trash2, CheckCircle, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { User } from '../domain/types';

interface SettingsPageProps {
    currentUser: User;
    onUpdateUser: (updatedUser: User) => void;
}

const SIDEBAR_ITEMS = [
    { id: 'account', label: 'Account' },
    { id: 'password', label: 'Password' },
    { id: 'email', label: 'Email' },
    { id: 'payment_methods', label: 'Payment methods' },
    { id: 'payment_history', label: 'Payment history' },
    { id: 'autoconfirmation', label: 'Autoconfirmation' },
    { id: 'calendar', label: 'Calendar' },
    { id: 'notifications', label: 'Notifications' },
    { id: 'delete_account', label: 'Delete account' },
];

export const SettingsPage: React.FC<SettingsPageProps> = ({ currentUser, onUpdateUser }) => {
    const [activeTab, setActiveTab] = useState('account');
    
    // Account Form State
    const [firstName, setFirstName] = useState(currentUser.name.split(' ')[0] || '');
    const [lastName, setLastName] = useState(currentUser.name.split(' ').slice(1).join(' ') || '');
    const [phoneNumber, setPhoneNumber] = useState('345 678 901');
    const [countryCode, setCountryCode] = useState('+1');
    const [timezone, setTimezone] = useState('Europe/Belgrade GMT +1:00');
    
    const [isFacebookConnected, setIsFacebookConnected] = useState(false);
    const [isGoogleConnected, setIsGoogleConnected] = useState(true);

    // Password Form State
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [verifyPassword, setVerifyPassword] = useState('');
    const [showCurrentPassword, setShowCurrentPassword] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [showVerifyPassword, setShowVerifyPassword] = useState(false);

    // Payment Methods State
    const [paymentCards, setPaymentCards] = useState([
        { id: 'card-1', type: 'Visa', last4: '4242', expiry: '12/25' },
        { id: 'card-2', type: 'Mastercard', last4: '5693', expiry: '06/27' }
    ]);

    // Autoconfirmation State
    const [autoconfirmOption, setAutoconfirmOption] = useState('automatic');

    // Notifications State
    const [emailTips, setEmailTips] = useState(true);
    const [emailSurveys, setEmailSurveys] = useState(false);

    // Delete Account State
    const [deleteEmail, setDeleteEmail] = useState('');

    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleSave = () => {
        if (activeTab === 'password') {
            setCurrentPassword('');
            setNewPassword('');
            setVerifyPassword('');
            alert('Password updated successfully!');
            return;
        }
        if (activeTab === 'autoconfirmation' || activeTab === 'notifications') {
            alert('Settings saved successfully!');
            return;
        }

        const updatedUser = {
            ...currentUser,
            name: `${firstName} ${lastName}`.trim(),
        };
        onUpdateUser(updatedUser);
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                onUpdateUser({ ...currentUser, avatarUrl: reader.result as string });
            };
            reader.readAsDataURL(file);
        }
    };

    // Payment Method Handlers
    const handleAddCard = () => {
        const brands = ['Visa', 'Mastercard', 'Amex'];
        const brand = brands[Math.floor(Math.random() * brands.length)];
        const newCard = {
            id: `card-${Date.now()}`,
            type: brand,
            last4: Math.floor(1000 + Math.random() * 9000).toString(),
            expiry: `${Math.floor(1 + Math.random() * 12).toString().padStart(2, '0')}/${Math.floor(24 + Math.random() * 5)}`
        };
        setPaymentCards([...paymentCards, newCard]);
    };

    const handleRemoveCard = (id: string) => {
        if (window.confirm("Are you sure you want to remove this payment method?")) {
            setPaymentCards(paymentCards.filter(c => c.id !== id));
        }
    };

    const renderCardIcon = (type: string) => {
        switch (type.toLowerCase()) {
            case 'visa':
                return (
                    <div className="h-8 w-12 border border-slate-200 dark:border-slate-700 rounded bg-white flex items-center justify-center" aria-label="Visa">
                        <svg viewBox="0 0 36 12" className="h-4 w-auto" fill="#1A1F71">
                            <path d="M13.5 0L10 11H7L9.5 1H13.5ZM21.5 0L18 11H15L17.5 1H21.5ZM35.5 0L32 11H29L31.5 1H35.5ZM6 0L2.5 11H0L3.5 1H6Z" />
                            <path d="M4.7 0.3L1.5 8.7L0.8 1.9C0.7 0.9 0 0.5 0 0.5L3.5 0.3H4.7ZM8.8 0.3L6 8.7L7.8 0.3H8.8ZM12.7 0.3L12 3.6L10.3 0.3H8.9L11.3 4.5L10.2 8.7H12.6L16 0.3H12.7ZM19.2 3.2C19.2 2 17.5 1.9 17.5 1.4C17.5 1.2 17.7 1 18.3 0.9C18.6 0.9 19.3 0.9 20.3 1.4L20.7 0.3C20.2 0.1 19.5 0 18.7 0C16.4 0 14.8 1.2 14.8 2.9C14.8 4.2 16 4.9 16.9 5.3C17.8 5.8 18.1 6.1 18.1 6.5C18.1 7.1 17.4 7.3 16.7 7.3C15.6 7.3 14.9 6.8 14.4 6.6L14 7.8C14.5 8 15.5 8.3 16.6 8.3C19.1 8.3 20.7 7 20.7 5.4C20.8 4.1 19.2 3.6 19.2 3.2Z" />
                        </svg>
                    </div>
                );
            case 'mastercard':
                return (
                    <div className="h-8 w-12 border border-slate-200 dark:border-slate-700 rounded bg-white flex items-center justify-center" aria-label="Mastercard">
                       <svg viewBox="0 0 24 18" className="h-5 w-auto">
                           <circle cx="7" cy="9" r="7" fill="#EB001B" />
                           <circle cx="17" cy="9" r="7" fill="#F79E1B" fillOpacity="0.8" />
                       </svg>
                    </div>
                );
            case 'amex':
                return (
                    <div className="h-8 w-12 border border-slate-200 dark:border-slate-700 rounded bg-[#006fcf] flex items-center justify-center overflow-hidden" aria-label="Amex">
                        <svg viewBox="0 0 40 24" className="h-4 w-auto fill-white">
                            <path d="M3.3 15.6h3.6l-1.8-4.2-1.8 4.2zm-3.3 0h3.1l.6-1.4h4.4l.6 1.4h3.1l-4.5-9.8H7.3L0 15.6zm13.1-9.8h3.3l1.8 5.3 1.7-5.3h3.3l-3.3 9.8h-3.5l-3.3-9.8zM24.7 5.8h8.3v1.8h-5.3v2.1h5.3v1.8h-5.3v2.3h5.3v1.8h-8.3V5.8zm9.5 0h3.6l1.3 2.1 1.4-2.1h3.6l-3.1 4.7 3.3 5.1h-3.7l-1.5-2.4-1.5 2.4h-3.7l3.3-5.1-3-4.7z"/>
                        </svg>
                    </div>
                );
            case 'discover':
                return (
                    <div className="h-8 w-12 border border-slate-200 dark:border-slate-700 rounded bg-white flex items-center justify-center" aria-label="Discover">
                        <svg viewBox="0 0 100 18" className="h-3 w-auto">
                            <path d="M12.1 1.6H2.9v14.8h9.2c4.1 0 7.4-3.3 7.4-7.4s-3.3-7.4-7.4-7.4zm0 11.8H5.9V4.6h6.2c2.5 0 4.4 1.9 4.4 4.4s-1.9 4.4-4.4 4.4zM24.3 1.6h-3v14.8h3V1.6zM36.1 12.1c-1.3-.6-1.7-1.1-1.7-2 0-1 .9-1.6 2.3-1.6 1.4 0 2.5.6 3.1 1.2l1.9-2.1c-1.1-1.1-2.9-2.1-5-2.1-3.3 0-5.5 2.1-5.5 5 0 3.3 2.9 3.9 5.3 4.9 1.1.5 1.5.9 1.5 1.9 0 1-.9 1.7-2.6 1.7-1.6 0-3.1-.7-4-1.8l-2.1 2c1.4 1.7 3.5 2.7 6.1 2.7 3.4 0 5.7-2.1 5.7-5.1 0-3.3-2.9-4-5-4.7zM57.6 5.2c-2.3 0-4.2 1.9-4.2 4.2 0 1.2.5 2.2 1.3 3l-1.9 2.1C51.4 13.1 50.4 11.2 50.4 9c0-4 3.2-7.4 7.2-7.4 2.1 0 4.1 1 5.4 2.5l-2.1 2.1c-.8-.6-1.9-1-3.3-1zM72.3 1.6c-4.1 0-7.4 3.3-7.4 7.4s3.3 7.4 7.4 7.4 7.4-3.3 7.4-7.4-3.3-7.4-7.4-7.4zm0 11.9c-2.5 0-4.4-2-4.4-4.4s2-4.4 4.4-4.4 4.4 2 4.4 4.4-2 4.4-4.4 4.4z" fill="#4B4B4B"/>
                            <circle cx="72.3" cy="9" r="4.4" fill="#F97316"/>
                            <path d="M89.7 1.6h-3.3L81.1 16.4h3.1l.9-2.8h5.3l.9 2.8h3.1L89.7 1.6zm-3.8 9.3l1.8-5.7 1.8 5.7H85.9z" fill="#4B4B4B"/>
                            <path d="M100 1.6h-5.2v14.8h3V10h1.8l2.9 6.4h3.4L102.5 9c1.9-.5 3.1-2.1 3.1-4.1 0-2.3-1.9-3.3-5.6-3.3zm-2.2 6.1h-1.9V4.4h1.9c1.1 0 1.7.5 1.7 1.6.1 1.2-.6 1.7-1.7 1.7z" fill="#4B4B4B"/>
                        </svg>
                    </div>
                );
            default:
                return (
                    <div className="h-8 w-12 bg-slate-100 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 flex items-center justify-center text-[10px] font-bold text-slate-500">
                        CARD
                    </div>
                );
        }
    };

    const renderContent = () => {
        switch (activeTab) {
            case 'account':
                return (
                    <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
                        {/* Profile Image */}
                        <div className="space-y-4">
                            <label className="block text-sm font-medium text-slate-900 dark:text-white">Profile image</label>
                            <div className="flex flex-col sm:flex-row items-start gap-6 sm:gap-8">
                                <div className="flex flex-col items-center gap-2">
                                    <div className="w-24 h-24 sm:w-32 sm:h-32 bg-slate-200 dark:bg-slate-800 rounded-lg overflow-hidden flex-shrink-0 shadow-sm">
                                        <img 
                                            src={currentUser.avatarUrl} 
                                            alt="Profile" 
                                            className="w-full h-full object-cover"
                                            onError={(e) => { (e.target as HTMLImageElement).src = 'https://via.placeholder.com/150' }} 
                                        />
                                    </div>
                                    <button 
                                        onClick={() => fileInputRef.current?.click()}
                                        className="text-sm text-slate-900 dark:text-white underline decoration-slate-900 dark:decoration-white font-medium hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                                    >
                                        Edit
                                    </button>
                                </div>
                                <div className="pt-2 space-y-3 w-full sm:w-auto">
                                    <input 
                                        type="file" 
                                        ref={fileInputRef}
                                        onChange={handleFileChange}
                                        className="hidden"
                                        accept="image/png, image/jpeg"
                                    />
                                    <button 
                                        onClick={() => fileInputRef.current?.click()}
                                        className="flex items-center justify-center sm:justify-start gap-2 px-4 py-2 w-full sm:w-auto bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg text-sm font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors shadow-sm"
                                    >
                                        <Upload size={16} /> Upload photo
                                    </button>
                                    <div className="text-xs text-slate-500 dark:text-slate-400 space-y-1 text-center sm:text-left">
                                        <p>Maximum size – 2MB</p>
                                        <p>JPG or PNG format</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Name Fields */}
                        <div className="space-y-6">
                            <div>
                                <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">First name <span className="text-slate-400 font-normal text-xs ml-1">• Required</span></label>
                                <input 
                                    type="text" 
                                    value={firstName}
                                    onChange={(e) => setFirstName(e.target.value)}
                                    className="w-full p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Last name</label>
                                <input 
                                    type="text" 
                                    value={lastName}
                                    onChange={(e) => setLastName(e.target.value)}
                                    className="w-full p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                                />
                            </div>
                        </div>

                        {/* Phone Number */}
                        <div>
                            <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Phone number</label>
                            <div className="relative flex items-center group">
                                <div className="absolute left-3 flex items-center gap-2 border-r border-slate-200 dark:border-slate-700 pr-3 h-6">
                                    <img src="https://flagcdn.com/w20/us.png" alt="US" className="w-5 h-auto rounded-sm shadow-sm" />
                                    <span className="text-sm text-slate-700 dark:text-slate-300 font-medium">{countryCode}</span>
                                    <span className="text-[10px] text-slate-400">▼</span>
                                </div>
                                <input 
                                    type="text" 
                                    value={phoneNumber}
                                    onChange={(e) => setPhoneNumber(e.target.value)}
                                    className="w-full p-3 pl-24 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                                />
                                <HelpCircle size={18} className="absolute right-3 text-slate-400 cursor-help hover:text-slate-600 transition-colors" />
                            </div>
                        </div>

                        {/* Timezone */}
                        <div>
                            <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Timezone</label>
                            <div className="relative">
                                <select 
                                    value={timezone}
                                    onChange={(e) => setTimezone(e.target.value)}
                                    className="w-full p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 appearance-none transition-all cursor-pointer"
                                >
                                    <option>Europe/Belgrade GMT +1:00</option>
                                    <option>America/New_York GMT -4:00</option>
                                    <option>Asia/Tokyo GMT +9:00</option>
                                    <option>Europe/London GMT +0:00</option>
                                </select>
                                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                                    <svg width="12" height="8" viewBox="0 0 12 8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M1 1.5L6 6.5L11 1.5"/>
                                    </svg>
                                </div>
                            </div>
                        </div>

                        {/* Social Networks */}
                        <div>
                            <label className="block text-sm text-slate-700 dark:text-slate-300 mb-4">Social networks</label>
                            <div className="space-y-4">
                                {/* Facebook */}
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 bg-black dark:bg-white rounded-full flex items-center justify-center text-white dark:text-black shadow-sm">
                                            <Facebook size={18} fill="currentColor" />
                                        </div>
                                        <span className="text-sm text-slate-700 dark:text-slate-300 truncate max-w-[150px] sm:max-w-none">
                                            {isFacebookConnected ? 'Connected to Facebook' : 'Not connected'}
                                        </span>
                                    </div>
                                    <button 
                                        onClick={() => setIsFacebookConnected(!isFacebookConnected)}
                                        className="px-4 py-1.5 border border-slate-300 dark:border-slate-600 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors min-w-[100px]"
                                    >
                                        {isFacebookConnected ? 'Disconnect' : 'Connect'}
                                    </button>
                                </div>

                                {/* Google */}
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 bg-white border border-slate-200 rounded-full flex items-center justify-center p-1.5 shadow-sm">
                                            <svg viewBox="0 0 24 24" className="w-full h-full">
                                                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                                                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                                                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                                                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                                            </svg>
                                        </div>
                                        <span className="text-sm text-slate-700 dark:text-slate-300 truncate max-w-[150px] sm:max-w-none">
                                            {isGoogleConnected ? `Connected as ${firstName}` : 'Not connected'}
                                        </span>
                                    </div>
                                    <button 
                                        onClick={() => setIsGoogleConnected(!isGoogleConnected)}
                                        className="px-4 py-1.5 border border-slate-300 dark:border-slate-600 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors min-w-[100px]"
                                    >
                                        {isGoogleConnected ? 'Disconnect' : 'Connect'}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Save Button */}
                        <div className="pt-4 pb-8">
                            <button 
                                onClick={handleSave}
                                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-0.5"
                            >
                                Save changes
                            </button>
                        </div>
                    </div>
                );
            case 'password':
                return (
                    <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
                        <div>
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Create Password</h3>
                            
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Current password</label>
                                    <div className="relative">
                                        <input 
                                            type={showCurrentPassword ? "text" : "password"}
                                            value={currentPassword}
                                            onChange={(e) => setCurrentPassword(e.target.value)}
                                            className="w-full p-3 pr-10 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors" 
                                        />
                                        <button 
                                            type="button"
                                            onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                                        >
                                            {showCurrentPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                        </button>
                                    </div>
                                    <div className="mt-2">
                                        <button 
                                            onClick={() => alert('Password reset link sent to your email.')}
                                            className="text-sm font-bold text-slate-900 dark:text-white hover:text-emerald-600 dark:hover:text-emerald-400 border-b border-slate-900 dark:border-white hover:border-emerald-600 dark:hover:border-emerald-400 transition-all"
                                        >
                                            Forgot your password?
                                        </button>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">New password</label>
                                    <div className="relative">
                                        <input 
                                            type={showNewPassword ? "text" : "password"}
                                            value={newPassword}
                                            onChange={(e) => setNewPassword(e.target.value)}
                                            className="w-full p-3 pr-10 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors" 
                                        />
                                        <button 
                                            type="button"
                                            onClick={() => setShowNewPassword(!showNewPassword)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                                        >
                                            {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                        </button>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Verify password</label>
                                    <div className="relative">
                                        <input 
                                            type={showVerifyPassword ? "text" : "password"}
                                            value={verifyPassword}
                                            onChange={(e) => setVerifyPassword(e.target.value)}
                                            className="w-full p-3 pr-10 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors" 
                                        />
                                        <button 
                                            type="button"
                                            onClick={() => setShowVerifyPassword(!showVerifyPassword)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                                        >
                                            {showVerifyPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <div className="pt-6">
                                <button 
                                    onClick={handleSave}
                                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-0.5"
                                >
                                    Save changes
                                </button>
                            </div>
                        </div>
                    </div>
                );
            case 'payment_methods':
                return (
                    <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
                        {/* The "Add Card" Box */}
                        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-6">
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Credit or debit card</h3>
                            
                            <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
                                <div className="flex items-center gap-2">
                                    {renderCardIcon('visa')}
                                    {renderCardIcon('mastercard')}
                                    {renderCardIcon('amex')}
                                    {renderCardIcon('discover')}
                                </div>

                                <button 
                                    onClick={handleAddCard}
                                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 px-6 rounded-md transition-colors shadow-sm whitespace-nowrap w-full sm:w-auto"
                                >
                                    Add card
                                </button>
                            </div>
                        </div>

                        {/* Security Notice */}
                        <div className="flex items-center gap-3 text-slate-500 dark:text-slate-400">
                            <Lock size={18} className="shrink-0" />
                            <p className="text-sm">EduConnect uses industry-standard encryption to protect your information.</p>
                        </div>

                        {/* Saved Cards List */}
                        {paymentCards.length > 0 && (
                            <div className="pt-6">
                                <h4 className="font-bold text-slate-900 dark:text-white mb-4">Saved cards</h4>
                                <div className="space-y-3">
                                    {paymentCards.map(card => (
                                        <div key={card.id} className="flex items-center justify-between p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg">
                                            <div className="flex items-center gap-4">
                                                {renderCardIcon(card.type)}
                                                <div>
                                                    <p className="text-sm font-bold text-slate-900 dark:text-white">
                                                        •••• {card.last4}
                                                    </p>
                                                    <p className="text-xs text-slate-500">Expires {card.expiry}</p>
                                                </div>
                                            </div>
                                            <button 
                                                onClick={() => handleRemoveCard(card.id)}
                                                className="text-sm text-red-500 hover:text-red-600 font-medium px-3 py-1 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                                            >
                                                Remove
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                );
            case 'payment_history':
                const transactions = [
                    { id: 'tx1', date: '2024-10-24T14:00:00', subject: 'English Literature', tutorName: 'Marcus Thorne', hours: 1, amount: 70 },
                    { id: 'tx2', date: '2024-10-20T10:00:00', subject: 'Physics', tutorName: 'Dr. Elena Vance', hours: 1, amount: 85 },
                    { id: 'tx3', date: '2024-10-15T16:00:00', subject: 'Computer Science', tutorName: 'James Chen', hours: 1, amount: 60 },
                    { id: 'tx4', date: '2024-10-01T09:00:00', subject: 'Mathematics', tutorName: 'Sarah Miller', hours: 1, amount: 45 },
                ];

                return (
                    <div className="space-y-8 animate-in fade-in duration-300">
                        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Payment history</h1>
                            <button className="px-5 py-2.5 border border-slate-900 dark:border-slate-200 rounded-lg text-sm font-bold text-slate-900 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                                Update billing info
                            </button>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse min-w-[600px]">
                                <thead>
                                    <tr className="border-b border-slate-200 dark:border-slate-700">
                                        <th className="pb-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Date</th>
                                        <th className="pb-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Subject</th>
                                        <th className="pb-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Tutor</th>
                                        <th className="pb-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Hours</th>
                                        <th className="pb-4 text-xs font-bold text-slate-500 uppercase tracking-wider">
                                            <div className="flex items-center gap-1">
                                                Amount <HelpCircle size={14} className="text-slate-400" />
                                            </div>
                                        </th>
                                        <th className="pb-4 text-right">
                                            <button className="text-xs font-bold text-slate-900 dark:text-white underline uppercase tracking-wider hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                                                Download All
                                            </button>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {transactions.map((tx) => (
                                        <tr key={tx.id} className="group hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                            <td className="py-6 text-sm font-medium text-slate-900 dark:text-white">
                                                {new Date(tx.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                                            </td>
                                            <td className="py-6 text-sm text-slate-600 dark:text-slate-400">{tx.subject}</td>
                                            <td className="py-6 text-sm text-slate-600 dark:text-slate-400">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                                                        {tx.tutorName.charAt(0)}
                                                    </div>
                                                    <span className="truncate max-w-[120px]">{tx.tutorName}</span>
                                                </div>
                                            </td>
                                            <td className="py-6 text-sm text-slate-600 dark:text-slate-400 pl-4">{tx.hours}</td>
                                            <td className="py-6 text-sm font-bold text-slate-900 dark:text-white pl-2">${tx.amount.toFixed(2)}</td>
                                            <td className="py-6 text-right">
                                                <button className="text-sm font-bold text-emerald-600 hover:text-emerald-500 transition-colors">
                                                    Invoice
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                );
            case 'autoconfirmation':
                return (
                    <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
                        <div>
                            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-6">Lesson autoconfirmation</h3>
                            
                            <div className="space-y-4 mb-8 text-slate-600 dark:text-slate-400 leading-relaxed">
                                <p>
                                    We automatically confirm your lessons so your tutor can get paid. Here's how the autoconfirmation timing works:
                                </p>
                                
                                <div className="space-y-3">
                                    <p>
                                        <span className="font-bold text-slate-900 dark:text-white">Lessons completed in the EduConnect classroom</span> are autoconfirmed 15 minutes after completion.
                                    </p>
                                    <p>
                                        <span className="font-bold text-slate-900 dark:text-white">Lessons completed outside EduConnect</span> are autoconfirmed 72 hours after the original scheduled end time.
                                    </p>
                                </div>

                                <p className="pt-2">Choose your settings for lessons that take place outside EduConnect:</p>
                            </div>

                            <div className="space-y-5 mb-8">
                                <label className="flex items-start gap-3 cursor-pointer group select-none">
                                    <div className="relative flex items-center mt-0.5">
                                        <input 
                                            type="radio" 
                                            name="autoconfirm" 
                                            className="peer sr-only" 
                                            checked={autoconfirmOption === 'manual'} 
                                            onChange={() => setAutoconfirmOption('manual')}
                                        />
                                        <div className="w-5 h-5 rounded-full border-2 border-slate-300 dark:border-slate-600 peer-checked:border-slate-900 dark:peer-checked:border-white transition-colors flex items-center justify-center">
                                            <div className={`w-2.5 h-2.5 rounded-full bg-slate-900 dark:bg-white transition-transform duration-200 ${autoconfirmOption === 'manual' ? 'scale-100' : 'scale-0'}`}></div>
                                        </div>
                                    </div>
                                    <span className="text-slate-700 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-white transition-colors leading-snug">
                                        Only lessons scheduled by you or rescheduled by your tutor on your behalf
                                    </span>
                                </label>

                                <label className="flex items-start gap-3 cursor-pointer group select-none">
                                    <div className="relative flex items-center mt-0.5">
                                        <input 
                                            type="radio" 
                                            name="autoconfirm" 
                                            className="peer sr-only" 
                                            checked={autoconfirmOption === 'automatic'} 
                                            onChange={() => setAutoconfirmOption('automatic')}
                                        />
                                        <div className="w-5 h-5 rounded-full border-2 border-slate-300 dark:border-slate-600 peer-checked:border-slate-900 dark:peer-checked:border-white transition-colors flex items-center justify-center">
                                            <div className={`w-2.5 h-2.5 rounded-full bg-slate-900 dark:bg-white transition-transform duration-200 ${autoconfirmOption === 'automatic' ? 'scale-100' : 'scale-0'}`}></div>
                                        </div>
                                    </div>
                                    <span className="text-slate-700 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-white transition-colors leading-snug">
                                        Autoconfirm all my lessons, including weekly lessons and lessons scheduled or rescheduled by my tutor.
                                    </span>
                                </label>
                            </div>

                            <p className="text-sm text-slate-500 dark:text-slate-400 mb-8 leading-relaxed">
                                If you have any problems with your lessons, please let us know as soon as possible and we'll help you find a solution.
                            </p>

                            <div className="pt-2">
                                <button 
                                    onClick={handleSave}
                                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-0.5"
                                >
                                    Save changes
                                </button>
                            </div>
                        </div>
                    </div>
                );
            case 'calendar':
                return (
                    <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
                        <div>
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Google Calendar</h3>
                            <div className="flex items-center gap-4 mb-8">
                                <div className="w-12 h-12 bg-white dark:bg-slate-800 rounded-full flex items-center justify-center shrink-0 shadow-sm border border-slate-100 dark:border-slate-700">
                                     <svg viewBox="0 0 24 24" className="w-7 h-7">
                                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                                    </svg>
                                </div>
                                <p className="text-slate-600 dark:text-slate-300 text-lg">
                                    Connect your Google Calendar and synchronize all your lessons with your personal schedule
                                </p>
                            </div>
                            
                            <button 
                                onClick={() => window.open('https://calendar.google.com', '_blank')}
                                className="w-full py-4 border border-slate-900 dark:border-white rounded-xl text-slate-900 dark:text-white font-bold hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-lg"
                            >
                                Connect Google Calendar
                            </button>
                        </div>
                    </div>
                );
            case 'notifications':
                return (
                    <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
                        <div>
                             <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Notification Preferences</h3>
                             <p className="text-slate-500 dark:text-slate-400 mb-8">Manage how and when you hear from us.</p>

                             <div className="flex items-center gap-2 mb-2 text-slate-900 dark:text-white font-bold text-lg">
                                <Mail size={20} /> Email notifications
                             </div>
                             <p className="text-slate-500 dark:text-slate-400 mb-6 text-sm">Manage the emails you receive from us.</p>

                             <div className="space-y-6">
                                {/* Transactional */}
                                <div className="flex items-start justify-between pb-6 border-b border-slate-100 dark:border-slate-800">
                                    <div>
                                        <h4 className="font-bold text-slate-900 dark:text-white mb-1">Transactional</h4>
                                        <p className="text-slate-500 dark:text-slate-400 text-sm">Important updates about your account and activity.</p>
                                    </div>
                                    <span className="bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold px-3 py-1.5 rounded">Always active</span>
                                </div>

                                {/* Tips and discounts */}
                                 <div className="flex items-start justify-between pb-6 border-b border-slate-100 dark:border-slate-800">
                                    <div className="pr-4">
                                        <h4 className="font-bold text-slate-900 dark:text-white mb-1">Tips and discounts</h4>
                                        <p className="text-slate-500 dark:text-slate-400 text-sm">Get learning resources and exclusive offers to support your progress.</p>
                                    </div>
                                    <button 
                                        onClick={() => setEmailTips(!emailTips)}
                                        className={`w-12 h-6 rounded-full p-1 transition-colors duration-200 ease-in-out relative flex-shrink-0 ${emailTips ? 'bg-slate-900 dark:bg-white' : 'bg-slate-200 dark:bg-slate-700'}`}
                                    >
                                        <div className={`w-4 h-4 rounded-full bg-white dark:bg-slate-900 shadow-sm transform transition-transform duration-200 ${emailTips ? 'translate-x-6' : 'translate-x-0'}`}></div>
                                    </button>
                                </div>

                                {/* Surveys and interviews */}
                                 <div className="flex items-start justify-between">
                                    <div className="pr-4">
                                        <h4 className="font-bold text-slate-900 dark:text-white mb-1">Surveys and interviews</h4>
                                        <p className="text-slate-500 dark:text-slate-400 text-sm">Take part in research studies to help us improve EduConnect.</p>
                                    </div>
                                     <button 
                                        onClick={() => setEmailSurveys(!emailSurveys)}
                                        className={`w-12 h-6 rounded-full p-1 transition-colors duration-200 ease-in-out relative flex-shrink-0 ${emailSurveys ? 'bg-slate-900 dark:bg-white' : 'bg-slate-200 dark:bg-slate-700'}`}
                                    >
                                         <div className={`w-4 h-4 rounded-full bg-white dark:bg-slate-900 shadow-sm transform transition-transform duration-200 ${emailSurveys ? 'translate-x-6' : 'translate-x-0'}`}></div>
                                    </button>
                                </div>
                             </div>

                             <div className="pt-8">
                                <button 
                                    onClick={handleSave}
                                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-0.5"
                                >
                                    Save changes
                                </button>
                            </div>
                        </div>
                    </div>
                );
            case 'delete_account':
                return (
                    <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
                        <div>
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">Delete account</h3>
                            <p className="text-slate-600 dark:text-slate-400 mb-8 leading-relaxed">
                                Deleting your account is permanent and all your account information will be deleted along with it. If you're sure you want to proceed, enter your email address below.
                            </p>

                            <div className="mb-8">
                                <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Email</label>
                                <input 
                                    type="email" 
                                    value={deleteEmail}
                                    onChange={(e) => setDeleteEmail(e.target.value)}
                                    className="w-full p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-red-500 transition-colors"
                                />
                            </div>

                            <div className="flex justify-end">
                                <button 
                                    disabled={!deleteEmail}
                                    className="px-6 py-3 bg-slate-200 dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-bold rounded-lg flex items-center gap-2 disabled:cursor-not-allowed hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-colors"
                                >
                                    <Trash2 size={18} /> Delete account
                                </button>
                            </div>
                        </div>
                    </div>
                );
            default:
                return (
                    <div className="flex flex-col items-center justify-center h-64 text-slate-400 animate-in fade-in duration-300 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl bg-slate-50 dark:bg-slate-900/50">
                        <div className="w-16 h-16 bg-white dark:bg-slate-800 rounded-full flex items-center justify-center mb-4 shadow-sm">
                            <SettingsIcon tab={activeTab} size={24} className="text-slate-400 dark:text-slate-500" />
                        </div>
                        <p className="font-medium text-slate-600 dark:text-slate-300">Settings for {SIDEBAR_ITEMS.find(i => i.id === activeTab)?.label}</p>
                        <p className="text-sm mt-1 text-slate-400">This section is coming soon.</p>
                    </div>
                );
        }
    };

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl min-h-[calc(100vh-80px)]">
            <div className="flex flex-col md:flex-row gap-12">
                
                {/* Sidebar - Mobile Responsive: Stacks on top */}
                <div className="w-full md:w-64 flex-shrink-0">
                    <div className="space-y-1 md:sticky md:top-24 overflow-x-auto md:overflow-visible flex md:block pb-2 md:pb-0 gap-2 md:gap-0 snap-x snap-mandatory md:snap-none">
                        {SIDEBAR_ITEMS.map((item) => (
                            <button
                                key={item.id}
                                onClick={() => setActiveTab(item.id)}
                                className={`flex-shrink-0 md:w-full text-left px-4 py-3 text-sm font-medium transition-all rounded-lg md:rounded-none md:border-l-[3px] border-l-0 snap-center ${
                                    activeTab === item.id 
                                        ? 'border-emerald-500 text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/10' 
                                        : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                                }`}
                            >
                                {item.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1 max-w-5xl">
                    {!['payment_history', 'password', 'autoconfirmation', 'delete_account', 'calendar', 'notifications'].includes(activeTab) && (
                        <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-8">
                            {activeTab === 'account' ? 'Account Settings' : `${SIDEBAR_ITEMS.find(i => i.id === activeTab)?.label}`}
                        </h1>
                    )}
                    {renderContent()}
                </div>
            </div>
        </div>
    );
};

const SettingsIcon = ({ tab, size, className }: { tab: string, size: number, className?: string }) => {
    switch(tab) {
        case 'password': return <Lock size={size} className={className} />;
        case 'email': return <Mail size={size} className={className} />;
        case 'payment_methods': return <CreditCard size={size} className={className} />;
        case 'calendar': return <Calendar size={size} className={className} />;
        case 'notifications': return <Bell size={size} className={className} />;
        case 'delete_account': return <Trash2 size={size} className={className} />;
        default: return <CheckCircle size={size} className={className} />;
    }
}
