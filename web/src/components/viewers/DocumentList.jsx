import { useEffect, useState } from 'react';
import { getDocs } from '../../api/docs';
import { useLesson } from '../../hooks/useLesson';

export default function DocumentList({ onSelect }) {
    const { lesson } = useLesson();
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getDocs(lesson).then(d => { console.log(d); setDocs(d.docs || []) }).finally(() => setLoading(false));
    }, [lesson]);



    if (loading) return <div className=" text-sm text-gray-500">Loading docs…</div>;
    if (!docs.length) return <div className="text-sm text-gray-500">No PDFs found.</div>;

    return (
        <div>
            {docs.map(doc => (
                <button
                    key={doc.url}
                    className="block w-full text-left border rounded hover:bg-gray-50"
                    onClick={() => onSelect(doc.url)}
                >
                    {doc.name}
                </button>
            ))}
        </div>
    );
}
