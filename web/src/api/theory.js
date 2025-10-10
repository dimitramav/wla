import { API_BASE } from './client';

export async function getTopicSummary(topic) {
    const res = await fetch(`${API_BASE}/api/topics/${topic}/summary`, {
        method: 'GET',
        credentials: 'include',
    });
    if (!res.ok) throw new Error('summary fetch failed');
    return res.json();
}
