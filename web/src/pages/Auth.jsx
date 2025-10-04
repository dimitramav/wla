import { useState, useContext } from "react";
import logo from "../assets/full-logo.png";
import { useNavigate } from "react-router-dom";
const Auth = (props) => {
    const [authMode, setAuthMode] = useState("signin");
    const [name, setName] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(false);
    const navigate = useNavigate();

    const changeAuthMode = () => {
        setAuthMode(authMode === "signin" ? "signup" : "signin");
    };
    const signIn = () => {
        // axios({
        //     // Endpoint to send files
        //     url: `${ip}/auth/generateToken`,
        //     method: "POST",
        //     headers: {
        //         "Content-Type": "application/json",
        //     },
        //     responseType: "text",
        //     // Attaching the form data
        //     data: {
        //         username: name,
        //         password: password,
        //     },
        // })
        //     // Handle the response from backend here
        //     .then((res) => {
        //         if (res.data) {
        //             sessionStorage.setItem("token", JSON.stringify(res.data));

        //             navigate("/");
        //         } else {
        //             setError(true);
        //         }
        //     })

        //     // Catch errors if any
        //     .catch((err) => {
        //         console.log(err);
        //         setError(true);
        //     });
    };

    if (authMode === "signin") {
        return (
            <div className="Auth-form-container">
                <form className="Auth-form">
                    <div className="Auth-form-content">
                        <div className="text-center">
                            <img src={logo}></img>
                        </div>{" "}
                        <div className="text-center">
                            Not registered yet?
                            <span className="link-primary" onClick={changeAuthMode}>
                                Sign Up
                            </span>
                        </div>
                        <div className="form-group mt-3">
                            <label>Username</label>
                            <input
                                className="form-control mt-1"
                                placeholder="Enter name"
                                onChange={(e) => {
                                    setError(false);
                                    setName(e.target.value);
                                }}
                            />
                        </div>
                        <div className="form-group mt-3">
                            <label>Password</label>
                            <input
                                type="password"
                                className="form-control mt-1"
                                placeholder="Enter password"
                                onChange={(e) => {
                                    setError(false);
                                    setPassword(e.target.value);
                                }}
                            />
                        </div>
                        {error && (
                            <div className="form-group mt-3">
                                <div className="alert alert-danger" role="alert">
                                    <label className="alert-label">
                                        Incorrect username or password
                                    </label>
                                </div>
                            </div>
                        )}
                        <div className="d-grid gap-2 mt-3">
                            <button
                                type="button"
                                className="btn btn-primary"
                                onClick={signIn}
                            >
                                Submit
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        );
    }

    return (
        <div className="Auth-form-container">
            <form className="Auth-form">
                <div className="Auth-form-content">
                    <div className="text-center">
                        <img src={logo} width={120} height={120}></img>
                    </div>
                    <div className="text-center">
                        Already registered?{" "}
                        <span className="link-primary" onClick={changeAuthMode}>
                            Sign In
                        </span>
                    </div>
                    <div className="form-group mt-3">
                        <label>Full Name</label>
                        <input
                            type="email"
                            className="form-control mt-1"
                            placeholder="e.g Jane Doe"
                        />
                    </div>
                    <div className="form-group mt-3">
                        <label>Email address</label>
                        <input
                            type="email"
                            className="form-control mt-1"
                            placeholder="Email Address"
                        />
                    </div>
                    <div className="form-group mt-3">
                        <label>Password</label>
                        <input
                            type="password"
                            className="form-control mt-1"
                            placeholder="Password"
                        />
                    </div>
                    <div className="d-grid gap-2 mt-3">
                        <button type="button" className="btn btn-primary" onClick={signIn}>
                            Submit
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
};

export default Auth;
