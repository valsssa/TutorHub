
import React, { createContext, useContext, useState } from 'react';
import { User, UserRole } from '../domain/types';
import { api } from '../services/api';

interface AuthContextType {
    currentUser: User | null;
    login: (email: string, role: UserRole) => Promise<void>;
    logout: () => void;
    updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [currentUser, setCurrentUser] = useState<User | null>(null);

    const login = async (email: string, role: UserRole) => {
        try {
            const user = await api.auth.login(email, role);
            setCurrentUser(user);
        } catch (error) {
            console.error("Login failed", error);
            throw error;
        }
    };

    const logout = () => {
        setCurrentUser(null);
    };

    const updateUser = (user: User) => {
        setCurrentUser(user);
    };

    return (
        <AuthContext.Provider value={{ currentUser, login, logout, updateUser }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error("useAuth must be used within an AuthProvider");
    return context;
};
