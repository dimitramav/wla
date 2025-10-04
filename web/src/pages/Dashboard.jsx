import Sidebar from '../components/layout/Sidebar';
import TheoryPanel from '../components/viewers/Theory';
import DocumentList from '../components/viewers/DocumentList';
import PdfViewer from '../components/viewers/SingleDocument';
import Navbar from '../components/layout/Navbar';
import Footer from "../components/layout/Footer";
import { useState } from 'react';

const Dashboard = () => {
    const [selectedUrl, setSelectedUrl] = useState(undefined);

    return (
        <div className="dashboard-grid">
            <Sidebar />
            <div className="main-area">
                <Navbar />
                <div className="content-grid">
                    <TheoryPanel />
                    <div className="documents-panel">
                        <div className="documents-grid">
                            <DocumentList onSelect={setSelectedUrl} />
                            <PdfViewer url={selectedUrl} />
                        </div>
                    </div>
                </div>
                {/* <Footer /> */}
            </div>
        </div>
    );
};

export default Dashboard;
