import Sidebar from '../components/layout/Sidebar';
import TheoryPanel from '../components/viewers/Theory';
import DocumentList from '../components/viewers/DocumentList';
import PdfViewer from '../components/viewers/SingleDocument';
import { useState } from 'react';

const Dashboard = () => {
    const [selectedUrl, setSelectedUrl] = useState(undefined);

    return (
        <div className="dashboard-grid">
            <div className="sidebar"><Sidebar /></div>
            <div className="theory-panel"><TheoryPanel /></div>
            <div className="documents-panel">
                <div className="documents-grid">
                    <div className="document-list">
                        <DocumentList onSelect={setSelectedUrl} />
                    </div>
                    <div className="pdf-viewer">
                        <PdfViewer url={selectedUrl} />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;