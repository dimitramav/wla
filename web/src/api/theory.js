import { apiGet } from './client';
export async function getSummary(topic) {
    return apiGet(`/api/${topic}/theory/summary`);
}