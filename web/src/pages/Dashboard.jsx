import Sidebar from '../components/layout/Sidebar';
import TheoryPanel from '../components/viewers/Theory';
import DocumentList from '../components/viewers/DocumentList';
import PdfViewer from '../components/viewers/SingleDocument';
import Navbar from '../components/layout/Navbar';
import Footer from "../components/layout/Footer";
import Progress from '../components/viewers/Progress';
import Quiz from '../components/quiz/Quiz';
import { useTopic } from '../hooks/useTopic';
import { useAuth } from "../context/AuthContext";
import { useState } from 'react';

const Dashboard = () => {
    const PASS_THRESHOLD = import.meta.env.PASS_THRESHOLD;
    const { topic, docsetHash } = useTopic();
    const { user } = useAuth();
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
                        <TheoryPanel onShow={handleShow} activeDrawer={activeDrawer}
                        />
                        {activeDrawer === 'progress' && <div className='drawer-panel'><Progress topic={topic} userId={user?.id} PASS_THRESHOLD={PASS_THRESHOLD} /></div>}
                        {activeDrawer === 'quiz' && <div className='drawer-panel'><Quiz topic={topic} docsetHash={docsetHash} userId={user?.id} PASS_THRESHOLD={PASS_THRESHOLD} onShowProgress={() => setActiveDrawer("progress")} /></div>}
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
