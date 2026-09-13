/**
 * Results — Post-deep-dive reveal of top 3 domains.
 *
 * §12: Shows only top 3 domains. #1 is "Strongest Match" (personalized),
 * #2/#3 are "Worth Exploring" (general). Includes insight summary card.
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { assessmentAPI } from '../api/client';
import './Results.css';

const DOMAIN_META = {
  backend: { icon: '⚙️', color: '#8b5cf6', desc: 'Build the systems behind the interface.' },
  frontend: { icon: '🎨', color: '#06b6d4', desc: 'Craft experiences people love to use.' },
  devops: { icon: '🛡️', color: '#10b981', desc: 'Keep systems alive, fast, and reliable.' },
  data_eng: { icon: '📊', color: '#f59e0b', desc: 'Build pipelines that turn data into insight.' },
  ai_ml: { icon: '🤖', color: '#ec4899', desc: 'Teach machines to learn and decide.' },
  cybersecurity: { icon: '🔒', color: '#ef4444', desc: 'Protect systems from those who would break them.' },
  product_eng: { icon: '🎯', color: '#3b82f6', desc: 'Bridge user needs and engineering decisions.' },
};

export default function Results() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [topDomains, setTopDomains] = useState([]);
  const [thinkingStyles, setThinkingStyles] = useState([]);
  const [insightSummary, setInsightSummary] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const res = await assessmentAPI.getResults();
        setTopDomains(res.data.top_domains || []);
        setThinkingStyles(res.data.thinking_styles || []);
        setInsightSummary(res.data.insight_summary || '');
        setLoading(false);
      } catch (err) {
        const msg = err?.response?.data?.error || 'Could not load results. Please complete the deep dive first.';
        setError(msg);
        setLoading(false);
      }
    };
    fetchResults();
  }, []);

  if (loading) {
    return (
      <div className="results-page results-loading">
        <motion.div
          className="loading-orb"
          animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
        <h2>Calculating your results…</h2>
      </div>
    );
  }

  if (error) {
    return (
      <div className="results-page results-error">
        <h2>⚠️ {error}</h2>
        <button className="btn btn-primary" onClick={() => navigate('/deep-dive')}>
          Start Deep Dive
        </button>
      </div>
    );
  }

  return (
    <motion.div
      className="results-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
    >
      <div className="container">
        {/* Header */}
        <motion.div
          className="results-header"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        >
          <h1>
            Your <span className="gradient-text-vibrant">Domain Map</span>
          </h1>
          <p className="results-subtitle">
            Your top 3 engineering domains, ranked by how your instincts aligned during the assessment.
          </p>
        </motion.div>

        {/* Top 3 Podium */}
        {topDomains.length >= 3 && (
          <div className="results-podium">
            {topDomains.map((d, i) => {
              const meta = DOMAIN_META[d.domain] || { icon: '💡', color: '#888', desc: '' };
              const heights = ['200px', '160px', '130px'];
              const delays = [0.4, 0.2, 0.6];

              return (
                <motion.div
                  key={d.domain}
                  className={`podium-item podium-${i + 1} ${d.personalized ? 'podium-personalized' : ''}`}
                  initial={{ opacity: 0, y: 60 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.7, delay: delays[i], ease: [0.22, 1, 0.36, 1] }}
                  style={{ order: i === 0 ? 1 : i === 1 ? 0 : 2 }}
                >
                  {d.personalized && (
                    <span className="podium-badge">✨ {d.label}</span>
                  )}
                  <span className="podium-icon">{meta.icon}</span>
                  <span className="podium-label">{d.display_name}</span>
                  <motion.div
                    className="podium-bar"
                    style={{ background: meta.color }}
                    initial={{ height: 0 }}
                    animate={{ height: heights[i] }}
                    transition={{ duration: 0.8, delay: delays[i] + 0.2, ease: 'easeOut' }}
                  />
                  <span className="podium-rank">#{i + 1}</span>
                </motion.div>
              );
            })}
          </div>
        )}

        {/* Insight Summary Card */}
        {insightSummary && (
          <motion.div
            className="results-insight glass-card"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1 }}
          >
            <div className="insight-header">
              <span className="insight-icon">💡</span>
              <h3>Your Deep-Dive Insights</h3>
            </div>
            <p className="insight-text">{insightSummary}</p>
          </motion.div>
        )}

        {/* Thinking styles summary */}
        {thinkingStyles.length > 0 && (
          <motion.div
            className="results-styles glass-card"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.3 }}
          >
            <h3 style={{ marginBottom: 'var(--space-6)' }}>Your Thinking Styles</h3>
            <div className="styles-mini-grid">
              {thinkingStyles.map((style) => (
                <div key={style.style_key} className="style-mini-card">
                  <span className="style-mini-icon">{style.icon || '🧠'}</span>
                  <span className="style-mini-name">
                    {style.name || style.style_key
                      .split('_')
                      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                      .join(' ')
                      .replace(/^/, 'The ')}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Roadmap CTAs */}
        <motion.div
          className="results-roadmaps"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.6 }}
        >
          <h3 style={{ textAlign: 'center', marginBottom: 'var(--space-6)' }}>
            Explore Your <span className="gradient-text">Roadmaps</span>
          </h3>
          <div className="roadmap-cards">
            {topDomains.map((d) => {
              const meta = DOMAIN_META[d.domain] || { icon: '💡', color: '#888', desc: '' };
              return (
                <motion.button
                  key={d.domain}
                  className={`roadmap-card glass-card ${d.personalized ? 'roadmap-card-primary' : ''}`}
                  onClick={() => navigate(`/roadmap/${d.domain}`)}
                  whileHover={{ scale: 1.03, y: -4 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span className="roadmap-card-icon">{meta.icon}</span>
                  <span className="roadmap-card-label">{d.display_name}</span>
                  <span className="roadmap-card-match" style={{ color: meta.color }}>
                    {d.personalized ? '★ Strongest Match' : 'Worth Exploring'}
                  </span>
                  <span className="roadmap-card-cta">
                    {d.personalized ? 'View Personalized Roadmap →' : 'View Roadmap →'}
                  </span>
                </motion.button>
              );
            })}
          </div>
        </motion.div>

        {/* Reset */}
        <motion.div
          className="results-footer"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2 }}
        >
          <button
            className="btn btn-secondary"
            onClick={() => navigate('/')}
          >
            ← Back to Home
          </button>
        </motion.div>
      </div>
    </motion.div>
  );
}
