import Sidebar from '../components/layout/Sidebar';
import TheoryPanel from '../components/viewers/Theory';
import DocumentList from '../components/viewers/DocumentList';
import PdfViewer from '../components/viewers/SingleDocument';
import { useState } from 'react';

export default function Dashboard() {
    const [selectedUrl, setSelectedUrl] = useState(undefined);

    return (
        <div className="grid" style={{ gridTemplateColumns: '15% 35% 50%', height: 'calc(100vh - 48px)' }}>
            <div className="border-r overflow-auto"><Sidebar /></div>
            <div className="border-r overflow-auto"><TheoryPanel /></div>
            <div className="overflow-auto">
                <div className="grid grid-cols-2 h-full">
                    <div className="border-r overflow-auto">
                        <DocumentList onSelect={setSelectedUrl} />
                    </div>
                    <div className="overflow-auto">
                        <PdfViewer url={selectedUrl} />
                    </div>
                </div>
            </div>
        </div>
    );
}
