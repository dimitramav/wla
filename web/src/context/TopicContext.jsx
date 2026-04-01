import { createContext, useContext, useState, useEffect, useMemo } from 'react';
import { getTopicSummary } from '../api/theory';

const TopicCtx = createContext(null);

export function useTopic() {
    const ctx = useContext(TopicCtx);
    if (!ctx) throw new Error('useTopic must be used within TopicProvider');
    return ctx;
}

export function TopicProvider({ children }) {
    const [topic, setTopic] = useState('school_anxiety');
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

    const value = useMemo(() => ({
        topic, setTopic, bullets, loading, error, docsetHash
    }), [topic, bullets, loading, error, docsetHash]);

    return <TopicCtx.Provider value={value}>{children}</TopicCtx.Provider>;
}
