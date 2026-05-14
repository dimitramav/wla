import { useState } from "react";
import logo from "../assets/wla-logo.png";
import fullLogo from "../assets/full-logo.png"
import { useNavigate } from "react-router-dom";
import { useAuth } from '../context/AuthContext';

const Auth = () => {
    const [authMode, setAuthMode] = useState("signin");
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [email, setEmail] = useState("");
    const [error, setError] = useState(null);
    const navigate = useNavigate();
    const { signup, login } = useAuth();


    const isSignIn = authMode === "signin";
    const isValid = isSignIn
        ? email.trim().length > 0 && password.trim().length > 0
        : email.trim().length > 0 && password.trim().length > 0 && username.trim().length > 0;

    const toggleAuthMode = () => {
        setAuthMode(isSignIn ? "signup" : "signin");
        setError(false);
        setUsername("");
        setPassword("");
        setEmail("");
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        if (!email || !password || (!isSignIn && !username)) {
            setError(isSignIn ? 'Invalid email or password.' : 'Please fill out all fields to sign up.');
            return;
        }

        try {
            if (isSignIn) {
                await login({ email, password });
            } else {
                await signup({ email, password, username: username });
            }
            navigate('/');
        } catch {
            setError('Authentication failed.');
        }
    };


    return (
        <div className="auth-container">
            <div className="auth-split">
                <div className="auth-hero">
                    <div className="auth-hero__illustration" aria-hidden="true">
                        <img src={logo} alt="Watch Listen Act" />
                    </div>
                    <h1 className="auth-hero__tagline">Watch · Listen · Act</h1>
                    <p className="auth-hero__subtitle">Empowering educators to recognize and support student mental health</p>
                </div>
                <div className="auth-form-wrapper">
                    <form className="auth-form" onSubmit={handleSubmit}>
                        <img src={fullLogo} alt="Watch Listen Act" className="auth-mobile-logo" />
                        <div>
                            <label className="label" htmlFor="auth-email">Email</label>
                            <input
                                id="auth-email"
                                type="email"
                                className="input"
                                placeholder="e.g. user@email.com"
                                value={email}
                                onChange={(e) => {
                                    setError(null);
                                    setEmail(e.target.value);
                                }}
                            />
                        </div>
                        {!isSignIn && (
                            <div>
                                <label className="label" htmlFor="auth-name">Username</label>
                                <input
                                    id="auth-name"
                                    className="input"
                                    placeholder="e.g. jane"
                                    value={username}
                                    onChange={(e) => {
                                        setError(null);
                                        setUsername(e.target.value);
                                    }}
                                /></div>
                        )}
                        <div>
                            <label className="label" htmlFor="auth-password">Password</label>
                            <input
                                id="auth-password"
                                type="password"
                                className="input"
                                placeholder="******"
                                value={password}
                                onChange={(e) => {
                                    setError(false);
                                    setPassword(e.target.value);
                                }}
                            />
                        </div>
                        {error && (
                            <div className="field-error" style={{ marginTop: "0.75rem" }}>
                                {error}
                            </div>
                        )}
                        <div className="label sub-label">
                            <span>
                                {isSignIn ? "Not registered yet?" : "Already registered?"}
                            </span>
                            <span
                                className="link"
                                onClick={toggleAuthMode}
                                aria-label={`Switch to ${isSignIn ? "Sign Up" : "Sign In"}`}
                            >
                                {isSignIn ? "Sign Up" : "Sign In"}
                            </span>
                        </div>
                        <div className="text-center">
                            <button type="submit" className="btn btn-primary" disabled={!isValid}>
                                Submit
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Auth;
