import { apiPost } from './client';

export async function startQuiz(topic, level, uid, docsetHash, weakFocusRatio) {
    const res = await apiPost(`/api/${topic}/quiz/start`, { level, uid, docsetHash, weakFocusRatio });
    console.log(res);
    return res; // { quizId, level, questions: [...] }
}

export async function submitQuiz(topic, quizId, correctCount, passed, userId, answers) {
    const res = await apiPost(`/api/${topic}/quiz/submit`, { quizId, correctCount, passed, userId, answers });
    return res; // { success: true }
}