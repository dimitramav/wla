export const API_BASE = import.meta.env.VITE_API_BASE;
export async function apiGet(path) {
    const res = await fetch(`${API_BASE}${path}`, { credentials: 'include' });
    if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
    return res.json();
}

export async function apiPost(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const msg = await res.text().catch(() => '');
        throw new Error(`POST ${path} failed: ${res.status} ${msg}`);
    }
    return res.json();
}