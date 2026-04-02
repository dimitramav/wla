import { FiAlertCircle } from 'react-icons/fi';

const EmptyState = ({ icon: Icon, title, message, variant = 'empty' }) => (
    <div className={`empty-state empty-state--${variant}`}>
        <div className="empty-state__icon">
            {Icon ? <Icon size={40} /> : <FiAlertCircle size={40} />}
        </div>
        {title && <p className="empty-state__title">{title}</p>}
        {message && <p className="empty-state__message">{message}</p>}
    </div>
);

export default EmptyState;
