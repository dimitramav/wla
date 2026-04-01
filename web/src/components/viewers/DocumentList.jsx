import { useEffect, useState } from 'react';
import { getDocs } from '../../api/docs';
import { useTopic } from '../../hooks/useTopic';
import TreeView from 'react-treeview';

const DocumentList = ({ onSelect }) => {
    const { topic } = useTopic();
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedUrl, setSelectedUrl] = useState(null);

    useEffect(() => {
        setLoading(true);
        setError(null);
        getDocs(topic)
            .then(d => {
                const docList = d.docs || [];
                setDocs(docList);
                if (docList.length > 0) {
                    setSelectedUrl(docList[0].url);
                    onSelect(docList[0].url); // Automatically select first doc
                }
            })
            .catch(() => setError(true))
            .finally(() => setLoading(false));
    }, [topic, onSelect]);

    if (loading) return <div className="panel-loading" />;
    if (error || !docs.length) return null;

    // TreeView Structure with topic as root
    const renderTree = (docs) => {
        return (
            <TreeView nodeLabel={<div className="node-label"><h4>{topic}</h4></div>} defaultCollapsed={false}>
                {docs.map(doc => (
                    <TreeView
                        key={doc.url}
                        nodeLabel={
                            <button
                                className={`doc-node-button ${selectedUrl === doc.url ? 'selected' : ''}`}
                                onClick={() => {
                                    setSelectedUrl(doc.url);
                                    onSelect(doc.url);
                                }}
                            >
                                <p>
                                    {doc.title}</p>
                            </button>
                        }
                        defaultCollapsed={true}
                    />
                ))}
            </TreeView>
        );
    };

    return (
        <div className="document-tree">
            {renderTree(docs)}
        </div>
    );
};

export default DocumentList;
