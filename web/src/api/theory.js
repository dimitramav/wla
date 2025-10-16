import { apiGet } from './client';

export async function getTopicSummary(topic) {
    return apiGet(`/api/topics/${topic}/summary`);

}
