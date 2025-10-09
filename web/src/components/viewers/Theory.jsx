import { useTopic } from '../../hooks/useTopic';

const Theory = () => {
    const { topic, bullets, loading, error } = useTopic();

    return (
        <div className="theory-panel">
            <div className="panel-content">
                <h2 className="panel-title">Theory at a glance</h2>
                <p className="panel-topic">Topic: {topic}</p>

                {loading && <div className="panel-message">Loading…</div>}
                {error && <div className="panel-error">Failed to load.</div>}

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
                    <button className="panel-button">Show Progress</button>
                    <button className="panel-button">Start Quiz</button>
                </div>
            </div>
        </div>
    );
};

export default Theory;
