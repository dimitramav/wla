import { useTopic } from '../../hooks/useTopic';
import logo from "../../assets/full-logo.png";

const TOPIC_ITEMS = [
    { label: "School Anxiety", slug: "school_anxiety", available: true },
    { label: "Depression", slug: "depression", available: false },
];

const Sidebar = () => {
    const { topic, setTopic } = useTopic();

    return (
        <div className='sidebar'>
            <img
                src={logo}
                alt="Logo"
                onClick={() => window.location.reload()}
            />
            <ul className="sidebar-list">
                {TOPIC_ITEMS.map((item) => (
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
                            <h3>{item.label}</h3>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Sidebar;
