import { apiGet } from './client';

export async function getDocs(lesson) {
    return apiGet(`/api/${lesson}/docs`);
}