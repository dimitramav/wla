import { useState } from "react";
import logo from "../assets/full-logo.png";
import { useNavigate } from "react-router-dom";

const Auth = () => {
    const [authMode, setAuthMode] = useState("signin");
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [email, setEmail] = useState("");
    const [error, setError] = useState(false);
    const navigate = useNavigate();

    const isSignIn = authMode === "signin";

    const toggleAuthMode = () => {
        setAuthMode(isSignIn ? "signup" : "signin");
        setError(false);
        setName("");
        setPassword("");
        setEmail("");
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        // Basic validation
        const valid =
            password &&
            email &&
            (isSignIn || username); // name required only for signup

        if (!valid) {
            setError(true);
            return;
        }

        // TODO: Replace with real backend call
        console.log("Submitting:", { email, username, password });
        navigate("/");
    };

    return (
        <div className="auth-container">
            <form className="auth-form" onSubmit={handleSubmit}>
                <img src={logo} />
                <div>
                    <label className="label" htmlFor="auth-email">Email</label>
                    <input
                        id="auth-email"
                        type="email"
                        className="input"
                        placeholder="e.g. user@email.com"
                        value={email}
                        onChange={(e) => {
                            setError(false);
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
                                setError(false);
                                setName(e.target.value);
                            }}
                        /></div>
                )}

                {/* Password */}
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
                        autoComplete={isSignIn ? "current-password" : "new-password"}
                    />
                </div>
                {/* Error Message */}
                {error && (
                    <div className="field-error" style={{ marginTop: "0.75rem" }}>
                        {isSignIn
                            ? "Invalid email or password."
                            : "Please fill out all fields to sign up."}
                    </div>
                )}
                <div className="label sub-label">
                    <span>
                        {isSignIn ? "Not registered yet?" : "Already registered?"}{" "}
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
                    <button type="submit" className="btn btn-primary">
                        Submit
                    </button>
                </div>
            </form >
        </div >
    );
};

export default Auth;
