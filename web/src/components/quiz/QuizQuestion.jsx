const QuizQuestion = ({ question, index, answer, onAnswer }) => {
    const { id, text, kind, options, keywords } = question;
    return (
        <div className="q-card">
            <div className="q-top">
                <div className="q-text">
                    <b>{index + 1}.</b>{text}
                </div>
            </div>

            <div className="q-options">
                {kind === "mcq" ? (
                    (options || []).map((opt) => (
                        <label key={opt} className={`q-opt${answer === opt ? ' selected' : ''}`}>
                            <span className="q-opt-bullet">
                                <input
                                    type="radio"
                                    name={id}
                                    value={opt}
                                    checked={answer === opt}
                                    onChange={() => onAnswer(id, opt)}
                                />
                                <svg
                                    className="q-opt-circle"
                                    viewBox="0 0 26 26"
                                    aria-hidden="true"
                                >
                                    <path
                                        d="M 13,2.5 C 20.5,2 25,8 24,14 C 23,20.5 18,25.5 12,24.5 C 6,23.5 1,18 1.5,12 C 2,5.5 7.5,1.5 13,2.5 C 14.5,2 16,2.5 15,3.5"
                                        className={`q-opt-circle-stroke${answer === opt ? ' active' : ''}`}
                                        pathLength="100"
                                    />
                                </svg>
                            </span>
                            {opt}
                        </label>
                    ))
                ) : (
                    ["Yes", "No"].map((opt) => (
                        <label key={opt} className={`q-opt${answer === opt ? ' selected' : ''}`}>
                            <span className="q-opt-bullet">
                                <input
                                    type="radio"
                                    name={id}
                                    value={opt}
                                    checked={answer === opt}
                                    onChange={() => onAnswer(id, opt)}
                                />
                                <svg
                                    className="q-opt-circle"
                                    viewBox="0 0 26 26"
                                    aria-hidden="true"
                                >
                                    <path
                                        d="M 13,2.5 C 20.5,2 25,8 24,14 C 23,20.5 18,25.5 12,24.5 C 6,23.5 1,18 1.5,12 C 2,5.5 7.5,1.5 13,2.5 C 14.5,2 16,2.5 15,3.5"
                                        className={`q-opt-circle-stroke${answer === opt ? ' active' : ''}`}
                                        pathLength="100"
                                    />
                                </svg>
                            </span>
                            {opt === "Yes" ? "True" : "False"}
                        </label>
                    ))
                )}
            </div>

            <div className="q-bottom">
                {Array.isArray(keywords) && keywords.length > 0 && (
                    <div className="q-tags">
                        {keywords.map((kw, j) => (
                            <span key={j} className="q-tag">{kw}</span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
export default QuizQuestion;