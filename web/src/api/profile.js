import { apiPost } from './client';
export async function getProfile(topic, userId) {
    return apiPost(`/api/${topic}/profile`, { userId });
}
