import { apiPost } from './client';

export async function startQuiz(topic, level, uid, docsetHash) {
    const res = await apiPost(`/api/${topic}/quiz/start`, { level, uid, docsetHash });
    return res; // { quizId, level, questions: [...] }
}
