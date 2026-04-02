import { useEffect, useRef, useState } from 'react';
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi';

const SCROLL_AMOUNT = 240;

const DocumentList = ({ docs, onSelect }) => {
    const [selectedUrl, setSelectedUrl] = useState(null);
    const [canScrollLeft, setCanScrollLeft] = useState(false);
    const [canScrollRight, setCanScrollRight] = useState(false);
    const rowRef = useRef(null);

    useEffect(() => {
        if (docs.length > 0) {
            setSelectedUrl(docs[0].url);
            onSelect(docs[0].url);
        }
    }, [docs, onSelect]);

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
