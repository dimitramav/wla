import Sidebar from '../components/layout/Sidebar';
import TheoryPanel from '../components/viewers/Theory';
import DocumentList from '../components/viewers/DocumentList';
import PdfViewer from '../components/viewers/SingleDocument';
import Navbar from '../components/layout/Navbar';
import Footer from "../components/layout/Footer";
import Progress from '../components/viewers/Progress';
import Quiz from '../components/quiz/Quiz';
import EmptyState from '../components/layout/widgets/EmptyState';
import { FiFile, FiAlertCircle } from 'react-icons/fi';
import { useTopic } from '../hooks/useTopic';
import { useDocs } from '../hooks/useDocs';
import { useAuth } from "../context/AuthContext";
import { TopicProvider } from '../context/TopicContext';
import { useState, useCallback } from 'react';

const DashboardContent = () => {
    const PASS_THRESHOLD = Number(import.meta.env.VITE_PASS_THRESHOLD);
    const { topic, docsetHash, loading } = useTopic();
    const { docs, loading: docsLoading, error: docsError } = useDocs();
    const { user } = useAuth();
    const [selectedUrl, setSelectedUrl] = useState(null);
    const [activeDrawer, setActiveDrawer] = useState(null); // 'progress' | 'quiz' | null
    const [activeTab, setActiveTab] = useState('practice'); // 'learn' | 'practice'
    const [quizError, setQuizError] = useState(false);
    const [quizKey, setQuizKey] = useState(0);
    const [docListKey, setDocListKey] = useState(0);
    const [highlightRequest, setHighlightRequest] = useState(null);

    const handleShow = (selectedDrawer) => {
        if (selectedDrawer === 'quiz') setQuizKey(k => k + 1);
        setActiveDrawer(selectedDrawer);
        setQuizError(false);
        setHighlightRequest(null);
    };

    const handleViewSource = useCallback((docFilename, searchText) => {
        if (!docFilename || !searchText || !topic) return;
        const fullUrl = `/pdfs/${topic}/${docFilename}`;
        setSelectedUrl(fullUrl);
        setHighlightRequest({ text: searchText, key: Date.now() });
    }, [topic]);

    const handleQuizReset = useCallback(() => {
        setHighlightRequest(null);
        setDocListKey(k => k + 1);
    }, []);

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
                <div className={`tutors-panel${activeDrawer ? ' tutors-panel--drawer' : ''}`}>
                    {loading && <div className="panel-loading" />}
                    {!loading && <TheoryPanel onShow={handleShow} activeDrawer={activeDrawer} quizError={quizError} />}
                    {activeDrawer && (
                        <button className="back-to-theory btn btn-outline-accent" onClick={() => { setActiveDrawer(null); setHighlightRequest(null); }}>
                            ← Theory
                        </button>
                    )}
                    {activeDrawer === 'progress' && <div className='drawer-panel'><Progress topic={topic} userId={user?.id} PASS_THRESHOLD={PASS_THRESHOLD} /></div>}
                    {activeDrawer === 'quiz' && <div className='drawer-panel'><Quiz key={quizKey} topic={topic} docsetHash={docsetHash} userId={user?.id} PASS_THRESHOLD={PASS_THRESHOLD} onShowProgress={() => setActiveDrawer("progress")} onError={() => setQuizError(true)} onViewSource={handleViewSource} onQuizReset={handleQuizReset} /></div>}
                </div>
                <div className="documents-panel">
                    <div className="documents-grid">
                        {docsLoading && <div className="panel-loading" />}
                        {!docsLoading && docsError && (
                            <EmptyState
                                icon={FiAlertCircle}
                                title="Failed to load documents"
                                message="Unable to fetch documents for this topic."
                                variant="error"
                            />
                        )}
                        {!docsLoading && !docsError && docs.length === 0 && (
                            <EmptyState
                                icon={FiFile}
                                title="No documents"
                                message="No documents are available for this topic yet."
                                variant="empty"
                            />
                        )}
                        {!docsLoading && !docsError && docs.length > 0 && (
                            <>
                                <DocumentList key={docListKey} docs={docs} onSelect={setSelectedUrl} />
                                {selectedUrl && <PdfViewer url={selectedUrl} highlightRequest={highlightRequest} />}
                            </>
                        )}
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
