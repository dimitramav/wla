import { useState, useEffect } from 'react';
import { useQuiz } from '../../hooks/useQuiz';

import Loader from '../layout/widgets/Loader';
import { FiHelpCircle, FiAlertCircle } from 'react-icons/fi';
import EmptyState from '../layout/widgets/EmptyState';
import Header from '../layout/Header';
import QuizQuestion from './QuizQuestion';
import QuizScore from './QuizScore';
import { submitQuiz } from '../../api/quiz';
const Quiz = ({ topic, docsetHash, userId, PASS_THRESHOLD, onShowProgress, onError, onViewSource, onQuizReset, onClose }) => {

    const {
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
        setCurrentIndex,

    } = useQuiz(topic, docsetHash, userId);
    const [submitted, setSubmitted] = useState(false);
    console.log(weakKeywords)
    useEffect(() => { if (error && onError) onError(); }, [error]);
    if (error) return (
        <EmptyState
            icon={FiAlertCircle}
            title="Quiz not available"
            message="Failed to load questions. Please try again."
            variant="error"
        />
    );
    if (loading || level === null) return <Loader message="Preparing questions..." />;
    if (questions.length === 0) return (
        <EmptyState
            icon={FiHelpCircle}
            title="No questions"
            message="No questions were loaded for this level. Try selecting a different topic or difficulty."
            variant="empty"
        />
    );
    return (
        <div className="quiz-panel">
            <Header panel="quiz" title="Quiz" topic={topic} level={level} onLevelChange={handleLevelChange} selectLevel={submitted === false} subtitle={weakKeywords.join(", ")} onClose={submitted ? onClose : undefined} />

            {submitted ? (
                <QuizScore
                    questions={questions}
                    answers={answers}
                    level={level}
                    onShowProgress={onShowProgress}
                    onNewQuiz={(quizLevel) => { setSubmitted(false); handleLevelChange(quizLevel); onQuizReset?.(); }}
                    onViewSource={onViewSource}
                />
            ) : (
                <>
                    <div className="quiz-body">
                        <div className="q-slide-container">
                            <div className="q-slide" style={{
                                transform: `translateX(-${currentIndex * 100}%)`
                            }}>
                                {questions.map((question, idx) => (
                                    <QuizQuestion
                                        key={question.id}
                                        question={question}
                                        index={idx}
                                        answer={answers[question.id]}
                                        onAnswer={handleAnswer}
                                    />
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
                                onClick={async () => {
                                    const correctCount = questions.reduce((acc, q) => {
                                        const userAns = answers[q.id];
                                        const isCorrect = userAns != null && userAns.charAt(0) === q.correct.charAt(0);
                                        return acc + (isCorrect ? 1 : 0);
                                    }, 0);
                                    const passed = correctCount >= PASS_THRESHOLD;
                                    try {
                                        const result = await submitQuiz(
                                            topic,
                                            quizId,
                                            correctCount,
                                            passed,
                                            userId,
                                            answers
                                        );

                                        if (result?.success) {
                                            setSubmitted(true);
                                        } else {
                                            alert("Submission failed. Try again.");
                                        }
                                    } catch (err) {
                                        console.error("Submission error:", err);
                                        alert("Failed to submit quiz.");
                                    }
                                }}

                            >
                                Submit
                            </button>
                        )}
                    </div>
                </>
            )
            }
        </div >

    );
};

export default Quiz;