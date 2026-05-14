import { FaCheckCircle, FaTimesCircle } from "react-icons/fa";
import { FiBookOpen } from "react-icons/fi";
const PASS_THRESHOLD = import.meta.env.PASS_THRESHOLD;

const QuizScore = ({ questions, answers, level, onNewQuiz, onShowProgress, onViewSource }) => {
    const results = questions.map(q => {
        const userAnswer = answers[q.id];
        const isCorrect = userAnswer && q.correct && userAnswer.charAt(0) === q.correct.charAt(0); return {
            ...q,
            userAnswer,
            isCorrect,
        };
    });

    const correctCount = results.filter(r => r.isCorrect).length;
    const passed = correctCount >= PASS_THRESHOLD;
    return (
        <div className="quiz-score">
            <div className="quiz-results">
                <h3> Result: <b className={passed ? "pass" : "fail"}>{passed ? "Pass" : "Fail"}</b>
                </h3>
                <p>
                    You answered <b>{correctCount}</b> out of <b>{questions.length}</b> correctly.
                </p>
            </div>
            <div className="score-list">
                {results.map((q, idx) => (
                    <div key={q.id} className={`score-item ${q.isCorrect ? "correct" : "incorrect"}`}>
                        <div className="score-header">
                            <span><b>{idx + 1}.</b> {q.text}</span>
                            {q.isCorrect ? (
                                <FaCheckCircle className="icon success" />
                            ) : (
                                <FaTimesCircle className="icon fail" />
                            )}
                        </div>
                        <div className="score-answers">
                            <div className={q.isCorrect ? "pass" : "fail"}><strong>Your answer:</strong> {q.userAnswer}</div>
                            {!q.isCorrect && (
                                <div><strong>Correct answer:</strong> {q.correct}</div>
                            )}
                            <div className="score-why">
                                <span className="why-text">
                                    {!q.isCorrect && <><strong>Why:</strong> {q.why}</>}
                                </span>
                                {q.source_spans?.[0]?.text && onViewSource && (
                                    <button
                                        className="btn-view-source"
                                        onClick={() => onViewSource(q.source_spans[0].doc, q.source_spans[0].text)}
                                    >
                                        <FiBookOpen /> View Source
                                    </button>
                                )}
                            </div>
                            {Array.isArray(q.keywords) && q.keywords.length > 0 && (
                                <div className="q-tags">
                                    {q.keywords.map((kw, j) => (
                                        <span key={j} className="q-tag">{kw}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            <div className="quiz-score-actions">
                <button className="btn btn-outline-accent" onClick={onShowProgress}>Show Progress</button>
                {passed && level < 3 ? (
                    <button className="btn btn-accent" onClick={() => onNewQuiz(level + 1)}>{`Start Level ${level + 1}`} </button>
                ) : (
                    <button className="btn btn-accent" onClick={() => onNewQuiz(level)}>{`Repeat Level ${level}`}</button>
                )}
            </div>
        </div>
    );
};

export default QuizScore;
