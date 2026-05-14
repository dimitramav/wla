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
                    (() => {
                        const groups = [];
                        bullets.forEach((b) => {
                            const t = b.trim();
                            if (t.startsWith('+')) {
                                if (groups.length) groups[groups.length - 1].subs.push(t.substring(1).trim());
                            } else {
                                const text = t.startsWith('*') ? t.substring(1).trim() : t.replace(/^\d+\.\s*/, '');
                                groups.push({ text, subs: [] });
                            }
                        });
                        return (
                            <div className="theory-cards">
                                {groups.map((g, i) => (
                                    <article
                                        key={i}
                                        className="theory-card"
                                        style={{ animationDelay: `${i * 60}ms` }}
                                    >
                                        <span className="theory-card__index">{i + 1}</span>
                                        <div className="theory-card__body">
                                            <h4 className="theory-card__title">{g.text}</h4>
                                            {g.subs.length > 0 && (
                                                <ul className="theory-card__subs">
                                                    {g.subs.map((s, j) => <li key={j}>{s}</li>)}
                                                </ul>
                                            )}
                                        </div>
                                    </article>
                                ))}
                            </div>
                        );
                    })()
                ) : (
                    <EmptyState
                        icon={FiBookOpen}
                        title="No theory yet"
                        message="Select a topic from the sidebar to see a summary here."
                        variant="empty"
                    />
                )
            )}

            {!loading && !error && bullets?.length > 0 && (
                <div className="panel-buttons">
                    <button className="btn btn-outline-primary" disabled={activeDrawer === 'quiz' && !quizError} onClick={() => onShow('progress')}><p>
                        Show Progress</p>
                    </button>
                    <button className="btn btn-outline-primary" disabled={activeDrawer === 'quiz' && !quizError} onClick={() => onShow('quiz')}><p>
                        Start Quiz</p>
                    </button>
                </div>
            )}
        </div>
    );
};

export default Theory;
