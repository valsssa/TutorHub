
import React, { useState } from 'react';
import { UserRole, Tutor } from '../../domain/types';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigation } from '../../contexts/NavigationContext';
import { useData } from '../../contexts/DataContext';
import { useTheme } from '../../contexts/ThemeContext';

// Pages
import { LoginPage } from '../../pages/LoginPage';
import { MarketplacePage } from '../../pages/MarketplacePage';
import { TutorProfilePage } from '../../pages/TutorProfilePage';
import { StudentLessonsPage } from '../../pages/StudentLessonsPage';
import { SavedTutorsPage } from '../../pages/SavedTutorsPage';
import { TutorDashboard } from '../../pages/TutorDashboard';
import { AdminDashboard } from '../../pages/AdminDashboard';
import { SettingsPage } from '../../pages/SettingsPage';
import { ReferralPage } from '../../pages/ReferralPage';
import { PaymentPage } from '../../pages/PaymentPage';
import { TutorEarningsPage } from '../../pages/TutorEarningsPage';
import { TutorStudentsPage } from '../../pages/TutorStudentsPage';
import { AdminRevenuePage } from '../../pages/AdminRevenuePage';
import { AdminVerificationsPage } from '../../pages/AdminVerificationsPage';
import { AdminSessionsPage } from '../../pages/AdminSessionsPage';
import { AdminTutorsPage } from '../../pages/AdminTutorsPage';
import { AdminManagePage } from '../../pages/AdminManagePage';
import { LegalPage } from '../../pages/LegalPage';
import { PrivacyPage } from '../../pages/PrivacyPage';
import { TermsPage } from '../../pages/TermsPage';
import { CookiePolicyPage } from '../../pages/CookiePolicyPage';
import { MobileAppPage } from '../../pages/MobileAppPage';
import { SuccessStoriesPage } from '../../pages/SuccessStoriesPage';
import { AffiliateProgramPage } from '../../pages/AffiliateProgramPage';
import { BecomeTutorPage } from '../../pages/BecomeTutorPage';
import { TutorRulesPage } from '../../pages/TutorRulesPage';
import { CancellationPolicyPage } from '../../pages/CancellationPolicyPage';
import { SupportPage } from '../../pages/SupportPage';
import { PricingPage } from '../../pages/PricingPage';

// Components
import { Classroom } from '../classroom/Classroom';
import { TutorProfileEditor } from '../dashboard/TutorProfileEditor';
import { TutorScheduleManager } from '../dashboard/TutorScheduleManager';
import { TutorLessonScheduler } from '../dashboard/TutorLessonScheduler';
import { VerificationManager } from '../dashboard/VerificationManager';
import { Modal } from '../shared/UI';
import { MessagingSystem } from '../messaging/MessagingSystem';

export const AppRouter: React.FC<{ 
    isMessagingOpen: boolean, 
    setIsMessagingOpen: (v: boolean) => void,
    activeThreadId: string | null,
    setActiveThreadId: (id: string | null) => void 
}> = ({ isMessagingOpen, setIsMessagingOpen, activeThreadId, setActiveThreadId }) => {
    
    const { currentUser, login, updateUser } = useAuth();
    const { 
        currentView, navigate, activeTutor, bookingSlot, activeSession, 
        goToProfile, goToBooking, startSession, endSession 
    } = useNavigation();
    const { 
        tutors, sessions, verificationRequests, chats, admins, students,
        updateTutor, addSession, updateVerificationStatus, sendMessage, createThread, addAdmin, removeAdmin
    } = useData();
    const { theme } = useTheme();

    // Local UI State for specific overlays
    const [isManagingSchedule, setIsManagingSchedule] = useState(false);
    const [isVerificationManagerOpen, setIsVerificationManagerOpen] = useState(false);
    const [scheduleMode, setScheduleMode] = useState<'calendar' | 'setup'>('calendar');
    const [quickActionType, setQuickActionType] = useState<'Lesson' | 'Time off' | 'Extra slots' | null>(null);
    const [filters, setFilters] = useState<any>({
        searchQuery: '', maxPrice: 200, subject: '', minRating: 0,
        country: 'Any country', availability: 'Any time', sort: 'Our top picks', nativeSpeaker: false
    });

    const handleLogin = (user: any, nextView: any) => {
        // AuthContext already handles the API call, we just need to route
        navigate(nextView);
    };

    const handleConfirmBooking = () => {
        if (activeTutor && currentUser && bookingSlot) {
            addSession({
                id: `ses-${Date.now()}`,
                tutorId: activeTutor.id,
                tutorName: activeTutor.name,
                studentId: currentUser.id,
                date: bookingSlot,
                status: 'upcoming',
                price: activeTutor.hourlyRate,
                subject: activeTutor.subject
            });
            alert("Booking Confirmed!");
            navigate('student-lessons');
        }
    };

    const handleToggleSaveTutor = (e: React.MouseEvent, tutorId: string) => {
        e.stopPropagation();
        if (!currentUser) return;
        const isSaved = currentUser.savedTutorIds?.includes(tutorId);
        let newSavedIds = currentUser.savedTutorIds || [];
        if (isSaved) {
            newSavedIds = newSavedIds.filter(id => id !== tutorId);
        } else {
            newSavedIds = [...newSavedIds, tutorId];
        }
        updateUser({ ...currentUser, savedTutorIds: newSavedIds });
    };

    const handleOpenChat = (threadId?: string) => {
        if (!currentUser) {
            navigate('login');
            return;
        }
        setIsMessagingOpen(true);
        if (threadId) setActiveThreadId(threadId);
    };

    const handleMessageUser = (participantId: string, participantName?: string, participantAvatar?: string) => {
        if (!currentUser) {
            navigate('login');
            return;
        }
        
        setIsMessagingOpen(true);
        
        // Find existing thread with this participant
        const existingThread = chats.find(c => c.participantId === participantId);
        if (existingThread) {
            setActiveThreadId(existingThread.id);
        } else if (participantName) {
            // Create a new thread if one doesn't exist but we have user details
            const avatar = participantAvatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(participantName)}&background=random`;
            const newThreadId = createThread(participantId, participantName, avatar);
            setActiveThreadId(newThreadId);
        } else {
            // If no thread exists and insufficient info to create one, show list
            setActiveThreadId(null);
        }
    };

    // Helper to check auth before booking
    const handleBookingAttempt = (tutor: Tutor, slot?: string) => {
        if (currentUser) {
            goToBooking(tutor, slot);
        } else {
            navigate('login');
        }
    };

    // --- Render Logic ---

    // Overlays for Tutor
    if (isVerificationManagerOpen && currentUser?.role === UserRole.TUTOR) {
        const myTutorProfile = tutors.find(t => t.id === currentUser.id);
        const myRequest = verificationRequests.find(r => r.tutorId === currentUser.id);
        return (
            <div className="container mx-auto px-4 py-8 max-w-2xl">
                <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
                   <VerificationManager 
                       status={myTutorProfile?.isVerified ? 'verified' : (myRequest?.status || 'unverified')}
                       currentRequest={myRequest}
                       onSubmit={(files) => { alert("Documents uploaded!"); setIsVerificationManagerOpen(false); }}
                       onClose={() => setIsVerificationManagerOpen(false)}
                   />
                </div>
            </div>
        );
    }

    // Main Router Switch
    switch (currentView) {
        case 'login':
            return <LoginPage onLogin={handleLogin} setNotification={(msg) => alert(msg)} />;
        
        case 'home':
            return (
                <MarketplacePage 
                    tutors={tutors}
                    savedTutorIds={currentUser?.savedTutorIds || []}
                    filters={filters}
                    setFilters={setFilters}
                    onSearch={(e) => e.preventDefault()}
                    onViewProfile={goToProfile}
                    onToggleSave={handleToggleSaveTutor}
                    onBook={(e, t) => handleBookingAttempt(t)}
                    onQuickBook={(e, t) => { e.stopPropagation(); handleBookingAttempt(t); }}
                    onSlotBook={(e, t, s) => { e.stopPropagation(); handleBookingAttempt(t, s); }}
                    onMessage={(e, t) => { e.stopPropagation(); handleMessageUser(t.id, t.name, t.imageUrl); }}
                    aiLoading={false}
                    onOpenFilter={() => {}}
                />
            );

        case 'tutor-profile':
            if (!activeTutor) return null;
            const isOwnProfile = currentUser?.id === activeTutor.id;
            return (
                <TutorProfilePage 
                    tutor={activeTutor}
                    onBack={() => navigate(isOwnProfile ? 'tutor-dashboard' : 'home')}
                    backLabel={isOwnProfile ? 'Back to Dashboard' : 'Back to Marketplace'}
                    onBook={() => handleBookingAttempt(activeTutor)}
                    onBookSlot={(t, s) => handleBookingAttempt(t, s)}
                    onMessage={(t) => handleMessageUser(t.id, t.name, t.imageUrl)}
                    isOwnProfile={isOwnProfile}
                    onEdit={() => navigate('tutor-profile-editor')}
                    onViewFullSchedule={() => {}}
                    onToggleSave={(e, id) => handleToggleSaveTutor(e, id)}
                    isSaved={currentUser?.savedTutorIds?.includes(activeTutor.id) || false}
                />
            );
        
        case 'tutor-profile-editor':
             if (!currentUser || currentUser.role !== UserRole.TUTOR) return <div>Unauthorized</div>;
             const myTutorProfileToEdit = tutors.find(t => t.id === currentUser.id);
             if (!myTutorProfileToEdit) return <div>Error: Profile not found</div>;
             
             return (
                 <TutorProfileEditor 
                    tutor={myTutorProfileToEdit}
                    onSave={(updated) => { 
                        updateTutor(updated); 
                        // If we came from the public profile view (activeTutor matches currentUser), return there.
                        // Otherwise return to dashboard.
                        if (activeTutor && activeTutor.id === currentUser.id) {
                            navigate('tutor-profile');
                        } else {
                            navigate('tutor-dashboard');
                        }
                    }} 
                    onCancel={() => {
                        if (activeTutor && activeTutor.id === currentUser.id) {
                            navigate('tutor-profile');
                        } else {
                            navigate('tutor-dashboard');
                        }
                    }}
                />
             );

        case 'payment':
            if (!activeTutor || !bookingSlot || !currentUser) return null;
            return (
                <PaymentPage 
                    tutor={activeTutor}
                    slot={bookingSlot}
                    currentUser={currentUser}
                    onBack={() => navigate('tutor-profile')}
                    onConfirm={handleConfirmBooking}
                    onNavigate={navigate}
                />
            );

        case 'student-lessons':
            if (!currentUser) return null;
            return (
                <StudentLessonsPage 
                    currentUser={currentUser}
                    sessions={sessions}
                    onStartSession={startSession}
                    onReviewSession={(id) => alert(`Review ${id}`)}
                    onTopUp={() => alert("Top up modal")}
                    onCancelSession={(id) => alert(`Cancel ${id}`)}
                />
            );

        case 'student-saved-tutors':
            const savedTutorsList = tutors.filter(t => currentUser?.savedTutorIds?.includes(t.id));
            return (
                <SavedTutorsPage 
                    savedTutors={savedTutorsList}
                    onViewProfile={goToProfile}
                    onToggleSave={handleToggleSaveTutor}
                    onBook={(e, t) => handleBookingAttempt(t)}
                    onQuickBook={(e, t) => { e.stopPropagation(); handleBookingAttempt(t); }}
                    onSlotBook={(e, t, s) => { e.stopPropagation(); handleBookingAttempt(t, s); }}
                    onMessage={(e, t) => { e.stopPropagation(); handleMessageUser(t.id, t.name, t.imageUrl); }}
                    onBrowse={() => navigate('home')}
                />
            );

        case 'classroom':
            if (!activeSession) return null;
            return (
                <Classroom 
                    session={activeSession} 
                    onLeave={() => endSession(currentUser?.role === UserRole.TUTOR ? 'tutor-dashboard' : 'student-lessons')} 
                />
            );

        // --- Tutor Views ---
        case 'tutor-dashboard':
            if (!currentUser) return null;
            const myTutorProfile = tutors.find(t => t.id === currentUser.id);
            
            if (isManagingSchedule) {
                return (
                    <div className="container mx-auto px-4 py-8 max-w-7xl">
                        <TutorScheduleManager 
                            availability={myTutorProfile?.availability || []}
                            onUpdateAvailability={(slots) => { /* Update via api */ }}
                            onClose={() => setIsManagingSchedule(false)}
                            initialMode={scheduleMode}
                        />
                    </div>
                );
            }

            return (
                <>
                    <TutorDashboard 
                        currentUser={currentUser}
                        tutorProfile={myTutorProfile}
                        verificationStatus={myTutorProfile?.isVerified ? 'verified' : 'unverified'}
                        sessions={sessions}
                        onStartSession={startSession}
                        onCancelSession={(id) => alert('Cancel ' + id)}
                        onRescheduleSession={(id) => alert('Reschedule ' + id)}
                        theme={theme}
                        onEditProfile={() => navigate('tutor-profile-editor')}
                        onViewProfile={() => { if (myTutorProfile) goToProfile(myTutorProfile); }}
                        onUpdateSchedule={(mode) => { setScheduleMode(mode || 'calendar'); setIsManagingSchedule(true); }}
                        onQuickAction={(action) => {
                            if (action === 'schedule') setQuickActionType('Lesson');
                            if (action === 'timeoff') setQuickActionType('Time off');
                            if (action === 'extraslots') setQuickActionType('Extra slots');
                        }}
                        onViewCalendar={() => { setScheduleMode('calendar'); setIsManagingSchedule(true); }}
                        onManageCalendar={() => { setScheduleMode('calendar'); setIsManagingSchedule(true); }}
                        onAcceptRequest={(id) => console.log('Accept', id)}
                        onDeclineRequest={(id) => console.log('Decline', id)}
                        onManageVerification={() => setIsVerificationManagerOpen(true)}
                        onOpenChat={(uid, name) => handleMessageUser(uid, name)} 
                        onViewEarnings={() => navigate('tutor-earnings')}
                        onViewStudents={() => navigate('tutor-students')}
                    />
                    <Modal isOpen={!!quickActionType} onClose={() => setQuickActionType(null)} title="Manage Schedule">
                        {quickActionType && (
                            <TutorLessonScheduler 
                                initialTab={quickActionType}
                                onClose={() => setQuickActionType(null)}
                            />
                        )}
                    </Modal>
                </>
            );

        case 'tutor-students':
            return (
                <TutorStudentsPage 
                    students={students}
                    onMessage={(id, name) => handleMessageUser(id, name)}
                    onSchedule={(id) => { setQuickActionType('Lesson'); }}
                    onViewProfile={(id) => alert(`View Profile ${id}`)}
                    onViewHistory={(id) => alert(`History ${id}`)}
                    onArchive={(id) => alert(`Archive ${id}`)}
                    onNotes={(id) => alert(`Notes ${id}`)}
                    onBack={() => navigate('tutor-dashboard')}
                />
            );

        case 'tutor-earnings':
            if (!currentUser) return null;
            return <TutorEarningsPage currentUser={currentUser} onBack={() => navigate('tutor-dashboard')} theme={theme} />;

        // --- Admin Views ---
        case 'admin-dashboard':
            if (!currentUser) return null;
            return (
                <AdminDashboard 
                    currentUser={currentUser}
                    verificationRequests={verificationRequests}
                    sessions={sessions}
                    users={[]} // pass full list if needed
                    tutors={tutors}
                    admins={admins}
                    onAddAdmin={addAdmin}
                    onRemoveAdmin={removeAdmin}
                    onApproveVerification={id => updateVerificationStatus(id, 'approved')}
                    onRejectVerification={id => updateVerificationStatus(id, 'rejected')}
                    onForceCancelSession={(id) => alert("Session Cancelled")}
                    onViewProfile={goToProfile}
                    onNavigate={navigate}
                />
            );
        
        case 'admin-revenue': return <AdminRevenuePage onBack={() => navigate('admin-dashboard')} />;
        case 'admin-verifications':
            return (
                <AdminVerificationsPage 
                    requests={verificationRequests} 
                    tutors={tutors}
                    onApprove={id => updateVerificationStatus(id, 'approved')}
                    onReject={id => updateVerificationStatus(id, 'rejected')}
                    onBack={() => navigate('admin-dashboard')}
                    onViewProfile={goToProfile}
                />
            );
        case 'admin-sessions': return <AdminSessionsPage sessions={sessions} onBack={() => navigate('admin-dashboard')} />;
        case 'admin-tutors': return <AdminTutorsPage tutors={tutors} onBack={() => navigate('admin-dashboard')} onViewProfile={goToProfile} />;
        case 'admin-manage':
            return (
                <AdminManagePage 
                    admins={admins}
                    onAddAdmin={addAdmin}
                    onRemoveAdmin={removeAdmin}
                    onBack={() => navigate('admin-dashboard')}
                />
            );

        // --- Shared/Static Pages ---
        case 'settings':
            if (!currentUser) return null;
            return <SettingsPage currentUser={currentUser} onUpdateUser={updateUser} />;
        case 'referral':
            if (!currentUser) return null;
            return <ReferralPage currentUser={currentUser} onBack={() => navigate('home')} />;
        case 'legal-compliance': return <LegalPage onBack={() => navigate('admin-dashboard')} />;
        case 'terms': return <TermsPage onBack={() => navigate('home')} />;
        case 'privacy': return <PrivacyPage onBack={() => navigate('home')} />;
        case 'cookie-policy': return <CookiePolicyPage onBack={() => navigate('home')} />;
        case 'mobile-app': return <MobileAppPage onBack={() => navigate('home')} />;
        case 'success-stories': return <SuccessStoriesPage onBack={() => navigate('home')} />;
        case 'affiliate-program': return <AffiliateProgramPage onBack={() => navigate('home')} onJoin={() => navigate('become-tutor')} onLogin={() => navigate('login')} />;
        case 'become-tutor': return <BecomeTutorPage onBack={() => navigate('home')} onApply={() => alert("Apply logic")} />;
        case 'tutor-rules': return <TutorRulesPage onBack={() => navigate('home')} />;
        case 'cancellation-policy': return <CancellationPolicyPage onBack={() => navigate('home')} />;
        case 'support': return <SupportPage onBack={() => navigate('home')} onChat={() => setIsMessagingOpen(true)} />;
        case 'pricing': return <PricingPage onBack={() => navigate('home')} onNavigate={navigate} />;
        
        default: return <div>Page not found</div>;
    }
};
