import { useEffect, useState } from 'react';
import { getDocs } from '../../api/docs';
import { useLesson } from '../../hooks/useLesson';
import TreeView from 'react-treeview';

const DocumentTree = ({ lesson, docs, onSelect }) => {
    const label = <span className="node-label">{lesson}</span>;

    return (
        <div className="document-tree">
            <TreeView nodeLabel={label} defaultCollapsed={false}>
                {docs.map(doc => (
                    <TreeView
                        key={doc.url}
                        nodeLabel={
                            <button
                                className="doc-node-button"
                                onClick={() => onSelect(doc.url)}
                            >
                                {doc.title}
                            </button>
                        }
                        defaultCollapsed={true}
                    />
                ))}
            </TreeView>
        </div>
    );
};
const DocumentList = ({ onSelect }) => {
    const { lesson } = useLesson();
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        getDocs(lesson)
            .then(d => {
                setDocs(d.docs || []);
            })
            .finally(() => {
                setLoading(false);
            });
    }, [lesson]);

    if (loading) {
        return <div className="text-muted">Loading docs…</div>;
    }
    if (!docs.length) {
        return <div className="text-muted">No PDFs found.</div>;
    }

    return (
        <DocumentTree lesson={lesson} docs={docs} onSelect={onSelect} />
    );
}
export default DocumentList;
