import { apiPost } from './client';

export async function startQuiz(topic, level) {
    const res = await apiPost(`/api/${topic}/quiz/start`, { level });
    return res; // { quizId, level, questions: [...] }
}
