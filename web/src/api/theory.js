import { apiGet } from './client';
export async function getSummary(lesson) {
    return apiGet(`/api/${lesson}/theory/summary`);
}