import { useEffect, useRef, useState } from 'react';
import { getDocs } from '../../api/docs';
import { useTopic } from '../../hooks/useTopic';
import { FiChevronLeft, FiChevronRight, FiFile, FiAlertCircle } from 'react-icons/fi';
import EmptyState from '../layout/widgets/EmptyState';

const SCROLL_AMOUNT = 240;

const DocumentList = ({ onSelect }) => {
    const { topic } = useTopic();
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedUrl, setSelectedUrl] = useState(null);
    const [canScrollLeft, setCanScrollLeft] = useState(false);
    const [canScrollRight, setCanScrollRight] = useState(false);
    const rowRef = useRef(null);

    useEffect(() => {
        setLoading(true);
        setError(null);
        getDocs(topic)
            .then(d => {
                const docList = d.docs || [];
                setDocs(docList);
                if (docList.length > 0) {
                    setSelectedUrl(docList[0].url);
                    onSelect(docList[0].url);
                }
            })
            .catch(() => setError(true))
            .finally(() => setLoading(false));
    }, [topic, onSelect]);

    const updateArrows = () => {
        const el = rowRef.current;
        if (!el) return;
        setCanScrollLeft(el.scrollLeft > 0);
        setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 1);
    };

    useEffect(() => {
        const el = rowRef.current;
        if (!el) return;
        updateArrows();
        el.addEventListener('scroll', updateArrows);
        const ro = new ResizeObserver(updateArrows);
        ro.observe(el);
        return () => {
            el.removeEventListener('scroll', updateArrows);
            ro.disconnect();
        };
    }, [docs]);

    if (loading) return <div className="panel-loading" />;
    if (error) return (
        <EmptyState
            icon={FiAlertCircle}
            title="Failed to load documents"
            message="Unable to fetch documents for this topic."
            variant="error"
        />
    );
    if (!docs.length) return (
        <EmptyState
            icon={FiFile}
            title="No documents"
            message="No documents are available for this topic yet."
            variant="empty"
        />
    );

    const scroll = (dir) => {
        rowRef.current?.scrollBy({ left: dir * SCROLL_AMOUNT, behavior: 'smooth' });
    };

    return (
        <div className="doc-chip-scroller">
            {canScrollLeft && (
                <button className="chip-arrow chip-arrow--left" onClick={() => scroll(-1)} aria-label="Scroll left">
                    <FiChevronLeft />
                </button>
            )}
            <div className="doc-chip-row" ref={rowRef}>
                {docs.map(doc => (
                    <button
                        key={doc.url}
                        className={`doc-chip ${selectedUrl === doc.url ? 'selected' : ''}`}
                        onClick={() => {
                            setSelectedUrl(doc.url);
                            onSelect(doc.url);
                        }}
                    >
                        {doc.title}
                    </button>
                ))}
            </div>
            {canScrollRight && (
                <button className="chip-arrow chip-arrow--right" onClick={() => scroll(1)} aria-label="Scroll right">
                    <FiChevronRight />
                </button>
            )}
        </div>
    );
};

export default DocumentList;
