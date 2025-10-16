import { useState } from 'react';
import { useQuiz } from '../../hooks/useQuiz';

import Loader from '../layout/widgets/Loader';
import Header from '../layout/Header';
import QuizQuestion from './QuizQuestion';
import QuizScore from './QuizScore';
import { submitQuiz } from '../../api/quiz';
const Quiz = ({ topic, docsetHash, userId, PASS_THRESHOLD, onShowProgress }) => {

    const {
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
        setCurrentIndex,
    } = useQuiz(topic, docsetHash, userId);
    console.log(quizId);
    const [submitted, setSubmitted] = useState(false);
    if (error) return <div className="error">{error}</div>;
    if (loading) return <Loader message="Preparing questions..." />;
    if (questions.length === 0) return <Loader message="No questions available..." />;
    return (
        <div className="quiz-panel">
            <Header panel="quiz" title="Quiz" topic={topic} level={level} onLevelChange={handleLevelChange} selectLevel={submitted === false} />

            {submitted ? (
                <QuizScore
                    questions={questions}
                    answers={answers}
                    level={level}
                    onShowProgress={onShowProgress}
                    onNewQuiz={(quizLevel) => { setSubmitted(false); handleLevelChange(quizLevel); }}
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
                                        return acc + (answers[q.id] === q.correct ? 1 : 0);
                                    }, 0);
                                    const passed = correctCount >= PASS_THRESHOLD;
                                    try {
                                        const success = await submitQuiz(
                                            topic,
                                            quizId,
                                            correctCount,
                                            passed,
                                            userId,
                                            answers
                                        );

                                        if (success) {
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