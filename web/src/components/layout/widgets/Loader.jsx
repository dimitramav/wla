const Loader = ({ message }) => {
    return (
        <div className="loader-wrapper">
            <div className="loader-con">
                <div style={{ "--i": 0 }} className="pfile"></div>
                <div style={{ "--i": 1 }} className="pfile"></div>
                <div style={{ "--i": 2 }} className="pfile"></div>
                <div style={{ "--i": 3 }} className="pfile"></div>
                <div style={{ "--i": 4 }} className="pfile"></div>
                <div style={{ "--i": 5 }} className="pfile"></div>
            </div>
            <div className="loader-text">{message}</div>
        </div>
    );
};

export default Loader;
