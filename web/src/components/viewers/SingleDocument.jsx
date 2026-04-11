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

        // Build a prioritized list of candidate keywords. PDF text-layer
        // extraction (pdf.js) often differs from Docling's markdown export —
        // ligatures, smart quotes, hyphenation, and whitespace can break exact
        // matches. Try short distinctive phrases first, then fall back to
        // individual rare words.
        const normalized = highlightRequest.text.replace(/\s+/g, ' ').trim();
        const words = normalized.split(' ').filter(w => w.length > 0);
        const candidates = [];

        // 1. Sliding 5-word windows
        for (let i = 0; i <= words.length - 5 && candidates.length < 6; i++) {
            candidates.push(words.slice(i, i + 5).join(' '));
        }
        // 2. Sliding 3-word windows
        for (let i = 0; i <= words.length - 3 && candidates.length < 12; i++) {
            candidates.push(words.slice(i, i + 3).join(' '));
        }
        // 3. Individual "rare" words (>6 chars, alphabetic)
        for (const w of words) {
            if (candidates.length >= 20) break;
            const clean = w.replace(/[^\w]/g, '');
            if (clean.length > 6 && /^[A-Za-z]+$/.test(clean)) {
                candidates.push(clean);
            }
        }

        console.log('[PDF-HL] candidates:', candidates);
        if (candidates.length === 0) return;

        let cancelled = false;
        const tryHighlight = async (attempt = 0) => {
            if (cancelled || !searchRef.current) {
                if (!searchRef.current && attempt < 10) {
                    setTimeout(() => tryHighlight(attempt + 1), 400);
                }
                return;
            }
            try {
                searchRef.current.clearHighlights();
                for (const keyword of candidates) {
                    const matches = await searchRef.current.highlight({
                        keyword,
                        matchCase: false,
                        wholeWords: false,
                    });
                    if (cancelled) return;
                    if (matches && matches.length > 0) {
                        console.log('[PDF-HL] matched with:', keyword, 'count:', matches.length);
                        searchRef.current.jumpToMatch(0);
                        return;
                    }
                    searchRef.current.clearHighlights();
                }
                console.warn('[PDF-HL] no candidates matched, attempt:', attempt);
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
