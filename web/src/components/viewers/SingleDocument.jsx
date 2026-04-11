import { useEffect, useRef } from 'react';
import { Worker, Viewer } from '@react-pdf-viewer/core';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';


const SingleDocument = ({ url, onSearchReady, highlightRequest }) => {
    const defaultLayoutPluginInstance = defaultLayoutPlugin();
    const workerUrl = "https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js";

    const searchPluginInstance = defaultLayoutPluginInstance.toolbarPluginInstance.searchPluginInstance;
    const searchRef = useRef(null);

    useEffect(() => {
        searchRef.current = searchPluginInstance;
        if (onSearchReady) {
            onSearchReady(searchPluginInstance);
        }
    }, []);

    useEffect(() => {
        if (!highlightRequest || !highlightRequest.text) return;

        // PDF text-layer extraction (pdf.js) often differs from Docling's
        // markdown export — ligatures, smart quotes, hyphenation, and
        // whitespace can break exact matches on long strings. So we slice
        // the chunk into many short overlapping phrases and highlight all of
        // them at once; each phrase that survives extraction contributes to
        // a contiguous highlight covering the full chunk.
        const normalized = highlightRequest.text.replace(/\s+/g, ' ').trim();
        const words = normalized.split(' ').filter(w => w.length > 0);

        const windows = (size) => {
            const out = [];
            for (let i = 0; i <= words.length - size; i++) {
                out.push(words.slice(i, i + size).join(' '));
            }
            return out;
        };

        const fiveWord = windows(5);
        const threeWord = windows(3);
        const rareWords = words
            .map(w => w.replace(/[^\w]/g, ''))
            .filter(w => w.length > 6 && /^[A-Za-z]+$/.test(w));

        let cancelled = false;
        const runHighlight = async (keywords) => {
            if (!keywords.length) return 0;
            searchRef.current.clearHighlights();
            const matches = await searchRef.current.highlight(
                keywords.map(keyword => ({ keyword, matchCase: false, wholeWords: false }))
            );
            return Array.isArray(matches) ? matches.length : (matches ? 1 : 0);
        };

        const tryHighlight = async (attempt = 0) => {
            if (cancelled || !searchRef.current) {
                if (!searchRef.current && attempt < 10) {
                    setTimeout(() => tryHighlight(attempt + 1), 400);
                }
                return;
            }
            try {
                for (const tier of [fiveWord, threeWord, rareWords]) {
                    const count = await runHighlight(tier);
                    if (cancelled) return;
                    if (count > 0) {
                        console.log('[PDF-HL] tier matched, highlights:', count);
                        searchRef.current.jumpToMatch(0);
                        return;
                    }
                }
                console.warn('[PDF-HL] no tier matched, attempt:', attempt);
                if (attempt < 5) setTimeout(() => tryHighlight(attempt + 1), 700);
            } catch (err) {
                console.error('[PDF-HL] highlight error:', err);
            }
        };
        const timer = setTimeout(() => tryHighlight(0), 500);
        return () => { cancelled = true; clearTimeout(timer); };
    }, [highlightRequest]);

    if (!url) {
        return <div className="pdf-placeholder">Select a document to preview.</div>;
    }

    return (
        <div className="pdf-viewer-container">
            <div className="pdf-scroll">
                <Worker workerUrl={workerUrl}>
                    <div style={{ height: '100%' }}>
                        <Viewer
                            fileUrl={url}
                            plugins={[defaultLayoutPluginInstance]}
                        />
                    </div>
                </Worker>
            </div>
        </div>
    );
};

export default SingleDocument;
