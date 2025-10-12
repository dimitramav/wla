import { useProfile } from "../../hooks/useProfile";
import { useAuth } from "../../context/AuthContext";
const QuizHeader = ({ topic, level, onLevelChange, selectLevel }) => {
    const { user } = useAuth();
    console.log(topic, user);
    const { unlockedLevel } = useProfile(topic, user?.id);
    console.log("unlockedLevel", unlockedLevel);

    return (
        <div className="quiz-header">
            <h2>Quiz</h2>
            {selectLevel && (
                <div className="quiz-controls">
                    <label htmlFor="quiz-level">Level:</label>
                    <select
                        id="quiz-level"
                        value={level}
                        onChange={(e) => onLevelChange(Number(e.target.value || 1))}
                    >
                        <option value={1}>1 (Beginner)</option>
                        <option value={2} disabled={unlockedLevel < 2}>2 (Intermediate)</option>
                        <option value={3} disabled={unlockedLevel < 3}>3 (Advanced)</option>
                    </select>
                </div>
            )}
        </div>
    );
};
export default QuizHeader;