/**
 * Thinking Styles — dramatic reveal of 3-4 matched thinking styles
 * after completing all 6 activities.
 *
 * §7: No domain information is shown here. Domains are hidden until
 * after the deep-dive completes.
 */
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { assessmentAPI } from '../api/client';
import './ThinkingStyles.css';

export default function ThinkingStyles() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [styles, setStyles] = useState([]);
  const [revealed, setRevealed] = useState(false);
  const [showIndex, setShowIndex] = useState(-1);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStyles = async () => {
      try {
        const res = await assessmentAPI.getThinkingStyles();
        setStyles(res.data.thinking_styles || []);
        setLoading(false);

        // Start reveal sequence after brief pause
        setTimeout(() => {
          setRevealed(true);
        }, 800);
      } catch (err) {
        setError('Could not load thinking styles. Please complete all activities first.');
        setLoading(false);
      }
    };
    fetchStyles();
  }, []);

  // Staggered reveal of each style card
  useEffect(() => {
    if (!revealed || styles.length === 0) return;
    let idx = 0;
    const interval = setInterval(() => {
      setShowIndex(idx);
      idx++;
      if (idx >= styles.length) clearInterval(interval);
    }, 500);
    return () => clearInterval(interval);
  }, [revealed, styles.length]);

  if (loading) {
    return (
      <div className="ts-page ts-loading">
        <motion.div
          className="loading-orb"
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.5, 1, 0.5],
          }}
          transition={{ duration: 2, repeat: Infinity }}
        />
        <h2>Analyzing your behavioral patterns…</h2>
        <p>Mapping signals to thinking styles</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ts-page ts-error">
        <h2>⚠️ {error}</h2>
        <button className="btn btn-primary" onClick={() => navigate('/activity/1')}>
          Go to Activities
        </button>
      </div>
    );
  }

  return (
    <motion.div
      className="ts-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
    >
      <div className="container">
        {/* Header */}
        <motion.div
          className="ts-header"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        >
          <span className="ts-badge">Your Thinking DNA</span>
          <h1>
            Your <span className="gradient-text-vibrant">Thinking Styles</span>
          </h1>
          <p className="ts-subtitle">
            Based on how you approached the 6 challenges, here are the thinking
            patterns that define your engineering instincts.
          </p>
        </motion.div>

        {/* Style Cards */}
        <div className="ts-cards">
          <AnimatePresence>
            {styles.map((style, i) => (
              showIndex >= i && (
                <motion.div
                  key={style.style_key}
                  className={`ts-card ${i === 0 ? 'ts-card-primary' : ''}`}
                  initial={{ opacity: 0, y: 40, scale: 0.9 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{
                    duration: 0.6,
                    ease: [0.22, 1, 0.36, 1],
                  }}
                >
                  <div className="ts-card-rank">#{i + 1}</div>
                  <div className="ts-card-icon">{style.icon || '🧠'}</div>
                  <h3 className="ts-card-name">
                    {style.name || style.style_key
                      .split('_')
                      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                      .join(' ')
                      .replace(/^/, 'The ')}
                  </h3>
                  <p className="ts-card-description">{style.description}</p>

                  {/* Confidence bar */}
                  <div className="ts-confidence">
                    <div className="ts-confidence-label">
                      <span>Confidence</span>
                      <span>{Math.round((style.confidence || 0) * 100)}%</span>
                    </div>
                    <div className="ts-confidence-bar">
                      <motion.div
                        className="ts-confidence-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${(style.confidence || 0) * 100}%` }}
                        transition={{ duration: 1, delay: 0.3, ease: 'easeOut' }}
                      />
                    </div>
                  </div>
                </motion.div>
              )
            ))}
          </AnimatePresence>
        </div>

        {/* CTA — points to deep dive, not results */}
        {showIndex >= styles.length - 1 && (
          <motion.div
            className="ts-cta"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <p className="ts-cta-hint">
              Ready to go deeper? A short conversation will personalize your results.
            </p>
            <button
              className="btn btn-primary btn-lg"
              onClick={() => navigate('/deep-dive')}
            >
              Start Deep Dive →
            </button>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
