/**
 * App.jsx
 *
 * This file defines the main application component for the web app.
 *
 * Key Features:
 * - Provides routing for the application using `react-router-dom`.
 * - Implements authentication context with `AuthProvider`.
 * - Protects routes with a minimal guard (`ProtectedRoute`).
 *
 * Routes:
 * - `/`: Protected route that renders the `Dashboard` component.
 * - `/login`: Public route that renders the `Auth` component.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Auth from './pages/Auth';
import { AuthProvider, useAuth } from './context/AuthContext';
import "./styles/main.scss";

// if loading, show nothing
// if no user, redirect to /login
// else show children

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
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
