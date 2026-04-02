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
import { TopicProvider } from '../context/TopicContext';
import { useState } from 'react';

const DashboardContent = () => {
    const PASS_THRESHOLD = import.meta.env.PASS_THRESHOLD;
    const { topic, docsetHash, loading } = useTopic();
    const { user } = useAuth();
    const [selectedUrl, setSelectedUrl] = useState(undefined);
    const [activeDrawer, setActiveDrawer] = useState(null); // 'progress' | 'quiz' | null
    const [activeTab, setActiveTab] = useState('practice'); // 'learn' | 'practice'

    const handleShow = (selectedDrawer) => setActiveDrawer(selectedDrawer);

    return (
        <div className="dashboard-grid">
            <Sidebar />
            <Navbar />
            <div className="responsive-toggle">
                <div className="toggle-inner">
                    <div className={`slider-highlight ${activeTab}`} />
                    <button 
                        type="button"
                        className={activeTab === 'learn' ? 'active' : ''} 
                        onClick={() => setActiveTab('learn')}
                    >
                        Learn
                    </button>
                    <button 
                        type="button"
                        className={activeTab === 'practice' ? 'active' : ''} 
                        onClick={() => setActiveTab('practice')}
                    >
                        Practice
                    </button>
                </div>
            </div>
            <div className={`content-grid content-grid--${activeTab}`}>
                <div className='tutors-panel'>
                    {loading && <div className="panel-loading" />}
                    {!loading && <TheoryPanel onShow={handleShow} activeDrawer={activeDrawer} />}
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
            <Footer />
        </div>
    );
};

const Dashboard = () => {
    return (
        <TopicProvider>
            <DashboardContent />
        </TopicProvider>
    );
};

export default Dashboard;
