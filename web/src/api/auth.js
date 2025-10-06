import { API_BASE } from './client';

export async function signup(payload) {
    const res = await fetch(`${API_BASE}/api/auth/signup`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('signup failed');
    return res.json();
}

export async function login(payload) {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('login failed');
    return res.json();
}

export async function logout() {
    const res = await fetch(`${API_BASE}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include',
    });
    if (!res.ok && res.status !== 204) throw new Error('logout failed');
}

export async function me() {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
        credentials: 'include',
    });
    if (!res.ok) throw new Error('unauthorized');
    return res.json();
}
