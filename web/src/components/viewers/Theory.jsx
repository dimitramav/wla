import { FiBookOpen, FiAlertCircle } from 'react-icons/fi';
import { useTopic } from '../../hooks/useTopic';
import EmptyState from '../layout/widgets/EmptyState';

const Theory = ({ onShow, activeDrawer, quizError }) => {
    const { topic, bullets, loading, error } = useTopic();

    return (
        <div className="theory-panel">
            <div className='header'>
                <h1>Theory at a glance</h1>
                <p className="panel-topic">Topic: {topic}</p>
            </div>

            {loading && <div className="panel-topic panel-message">Loading…</div>}

            {!loading && error && (
                <EmptyState
                    icon={FiAlertCircle}
                    title="Failed to load"
                    message="Unable to fetch theory content. Please try again."
                    variant="error"
                />
            )}

            {!loading && !error && (
                bullets?.length ? (
                    <ul className="bullet-list">
                        {bullets.map((b, i) => {
                            const trimmed = b.trim();

                            if (trimmed.startsWith('+')) {
                                return (
                                    <li key={i} className="bullet sub-bullet">
                                        {trimmed.substring(1).trim()}
                                    </li>
                                );
                            }

                            if (trimmed.startsWith('*')) {
                                return (
                                    <li key={i} className="bullet main-bullet">
                                        {trimmed.substring(1).trim()}
                                    </li>
                                );
                            }

                            return (
                                <li key={i} className="bullet main-bullet">
                                    {trimmed}
                                </li>
                            );
                        })}
                    </ul>
                ) : (
                    <EmptyState
                        icon={FiBookOpen}
                        title="No theory yet"
                        message="Select a topic from the sidebar to see a summary here."
                        variant="empty"
                    />
                )
            )}

            <div className="panel-buttons">
                <button className="btn btn-outline-primary" disabled={activeDrawer === 'quiz' && !quizError} onClick={onShow.bind(this, 'progress')}><p>
                    Show Progress</p>
                </button>
                <button className="btn btn-outline-primary" disabled={activeDrawer === 'quiz' && !quizError} onClick={onShow.bind(this, 'quiz')}><p>
                    Start Quiz</p>
                </button>
            </div>
        </div>
    );
};

export default Theory;
