import { Worker, Viewer } from '@react-pdf-viewer/core';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';
// pdfjs.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`


const SingleDocument = ({ url }) => {
    const defaultLayoutPluginInstance = defaultLayoutPlugin();
    const workerUrl = "https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js"

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

