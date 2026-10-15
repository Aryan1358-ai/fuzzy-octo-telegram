/**
 * Signup Page — supports email/password and Google OAuth.
 */
import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../context/AuthContext';

export default function Signup() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { register, googleLogin } = useAuth();

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await register(name, email, password);
      navigate('/context');
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

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
          marginBottom: 'var(--space-6)',
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

        {/* Divider */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
        }}>
          <div style={{ flex: 1, height: '1px', background: 'var(--color-border)' }} />
          <span style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            fontWeight: 500,
          }}>or sign up with email</span>
          <div style={{ flex: 1, height: '1px', background: 'var(--color-border)' }} />
        </div>

        <form onSubmit={handleSignup} className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <label htmlFor="name" style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600 }}>
              Full Name
            </label>
            <input
              id="name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Jane Doe"
              style={{
                width: '100%',
                padding: 'var(--space-3) var(--space-4)',
                background: 'rgba(0,0,0,0.2)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                color: 'white',
                outline: 'none',
              }}
              onFocus={(e) => (e.target.style.borderColor = 'var(--color-accent-2)')}
              onBlur={(e) => (e.target.style.borderColor = 'var(--color-border)')}
            />
          </div>

          <div className="flex flex-col gap-2">
            <label htmlFor="email" style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600 }}>
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              style={{
                width: '100%',
                padding: 'var(--space-3) var(--space-4)',
                background: 'rgba(0,0,0,0.2)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                color: 'white',
                outline: 'none',
              }}
              onFocus={(e) => (e.target.style.borderColor = 'var(--color-accent-2)')}
              onBlur={(e) => (e.target.style.borderColor = 'var(--color-border)')}
            />
          </div>

          <div className="flex flex-col gap-2">
            <label htmlFor="password" style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600 }}>
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              minLength={6}
              style={{
                width: '100%',
                padding: 'var(--space-3) var(--space-4)',
                background: 'rgba(0,0,0,0.2)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                color: 'white',
                outline: 'none',
              }}
              onFocus={(e) => (e.target.style.borderColor = 'var(--color-accent-2)')}
              onBlur={(e) => (e.target.style.borderColor = 'var(--color-border)')}
            />
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              At least 6 characters
            </span>
          </div>

          <motion.button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: 'var(--space-4)', marginTop: 'var(--space-2)' }}
            disabled={loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {loading ? 'Creating Account...' : 'Sign Up'}
          </motion.button>
        </form>

        <div className="text-center mt-8" style={{ fontSize: 'var(--font-size-sm)' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>Already have an account? </span>
          <Link to="/login" style={{ fontWeight: 600, color: 'var(--color-accent-2)' }}>Sign in</Link>
        </div>
      </div>
    </motion.div>
  );
}
