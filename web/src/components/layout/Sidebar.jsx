import { useTopic } from '../../hooks/useTopic';
import logo from "../../assets/full-logo.png";

const TOPIC_ITEMS = [
    { label: "School Anxiety", slug: "school_anxiety" },
    { label: "Depression", slug: "depression" },
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
                        className={topic === item.slug ? "selected" : ""}
                        onClick={() => setTopic(item.slug)}
                    >
                        <h3>{item.label}</h3>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Sidebar;
