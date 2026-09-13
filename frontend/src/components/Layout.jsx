/**
 * App Layout — shell with progress bar for assessment stages.
 *
 * Phase 15: 6-stage progress bar, mobile hamburger menu,
 * and responsive drawer.
 */
import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAssessment } from '../context/AssessmentContext';
import { useAuth } from '../context/AuthContext';
import './Layout.css';

const STAGES = [
  { key: 'context_intake', label: 'Context', path: '/context' },
  { key: 'pre_assessment', label: 'Activities', path: '/activity/1' },
  { key: 'thinking_styles', label: 'Styles', path: '/thinking-styles' },
  { key: 'deep_dive', label: 'Deep Dive', path: '/deep-dive' },
  { key: 'results', label: 'Results', path: '/results' },
];

export default function Layout({ children }) {
  const { session } = useAssessment();
  const { isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const currentStage = session?.current_stage || 'context_intake';
  // Map validation to deep_dive slot in UI
  const uiStage = currentStage === 'validation' ? 'deep_dive' : currentStage;
  const currentIdx = STAGES.findIndex(s => s.key === uiStage);
  const progress = Math.max(0, ((currentIdx + 1) / STAGES.length) * 100);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch {
      // ignore
    }
    setMenuOpen(false);
  };

  return (
    <div className="layout">
      <header className="layout-header">
        <div className="container">
          <div className="header-content">
            <a href="/" className="logo">
              <span className="logo-icon">🎯</span>
              <span className="logo-text gradient-text">Make Your Move</span>
            </a>

            {/* Desktop progress bar */}
            <div className="progress-section progress-desktop">
              <div className="progress-stages">
                {STAGES.map((stage, i) => (
                  <span
                    key={stage.key}
                    className={`stage-dot ${i <= currentIdx ? 'active' : ''} ${i === currentIdx ? 'current' : ''}`}
                    title={stage.label}
                  >
                    <span className="stage-label">{stage.label}</span>
                  </span>
                ))}
              </div>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
              </div>
            </div>

            {/* Mobile hamburger */}
            <button
              className={`hamburger ${menuOpen ? 'open' : ''}`}
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Menu"
            >
              <span />
              <span />
              <span />
            </button>
          </div>
        </div>

        {/* Mobile progress bar (always visible) */}
        <div className="mobile-progress">
          <div className="progress-bar-bg">
            <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>
      </header>

      {/* Mobile menu drawer */}
      {menuOpen && (
        <div className="mobile-drawer-overlay" onClick={() => setMenuOpen(false)}>
          <nav className="mobile-drawer" onClick={e => e.stopPropagation()}>
            <div className="drawer-header">
              <span className="gradient-text" style={{ fontWeight: 700 }}>Navigation</span>
              <button className="drawer-close" onClick={() => setMenuOpen(false)}>✕</button>
            </div>
            <div className="drawer-stages">
              {STAGES.map((stage, i) => (
                <button
                  key={stage.key}
                  className={`drawer-stage-btn ${i <= currentIdx ? 'completed' : ''} ${i === currentIdx ? 'current' : ''}`}
                  onClick={() => {
                    if (i <= currentIdx) {
                      navigate(stage.path);
                      setMenuOpen(false);
                    }
                  }}
                  disabled={i > currentIdx}
                >
                  <span className="drawer-stage-num">{i + 1}</span>
                  <span className="drawer-stage-label">{stage.label}</span>
                  {i < currentIdx && <span className="drawer-check">✓</span>}
                  {i === currentIdx && <span className="drawer-current">●</span>}
                </button>
              ))}
            </div>
            {isAuthenticated && (
              <button className="drawer-logout" onClick={handleLogout}>
                Sign Out
              </button>
            )}
          </nav>
        </div>
      )}

      <main className="layout-main">
        {children}
      </main>
    </div>
  );
}
