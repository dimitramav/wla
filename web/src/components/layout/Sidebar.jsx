import { useTopic } from '../../hooks/useTopic';
import logo from "../../assets/full-logo.png";
import { useEffect, useState } from 'react';
import { getTopics } from '../../api/topics';

const Sidebar = () => {
    const { topic, setTopic } = useTopic();
    const [topics, setTopics] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getTopics()
            .then(data => {
                setTopics(data.topics || []);
            })
            .catch(err => {
                console.error("Failed to load topics:", err);
            })
            .finally(() => {
                setLoading(false);
            });
    }, []);

    return (
        <div className='sidebar'>
            <img
                src={logo}
                alt="Logo"
                onClick={() => window.location.reload()}
            />
            <ul className="sidebar-list">
                {loading && <li className="disabled">Loading topics...</li>}
                {!loading && topics.map((item) => (
                    <li
                        key={item.slug}
                        className={[
                            topic === item.slug ? "selected" : "",
                            !item.available ? "disabled" : "",
                        ].join(" ").trim()}
                        data-tooltip={!item.available ? "This topic is under development" : undefined}
                        onClick={() => item.available && setTopic(item.slug)}
                    >
                        <div className="tab-inner">
                            <h4>{item.title || item.label}</h4>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Sidebar;
