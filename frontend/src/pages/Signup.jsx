/**
 * Signup Page — Google OAuth only (auto-creates account).
 */
import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../context/AuthContext';

export default function Signup() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { googleLogin } = useAuth();

  const handleGoogleSuccess = async (credentialResponse) => {
    setLoading(true);
    setError('');
    try {
      await googleLogin(credentialResponse.credential);
      navigate('/context');
    } catch (err) {
      setError(err.message || 'Google sign-up failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    setError('Google sign-in was cancelled or failed. Please try again.');
  };

  return (
    <motion.div
      className="container flex justify-center items-center"
      style={{ minHeight: '80vh' }}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 1.05 }}
      transition={{ duration: 0.4 }}
    >
      <div className="glass-card" style={{ width: '100%', maxWidth: '450px' }}>
        <div className="text-center mb-8">
          <h2 className="gradient-text-vibrant" style={{ marginBottom: 'var(--space-2)' }}>Create Account</h2>
          <p>Join to save your results and personalized roadmap.</p>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-3) var(--space-4)',
            marginBottom: 'var(--space-4)',
            color: '#fca5a5',
            fontSize: 'var(--font-size-sm)',
          }}>
            {error}
          </div>
        )}

        {/* Google Sign-Up Button */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: 'var(--space-4)',
        }}>
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            theme="filled_black"
            size="large"
            width="400"
            text="signup_with"
            shape="pill"
          />
        </div>

        {loading && (
          <p className="text-center" style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-muted)',
          }}>
            Creating your account...
          </p>
        )}

        <div className="text-center mt-8" style={{ fontSize: 'var(--font-size-sm)' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>Already have an account? </span>
          <Link to="/login" style={{ fontWeight: 600, color: 'var(--color-accent-2)' }}>Sign in</Link>
        </div>
      </div>
    </motion.div>
  );
}

