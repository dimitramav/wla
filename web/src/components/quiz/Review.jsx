
import { FaCheckCircle, FaTimesCircle } from "react-icons/fa";

const QuizReview = ({ questions, answers, level, onRetake, onNextLevel, onShowProgress }) => {
    console.log(questions, answers);
    const results = questions.map(q => {
        const userAnswer = answers[q.id];
        const isCorrect = userAnswer === q.correct;
        return {
            ...q,
            userAnswer,
            isCorrect,
        };
    });

    const correctCount = results.filter(r => r.isCorrect).length;
    const passed = correctCount >= 12;

    return (
        <div className="quiz-review">
            <div className="quiz-results">
                <h3> Result: <b className={passed ? "pass" : "fail"}>{passed ? "Pass" : "Fail"}</b>
                </h3>
                <p>
                    You answered <b>{correctCount}</b> out of <b>{questions.length}</b> correctly.
                </p>
            </div>
            <div className="review-list">
                {results.map((q, idx) => (
                    <div key={q.id} className={`review-item ${q.isCorrect ? "correct" : "incorrect"}`}>
                        <div className="review-header">
                            <span><b>{idx + 1}.</b> {q.text}</span>
                            {q.isCorrect ? (
                                <FaCheckCircle className="icon success" />
                            ) : (
                                <FaTimesCircle className="icon fail" />
                            )}
                        </div>
                        <div className="review-answers">
                            <div className={q.isCorrect ? "pass" : "fail"}><strong>Your answer:</strong> {q.userAnswer}</div>
                            {!q.isCorrect && (
                                <>
                                    <div><strong>Correct answer:</strong> {q.correct}</div>
                                    <div className="review-why"><strong>Why:</strong> {q.why}</div>
                                </>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            <div className="quiz-review-actions">
                <button className="btn btn-outline-accent" onClick={onShowProgress}>Show Progress</button>
                {passed && level < 3 ? (
                    <button className="btn btn-accent" onClick={onNextLevel}>{`Start Level ${level + 1}`} </button>
                ) : (
                    <button className="btn btn-accent" onClick={onRetake}>{`Repeat Level ${level}`}</button>
                )}
            </div>
        </div>
    );
};

export default QuizReview;
