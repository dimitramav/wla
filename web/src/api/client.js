export const API_BASE = import.meta.env.VITE_API_BASE;
export async function apiGet(path) {
    const res = await fetch(`${API_BASE}${path}`, { credentials: 'include' });
    if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
    return res.json();
}
