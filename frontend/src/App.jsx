/**
 * App shell with auth protection, progress bar, and route definitions.
 */
import { BrowserRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AssessmentProvider } from './context/AssessmentContext';
import Layout from './components/Layout';
import Landing from './pages/Landing';
import ContextIntake from './pages/ContextIntake';
import ActivityRouter from './pages/activities/ActivityRouter';
import ThinkingStyles from './pages/ThinkingStyles';
import Results from './pages/Results';
import DeepDive from './pages/DeepDive';
import Roadmap from './pages/Roadmap';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Analytics from './pages/Analytics';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

/**
 * Redirect to /login if not authenticated.
 */
function ProtectedRoute({ children }) {
  const { isAuthenticated, authLoading } = useAuth();

  if (authLoading) {
    return (
      <div className="container flex justify-center items-center" style={{ minHeight: '60vh' }}>
        <div className="glass-card text-center">
          <p style={{ fontSize: 'var(--font-size-lg)' }}>Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

/**
 * Redirect to /login if not admin.
 */
function AdminRoute({ children }) {
  const { isAuthenticated, isAdmin, authLoading } = useAuth();

  if (authLoading) {
    return (
      <div className="container flex justify-center items-center" style={{ minHeight: '60vh' }}>
        <div className="glass-card text-center">
          <p style={{ fontSize: 'var(--font-size-lg)' }}>Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }

  return children;
}

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        {/* Public routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Layout><Login /></Layout>} />
        <Route path="/signup" element={<Layout><Signup /></Layout>} />

        {/* Protected routes — require login */}
        <Route path="/context" element={<ProtectedRoute><Layout><ContextIntake /></Layout></ProtectedRoute>} />
        <Route path="/activity/:activityNumber" element={<ProtectedRoute><Layout><ActivityRouter /></Layout></ProtectedRoute>} />
        <Route path="/thinking-styles" element={<ProtectedRoute><Layout><ThinkingStyles /></Layout></ProtectedRoute>} />
        <Route path="/results" element={<ProtectedRoute><Layout><Results /></Layout></ProtectedRoute>} />
        <Route path="/deep-dive" element={<ProtectedRoute><Layout><DeepDive /></Layout></ProtectedRoute>} />
        <Route path="/deep-dive/:domain" element={<ProtectedRoute><Layout><DeepDive /></Layout></ProtectedRoute>} />
        <Route path="/roadmap/:domain" element={<ProtectedRoute><Layout><Roadmap /></Layout></ProtectedRoute>} />

        {/* Admin-only route */}
        <Route path="/analytics" element={<AdminRoute><Layout><Analytics /></Layout></AdminRoute>} />
      </Routes>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <BrowserRouter>
        <AuthProvider>
          <AssessmentProvider>
            <div className="bg-mesh" />
            <AnimatedRoutes />
          </AssessmentProvider>
        </AuthProvider>
      </BrowserRouter>
    </GoogleOAuthProvider>
  );
}
