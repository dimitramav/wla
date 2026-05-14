import { useState, useEffect } from 'react';
import { startQuiz } from '../api/quiz';
import { useProfile } from './useProfile';

export const useQuiz = (topic, docsetHash, userId) => {
    const { unlockedLevel, loading: profileLoading } = useProfile(topic, userId);
    const [level, setLevel] = useState(null);
    const [loading, setLoading] = useState(false);
    const [quizId, setQuizId] = useState(null);
    const [questions, setQuestions] = useState([]);
    const [answers, setAnswers] = useState({});
    const [error, setError] = useState(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [weakKeywords, setWeakKeywords] = useState([]);

    useEffect(() => {
        if (level === null && !profileLoading) setLevel(unlockedLevel || 1);
    }, [profileLoading, unlockedLevel, level]);

    const loadQuiz = async (targetLevel = level) => {
        setLoading(true);
        setError(null);
        setAnswers({});
        setQuestions([]);
        setQuizId(null);
        setCurrentIndex(0);
        const weakFocusRatio = 0.65;
        try {
            const data = await startQuiz(topic, targetLevel, userId, docsetHash, weakFocusRatio);
            setQuizId(data.quizId || null);
            setWeakKeywords(data.weak_keywords || []);
            setQuestions(Array.isArray(data.questions) ? data.questions : []);
        } catch (e) {
            console.error("Error loading quiz:", e);
            setError(e?.message || "Failed to start quiz");
        } finally {
            setLoading(false);
        }
    };
    useEffect(() => {
        if (docsetHash && userId && level !== null) {
            loadQuiz(level);
        }
    }, [docsetHash, userId, level]);

    // Same-level requests need an explicit reload because setLevel(newLevel) would be a no-op and the level-change effect wouldn't fire.
    const handleLevelChange = (newLevel) => {
        if (newLevel === level) {
            loadQuiz(newLevel);
        } else {
            setLevel(newLevel);
        }
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
        weakKeywords,
        handleLevelChange,
        handleAnswer,
        setCurrentIndex
    };
};