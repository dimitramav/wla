import { useState, useEffect } from 'react';
import { startQuiz } from '../api/quiz';

export const useQuiz = (topic, docsetHash, userId) => {
    const [level, setLevel] = useState(1);
    const [loading, setLoading] = useState(false);
    const [quizId, setQuizId] = useState(null);
    const [questions, setQuestions] = useState([]);
    const [answers, setAnswers] = useState({});
    const [error, setError] = useState(null);
    const [currentIndex, setCurrentIndex] = useState(0);

    const loadQuiz = async (targetLevel = level) => {
        setLoading(true);
        setError(null);
        setAnswers({});
        setQuestions([]);
        setQuizId(null);
        setCurrentIndex(0);

        try {
            const data = await startQuiz(topic, targetLevel, userId, docsetHash);
            setQuizId(data.quizId || null);
            setQuestions(Array.isArray(data.questions) ? data.questions : []);
        } catch (e) {
            console.error("Error loading quiz:", e);
            setError(e?.message || "Failed to start quiz");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (docsetHash && userId) {
            loadQuiz(level);
        }
    }, [docsetHash, userId, level]);

    const handleLevelChange = (newLevel) => {
        setLevel(newLevel);
        setCurrentIndex(0);
        loadQuiz(newLevel);
    };

    const handleAnswer = (qid, val) => {
        setAnswers(prev => ({ ...prev, [qid]: val }));
    };

    const allAnswered = questions.length > 0 &&
        questions.every(q => answers[q.id] !== undefined);

    return {
        level,
        loading,
        quizId,
        questions,
        answers,
        error,
        currentIndex,
        allAnswered,
        handleLevelChange,
        handleAnswer,
        setCurrentIndex
    };
};