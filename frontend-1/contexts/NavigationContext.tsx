
import React, { createContext, useContext, useState } from 'react';
import { ViewState, Tutor, Session } from '../domain/types';

interface NavigationContextType {
    currentView: ViewState;
    activeTutor: Tutor | null;
    bookingSlot: string | null;
    activeSession: Session | null;
    navigate: (view: ViewState) => void;
    goToProfile: (tutor: Tutor) => void;
    goToBooking: (tutor: Tutor, slot?: string) => void;
    startSession: (session: Session) => void;
    endSession: (redirectView: ViewState) => void;
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

export const NavigationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [currentView, setCurrentView] = useState<ViewState>('home');
    const [activeTutor, setActiveTutor] = useState<Tutor | null>(null);
    const [bookingSlot, setBookingSlot] = useState<string | null>(null);
    const [activeSession, setActiveSession] = useState<Session | null>(null);

    const navigate = (view: ViewState) => {
        // Pages that should NOT clear the booking flow/profile state
        const preserveStateViews: ViewState[] = ['payment', 'tutor-profile', 'tutor-profile-editor', 'terms', 'privacy', 'cancellation-policy', 'cookie-policy'];
        
        if (!preserveStateViews.includes(view)) {
            setBookingSlot(null);
            setActiveTutor(null);
        }
        
        setCurrentView(view);
    };

    const goToProfile = (tutor: Tutor) => {
        setActiveTutor(tutor);
        setCurrentView('tutor-profile');
    };

    const goToBooking = (tutor: Tutor, slot?: string) => {
        setActiveTutor(tutor);
        if (slot) setBookingSlot(slot);
        setCurrentView('payment');
    };

    const startSession = (session: Session) => {
        setActiveSession(session);
        setCurrentView('classroom');
    };

    const endSession = (redirectView: ViewState) => {
        setActiveSession(null);
        setCurrentView(redirectView);
    };

    return (
        <NavigationContext.Provider value={{ 
            currentView, activeTutor, bookingSlot, activeSession, 
            navigate, goToProfile, goToBooking, startSession, endSession 
        }}>
            {children}
        </NavigationContext.Provider>
    );
};

export const useNavigation = () => {
    const context = useContext(NavigationContext);
    if (!context) throw new Error("useNavigation must be used within a NavigationProvider");
    return context;
};
