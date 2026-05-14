import { useEffect, useState } from 'react';
import { Worker, Viewer } from '@react-pdf-viewer/core';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import { API_BASE } from '../../api/client';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';

const workerUrl = "https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js";

const SingleDocument = ({ url, highlightRequest }) => {
    const defaultLayoutPluginInstance = defaultLayoutPlugin();
    const [matches, setMatches] = useState([]);

    useEffect(() => {
        setMatches([]);
        if (!highlightRequest?.topic || !highlightRequest?.doc || !highlightRequest?.text) return;

        let cancelled = false;
        (async () => {
            try {
                const res = await fetch(`${API_BASE}/api/${encodeURIComponent(highlightRequest.topic)}/highlight`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ doc: highlightRequest.doc, text: highlightRequest.text }),
                });
                if (!res.ok) throw new Error(`highlight ${res.status}`);
                const data = await res.json();
                if (cancelled) return;
                const list = Array.isArray(data?.matches) ? data.matches : [];
                setMatches(list);
                if (list.length > 0) {
                    const firstPage = list[0].page - 1;
                    const nav = defaultLayoutPluginInstance.toolbarPluginInstance?.pageNavigationPluginInstance;
                    if (nav?.jumpToPage) {
                        setTimeout(() => nav.jumpToPage(firstPage), 200);
                    }
                }
            } catch (err) {
                console.error('[PDF-HL] highlight fetch failed:', err);
            }
        })();

        return () => { cancelled = true; };
    }, [highlightRequest]);

    const renderPage = (props) => {
        const pageNumber = props.pageIndex + 1;
        const pageMatches = matches.filter(m => m.page === pageNumber);
        return (
            <>
                {props.canvasLayer.children}
                {props.textLayer.children}
                {props.annotationLayer.children}
                {pageMatches.map((m, i) => {
                    const [l, t, r, b] = m.bbox;
                    return (
                        <div
                            key={i}
                            className="pdf-doc-highlight"
                            style={{
                                position: 'absolute',
                                left: `${l * 100}%`,
                                top: `${t * 100}%`,
                                width: `${(r - l) * 100}%`,
                                height: `${(b - t) * 100}%`,
                            }}
                        />
                    );
                })}
            </>
        );
    };

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
                            renderPage={renderPage}
                        />
                    </div>
                </Worker>
            </div>
        </div>
    );
};

export default SingleDocument;
