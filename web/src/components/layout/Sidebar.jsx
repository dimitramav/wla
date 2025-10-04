import { useState } from 'react';
import { useLesson } from '../../hooks/useLesson';
import logo from "../../assets/full-logo.png";

const Sidebar = () => {
    const { lesson } = useLesson();
    const items = ["School Anxiety", "Depression"];

    const [selectedLesson, setSelectedLesson] = useState(0);

    return (
        <div className='sidebar'>
            <img src={logo} alt="Logo" />
            <ul className="sidebar-list">
                {items.map((item, index) => (
                    <li
                        key={index}
                        className={selectedLesson === index ? "selected" : ""}
                        onClick={() => setSelectedLesson(index)}
                    >
                        <h3>{item}</h3>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Sidebar;
