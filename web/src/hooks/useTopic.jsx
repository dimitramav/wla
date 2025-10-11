import { useMemo, useEffect, useState } from 'react';
import { getTopicSummary } from '../api/theory';

export function useTopic() {
    const topic = useMemo(() => 'school_anxiety', []);
    const [bullets, setBullets] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [docsetHash, setDocsetHash] = useState(null);
    useEffect(() => {
        let alive = true;
        setLoading(true);

        getTopicSummary(topic)
            .then(data => {
                if (!alive) return;
                setBullets(data?.bullets || []);
                setDocsetHash(data?.hash || null);
                setError(null);
            })
            .catch(e => {
                if (!alive) return;
                setError(e?.message || 'error');
                setBullets([]);
            })
            .finally(() => {
                if (alive) setLoading(false);
            });

        return () => { alive = false; };
    }, [topic]);

    return { topic, bullets, loading, error, docsetHash };
}
