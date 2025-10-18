/**
 *
 * This file provides the authentication context for the application.
 *
 * Key Features:
 * - Defines the `AuthProvider` component to manage authentication state.
 * - Exposes the `useAuth` hook for accessing authentication context.
 * - Handles user login, signup, logout, and session persistence.
 */

import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { login, signup, logout, me } from '../api/auth';

const Ctx = createContext(null);


export function useAuth() {
    const ctx = useContext(Ctx);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    useEffect(() => {
        (async () => {
            try {
                const data = await me();
                setUser(data.user);
            } catch {
                setUser(null);
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    const value = useMemo(() => ({
        user,
        loading,
        async signup(p) {
            const data = await signup(p);
            setUser(data.user);
        },
        async login(p) {
            const data = await login(p);
            setUser(data.user);
        },
        async logout() {
            await logout();
            setUser(null);
        }
    }), [user, loading]);

    return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
