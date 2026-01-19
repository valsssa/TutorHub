
import React, { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { NavigationProvider, useNavigation } from './contexts/NavigationContext';
import { DataProvider, useData } from './contexts/DataContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { AppRouter } from './components/layout/AppRouter';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { CookieBanner } from './components/shared/CookieBanner';
import { MessagingSystem } from './components/messaging/MessagingSystem';

// Intermediate component to consume contexts that App can't
const AppContent: React.FC = () => {
    const { currentUser } = useAuth();
    const { chats, sendMessage } = useData();
    const { navigate, currentView } = useNavigation();
    
    // UI state for messaging needs to be lifted to this layout level 
    // so it persists across route changes
    const [isMessagingOpen, setIsMessagingOpen] = useState(false);
    const [activeThreadId, setActiveThreadId] = useState<string | null>(null);

    return (
        <div className="flex flex-col min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
            {/* Navbar */}
            {currentView !== 'classroom' && (
                <Navbar onOpenChat={() => setIsMessagingOpen(true)} />
            )}

            {/* Main Router Logic */}
            <main className="flex-1">
                <AppRouter 
                    isMessagingOpen={isMessagingOpen} 
                    setIsMessagingOpen={setIsMessagingOpen}
                    activeThreadId={activeThreadId}
                    setActiveThreadId={setActiveThreadId}
                />
            </main>

            {/* Footer */}
            {currentView !== 'classroom' && currentView !== 'login' && (
                <Footer />
            )}

            {/* Global Overlays */}
            <CookieBanner onNavigate={navigate} />
            
            {currentUser && (
                <MessagingSystem 
                    currentUser={currentUser}
                    threads={chats}
                    activeThreadId={activeThreadId}
                    isOpen={isMessagingOpen}
                    onClose={() => setIsMessagingOpen(false)}
                    onSelectThread={setActiveThreadId}
                    onSendMessage={(threadId, text) => sendMessage(threadId, text, currentUser.id)}
                />
            )}
        </div>
    );
};

export const App: React.FC = () => {
    return (
        <ThemeProvider>
            <AuthProvider>
                <DataProvider>
                    <NavigationProvider>
                        <AppContent />
                    </NavigationProvider>
                </DataProvider>
            </AuthProvider>
        </ThemeProvider>
    );
};
