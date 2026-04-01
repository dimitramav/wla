import { useAuth } from "../../context/AuthContext";

export default function Navbar() {
    const { user, logout } = useAuth();

    const handleSignOut = async () => {
        try {
            await logout();
        } catch (err) {
            console.error("Logout failed:", err);
        }
    };

    return (
        <div className="navbar">
            <span className="navbar-greeting">Welcome, {user?.email}</span>
            <p className="link link-danger" onClick={handleSignOut}>
                Sign out
            </p>
        </div>
    );
}
