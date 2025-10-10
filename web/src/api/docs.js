import { apiGet } from './client';

export async function getDocs(topic) {
    return apiGet(`/api/${topic}/docs`);
}