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
                        <label key={opt} className="q-opt">
                            <input
                                type="radio"
                                name={id}
                                value={opt}
                                checked={answer === opt}
                                onChange={() => onAnswer(id, opt)}
                            />
                            {opt}
                        </label>
                    ))
                ) : (
                    ["Yes", "No"].map((opt) => (
                        <label key={opt} className="q-opt">
                            <input
                                type="radio"
                                name={id}
                                value={opt}
                                checked={answer === opt}
                                onChange={() => onAnswer(id, opt)}
                            />
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