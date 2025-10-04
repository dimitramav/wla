export default function SingleDocument({ url }) {
    if (!url) {
        return <div className=" text-sm text-gray-500">Select a document to preview.</div>;
    }
    return (
        <div className="w-full h-full">
            <iframe title="pdf" src={url} className="w-full h-full border-0" />
        </div>
    );
}
