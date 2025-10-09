import { useState } from 'react';
import { useTopic } from '../../hooks/useTopic';
import logo from "../../assets/full-logo.png";

const Sidebar = () => {
    const { topic } = useTopic();
    const items = ["School Anxiety", "Depression"];

    const [selectedTopic, setSelectedTopic] = useState(0);

    return (
        <div className='sidebar'>
            <img src={logo} alt="Logo" />
            <ul className="sidebar-list">
                {items.map((item, index) => (
                    <li
                        key={index}
                        className={selectedTopic === index ? "selected" : ""}
                        onClick={() => setSelectedTopic(index)}
                    >
                        <h3>{item}</h3>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Sidebar;
