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
    const [weakKeywords, setWeakKeywords] = useState([]);
    console.log(userId)

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
            console.log(data)
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
        console.log("useQuiz effect:", { docsetHash, userId, level, currentIndex });
        if (docsetHash && userId) {
            loadQuiz(level);
        }
    }, [docsetHash, userId, level]);

    // load quiz when: level changes, docsetHash or userId changes, repeat level requested
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