import { useEffect, useState } from 'react';
import { getDocs } from '../api/docs';
import { useTopic } from '../context/TopicContext';

export const useDocs = () => {
    const { topic } = useTopic();
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!topic) return;
        setLoading(true);
        setError(null);
        getDocs(topic)
            .then(d => setDocs(d.docs || []))
            .catch(() => setError(true))
            .finally(() => setLoading(false));
    }, [topic]);

    return { docs, loading, error };
};
