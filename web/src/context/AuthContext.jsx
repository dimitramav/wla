import { createContext, useContext } from 'react';

const Ctx = createContext({ isAuthed: true });

export function useAuth() { return useContext(Ctx); }

export function AuthProvider({ children }) {
    return <Ctx.Provider value={{ isAuthed: true }}>{children}</Ctx.Provider>;
}