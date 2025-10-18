import { useProfile } from "../../hooks/useProfile";
import { useAuth } from "../../context/AuthContext";
const Header = ({ title, panel, topic, level = 1, onLevelChange = () => { }, subtitle = "", selectLevel = false }) => {
    const { user } = useAuth();
    const { unlockedLevel } = useProfile(topic, user?.id);
    return (
        <div className="header">
            <div className="title-section">
                <h2>{title}</h2>
                {subtitle && <p className="subtitle"><b>Areas to strengthen:</b> {subtitle}</p>}
            </div>
            {panel === "quiz" ? (
                selectLevel && (

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
                )) : (<p className="panel-topic">Topic: {topic}</p>
            )}
        </div>
    );
};
export default Header;