import { useTopic } from '../../hooks/useTopic';

const Theory = () => {
    const { topic, bullets, loading, error } = useTopic();

    return (
        <div className="theory-panel">
            <div className="p-4">
                <h2 className="font-semibold mb-2">Theory (Deterministic Summary)</h2>
                <p className="text-sm text-gray-600">Topic: {topic}</p>

                {loading && <div className="mt-3 text-sm text-gray-500">Loading…</div>}
                {error && <div className="mt-3 text-sm text-red-600">Failed to load.</div>}

                {!loading && !error && (
                    bullets?.length ? (
                        <ul className="mt-3 list-disc pl-5">
                            {bullets.map((b, i) => <li key={i}>{b}</li>)}
                        </ul>
                    ) : (
                        <div className="mt-3 text-sm text-gray-500">No summary available.</div>
                    )
                )}

                <div className="mt-4 flex gap-2">
                    <button className="px-3 py-2 border rounded">Show Progress</button>
                    <button className="px-3 py-2 border rounded">Start Quiz</button>
                </div>
            </div>
        </div>
    );
};

export default Theory;
