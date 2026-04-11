import { apiGet } from './client';

export async function getTopics() {
    return apiGet('/api/topics');
}
