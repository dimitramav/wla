const QuizHeader = ({ level, onLevelChange }) => (
    <div className="quiz-header">
        <h2>Quiz</h2>
        <div className="quiz-controls">
            <label htmlFor="quiz-level">Level:</label>
            <select
                id="quiz-level"
                value={level}
                onChange={(e) => onLevelChange(Number(e.target.value || 1))}
            >
                <option value={1}>1 (Beginner)</option>
                <option value={2}>2 (Intermediate)</option>
                <option value={3}>3 (Advanced)</option>
            </select>
        </div>
    </div>
);

export default QuizHeader;