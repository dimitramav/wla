import { useEffect, useState } from 'react';
import { getDocs } from '../../api/docs';
import { useTopic } from '../../hooks/useTopic';
import TreeView from 'react-treeview';

const DocumentList = ({ onSelect }) => {
    const { topic } = useTopic();
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedUrl, setSelectedUrl] = useState(null);

    useEffect(() => {
        setLoading(true);
        getDocs(topic)
            .then(d => {
                const docList = d.docs || [];
                setDocs(docList);
                if (docList.length > 0) {
                    setSelectedUrl(docList[0].url);
                    onSelect(docList[0].url); // Automatically select first doc
                }
            })
            .finally(() => setLoading(false));
    }, [topic, onSelect]);

    if (loading) return <div>Loading...</div>;
    if (!docs.length) return <div>No documents found</div>;

    // TreeView Structure with topic as root
    const renderTree = (docs) => {
        return (
            <TreeView nodeLabel={<span className="node-label">{topic}</span>} defaultCollapsed={false}>
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
                                {doc.title}
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
