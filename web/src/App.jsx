import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Auth from './pages/Auth';
import { AuthProvider, useAuth } from './context/AuthContext';
import "./styles/main.scss";

// Minimal guard
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  console.log(user)
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<Auth />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
