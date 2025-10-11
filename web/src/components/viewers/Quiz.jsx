import { useEffect, useMemo, useState } from "react";
import { startQuiz } from "../../api/quiz";
import { useTopic } from '../../hooks/useTopic';


const Quiz = () => {
    const [level, setLevel] = useState(1);
    const [loading, setLoading] = useState(false);
    const [quizId, setQuizId] = useState(null);
    const [questions, setQuestions] = useState([]);
    const [answers, setAnswers] = useState({});
    const [error, setError] = useState(null);
    const [currentIndex, setCurrentIndex] = useState(0);

    const { topic } = useTopic();

    async function loadQuiz(targetLevel = level) {
        setLoading(true);
        setError(null);
        setAnswers({});
        setQuestions([]);
        setQuizId(null);
        setCurrentIndex(0);
        try {
            const data = await startQuiz(topic, targetLevel);
            setQuizId(data.quizId || null);
            setQuestions(Array.isArray(data.questions) ? data.questions : []);
        } catch (e) {
            console.error("Error loading quiz:", e);
            setError(e?.message || "Failed to start quiz");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadQuiz(level);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const allAnswered =
        questions.length > 0 && questions.every((q) => answers[q.id] !== undefined);

    const handlePick = (qid, val) => {
        setAnswers((prev) => ({ ...prev, [qid]: val }));
    };

    return (
        <div className="quiz-panel">
            <div className="quiz-header">
                <h2>Quiz</h2>
                <div className="quiz-controls">
                    <label htmlFor="quiz-level">
                        Level:
                    </label>
                    <select
                        id="quiz-level"
                        value={level}
                        onChange={(e) => {
                            const next = Number(e.target.value || 1);
                            setLevel(next);
                            setCurrentIndex(0);
                            loadQuiz(next);
                        }}
                    >
                        <option value={1}>1 (Beginner)</option>
                        <option value={2}>2 (Intermediate)</option>
                        <option value={3}>3 (Advanced)</option>
                    </select>

                </div>
            </div>

            {error && <div className="error">{error}</div>}

            {loading ? (
                <div className="loading">Loading…</div>
            ) : questions.length === 0 ? (
                <div className="error">No questions available.</div>
            ) : (
                <>
                    <div className="quiz-body">
                        <div className="q-slide-container">
                            <div
                                className="q-slide"
                                style={{
                                    transform: `translateX(-${currentIndex * 100}%)`,
                                }}
                            >
                                {questions.map((q, idx) => (
                                    <div key={q.id} className="q-card">
                                        <div className="q-top">
                                            <div className="q-text">
                                                <b>{idx + 1}.</b>{q.text}
                                            </div>

                                        </div>

                                        <div className="q-options">
                                            {q.kind === "mcq" ? (
                                                (q.options || []).map((opt) => (
                                                    <label key={opt} className="q-opt">
                                                        <input
                                                            type="radio"
                                                            name={q.id}
                                                            value={opt}
                                                            checked={answers[q.id] === opt}
                                                            onChange={() => handlePick(q.id, opt)}
                                                        />
                                                        {opt}
                                                    </label>
                                                ))
                                            ) : (
                                                ["Yes", "No"].map((opt) => (
                                                    <label key={opt} className="q-opt">
                                                        <input
                                                            type="radio"
                                                            name={q.id}
                                                            value={opt}
                                                            checked={answers[q.id] === opt}
                                                            onChange={() => handlePick(q.id, opt)}
                                                        />
                                                        {opt}
                                                    </label>
                                                ))
                                            )}
                                        </div>
                                        <div className="q-bottom">{Array.isArray(q.keywords) && q.keywords.length > 0 && (
                                            <div className="q-tags">
                                                {q.keywords.map((kw, j) => (
                                                    <span key={j} className="q-tag">{kw}</span>
                                                ))}
                                            </div>
                                        )}</div>
                                    </div>
                                ))}
                            </div>
                        </div>


                    </div>

                    <div className="quiz-navigation">
                        {currentIndex < questions.length - 1 ? (
                            <button
                                className="btn btn-outline-accent"
                                disabled={answers[questions[currentIndex]?.id] === undefined}
                                onClick={() => setCurrentIndex(currentIndex + 1)}
                            >
                                Next
                            </button>
                        ) : (
                            <button
                                className="btn btn-accent"
                                disabled={!allAnswered || loading}
                                onClick={() => {
                                    console.log("Submit payload:", { quizId, topic, level, answers });
                                    alert("Submit wiring will be added.");
                                }}
                            >
                                Submit
                            </button>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default Quiz;
