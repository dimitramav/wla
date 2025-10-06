import { useAuth } from "../../context/AuthContext";

export default function Navbar() {
    const { logout } = useAuth();

    const handleSignOut = async () => {
        try {
            await logout();
        } catch (err) {
            console.error("Logout failed:", err);
        }
    };

    return (
        <div className="navbar">
            <p className="link link-danger" onClick={handleSignOut}>
                Sign out
            </p>
        </div>
    );
}
