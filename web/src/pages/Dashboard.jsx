import Sidebar from '../components/layout/Sidebar';
import TheoryPanel from '../components/viewers/Theory';
import DocumentList from '../components/viewers/DocumentList';
import PdfViewer from '../components/viewers/SingleDocument';
import Navbar from '../components/layout/Navbar';
import Footer from "../components/layout/Footer";
import Progress from '../components/viewers/Progress';
import Quiz from '../components/viewers/Quiz';
import { useState } from 'react';

const Dashboard = () => {
    const [selectedUrl, setSelectedUrl] = useState(undefined);
    const [activeDrawer, setActiveDrawer] = useState(null); // 'progress' | 'quiz' | null

    const handleShow = (selectedDrawer) => setActiveDrawer(selectedDrawer);

    return (
        <div className="dashboard-grid">
            <Sidebar />
            <div className="main-area">
                <Navbar />
                <div className="content-grid">
                    <div className='tutors-panel'>
                        <TheoryPanel onShow={handleShow}
                        />
                        {activeDrawer === 'progress' && <div className='drawer-panel'><Progress /></div>}
                        {activeDrawer === 'quiz' && <div className='drawer-panel'><Quiz /></div>}
                    </div>
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
