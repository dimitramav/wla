import { useTopic } from '../../hooks/useTopic';

const Theory = ({ onShow, activeDrawer }) => {
    const { topic, bullets, loading, error } = useTopic();

    return (
        <div className="theory-panel">
            <div className='header'>
                <h1>Theory at a glance</h1>
                <p className="panel-topic">Topic: {topic}</p>
            </div>

            {loading && <div className="panel-topic panel-message">Loading…</div>}
            {error && <div className="panel-topic panel-error">Failed to load.</div>}

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
                    <div className="panel-message">No summary available.</div>
                )
            )}

            <div className="panel-buttons">
                <button className="btn btn-outline-primary" disabled={activeDrawer === 'quiz'} onClick={onShow.bind(this, 'progress')}><p>
                    Show Progress</p>
                </button>
                <button className="btn btn-outline-primary" disabled={activeDrawer === 'quiz'} onClick={onShow.bind(this, 'quiz')}><p>
                    Start Quiz</p>
                </button>
            </div>
        </div>
    );
};

export default Theory;
