import { useEffect, useRef } from 'react';
import { Worker, Viewer } from '@react-pdf-viewer/core';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';


const SingleDocument = ({ url, onSearchReady, highlightRequest }) => {
    const defaultLayoutPluginInstance = defaultLayoutPlugin({
        toolbarPlugin: {
            searchPlugin: {
                onHighlightKeyword: (props) => {
                    props.highlightEle.style.backgroundColor = 'rgba(245, 158, 11, 0.35)';
                },
            },
        },
    });
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
        if (!highlightRequest || !highlightRequest.text || !searchRef.current) return;
        const doHighlight = async () => {
            searchRef.current.clearHighlights();
            const matches = await searchRef.current.highlight({
                keyword: highlightRequest.text,
                matchCase: false,
                wholeWords: false,
            });
            if (matches.length > 0) {
                searchRef.current.jumpToMatch(0);
            }
        };
        const timer = setTimeout(doHighlight, 500);
        return () => clearTimeout(timer);
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
