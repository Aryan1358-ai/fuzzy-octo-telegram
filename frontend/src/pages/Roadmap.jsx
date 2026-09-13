/**
 * Roadmap — personalized learning path for a specific domain.
 *
 * Phase 14: #1 domain gets deep-dive annotations + evidence.
 * #2/#3 get general roadmap with a note about personalizing.
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { assessmentAPI } from '../api/client';
import './Roadmap.css';

const DOMAIN_COLORS = {
  backend: '#8b5cf6',
  frontend: '#06b6d4',
  devops: '#10b981',
  data_eng: '#f59e0b',
  ai_ml: '#ec4899',
  cybersecurity: '#ef4444',
  product_eng: '#3b82f6',
};

const LEVEL_BADGES = {
  beginner: { label: 'Beginner', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' },
  intermediate: { label: 'Intermediate', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)' },
  advanced: { label: 'Advanced', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' },
};

export default function Roadmap() {
  const { domain } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [roadmap, setRoadmap] = useState(null);

  const domainColor = DOMAIN_COLORS[domain] || '#8b5cf6';

  useEffect(() => {
    const fetchRoadmap = async () => {
      try {
        const res = await assessmentAPI.getRoadmap(domain);
        setRoadmap(res.data);
        setLoading(false);
      } catch (err) {
        setError(`Could not load roadmap for "${domain}".`);
        setLoading(false);
      }
    };
    fetchRoadmap();
  }, [domain]);

  if (loading) {
    return (
      <div className="roadmap-page roadmap-loading">
        <motion.div
          className="loading-orb"
          style={{ background: `radial-gradient(circle, ${domainColor}40, transparent)` }}
          animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
        <h2>Loading your roadmap…</h2>
      </div>
    );
  }

  if (error || !roadmap) {
    return (
      <div className="roadmap-page roadmap-error">
        <h2>⚠️ {error || 'Roadmap not found.'}</h2>
        <button className="btn btn-primary" onClick={() => navigate('/results')}>
          Back to Results
        </button>
      </div>
    );
  }

  // Group steps by level
  const stepsByLevel = {};
  (roadmap.steps || []).forEach((step) => {
    if (!stepsByLevel[step.level]) stepsByLevel[step.level] = [];
    stepsByLevel[step.level].push(step);
  });

  return (
    <motion.div
      className="roadmap-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
    >
      <div className="container container-sm">
        {/* Back nav */}
        <motion.button
          className="roadmap-back"
          onClick={() => navigate('/results')}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          ← Back to Results
        </motion.button>

        {/* Header */}
        <motion.div
          className="roadmap-header"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        >
          <div
            className="roadmap-header-accent"
            style={{ background: `linear-gradient(135deg, ${domainColor}30, transparent)` }}
          />
          {roadmap.is_primary && (
            <span className="roadmap-personalized-badge" style={{ color: domainColor, borderColor: `${domainColor}40` }}>
              ✨ Your #1 Domain — Personalized Roadmap
            </span>
          )}
          <h1 style={{ color: domainColor }}>{roadmap.title}</h1>
          <p className="roadmap-desc">{roadmap.description}</p>
        </motion.div>

        {/* Timeline */}
        <div className="roadmap-timeline">
          <div className="timeline-line" style={{ background: `linear-gradient(to bottom, ${domainColor}, ${domainColor}20)` }} />

          {(roadmap.steps || []).map((step, i) => {
            const level = LEVEL_BADGES[step.level] || LEVEL_BADGES.beginner;
            return (
              <motion.div
                key={i}
                className="timeline-item"
                initial={{ opacity: 0, x: i % 2 === 0 ? -40 : 40 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.3 + i * 0.12 }}
              >
                <div className="timeline-dot" style={{ background: domainColor, boxShadow: `0 0 20px ${domainColor}40` }} />
                <div className="timeline-card glass-card">
                  <div className="timeline-card-header">
                    <span className="timeline-step-num" style={{ color: domainColor }}>
                      Step {i + 1}
                    </span>
                    <span
                      className="timeline-level-badge"
                      style={{ color: level.color, background: level.bg }}
                    >
                      {level.label}
                    </span>
                  </div>
                  <h3 className="timeline-title">{step.title}</h3>
                  <div className="timeline-meta">
                    <span className="timeline-duration">
                      🕐 {step.duration}
                    </span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Gemini Deep-Dive Annotations (primary domain only) */}
        {roadmap.annotations && roadmap.annotations.length > 0 && (
          <motion.div
            className="roadmap-annotations glass-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.5 }}
            style={{ borderLeft: `3px solid ${domainColor}` }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
              <span style={{ fontSize: '1.5rem' }}>✨</span>
              <h4 style={{ margin: 0, color: domainColor }}>Personalised for You</h4>
            </div>
            {roadmap.annotations.map((note, i) => (
              <motion.p
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.7 + i * 0.15 }}
                style={{
                  color: 'var(--color-text-secondary)',
                  padding: 'var(--space-3) 0',
                  borderBottom: i < roadmap.annotations.length - 1 ? '1px solid var(--color-border)' : 'none',
                  margin: 0,
                  fontSize: 'var(--font-size-sm)',
                  lineHeight: 1.7,
                }}
              >
                💡 {note}
              </motion.p>
            ))}
          </motion.div>
        )}

        {/* Structured Evidence — key skills from deep dive (primary domain only) */}
        {roadmap.structured_evidence && (
          <motion.div
            className="roadmap-evidence glass-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.8 }}
          >
            <h4 style={{ marginBottom: 'var(--space-4)' }}>🔍 What You Shared</h4>
            <div className="evidence-grid">
              {roadmap.structured_evidence.technologies?.length > 0 && (
                <div className="evidence-section">
                  <span className="evidence-label">Technologies</span>
                  <div className="evidence-tags">
                    {roadmap.structured_evidence.technologies.map((t, i) => (
                      <span key={i} className="evidence-tag" style={{ borderColor: domainColor }}>{t}</span>
                    ))}
                  </div>
                </div>
              )}
              {roadmap.structured_evidence.projects?.length > 0 && (
                <div className="evidence-section">
                  <span className="evidence-label">Projects</span>
                  <div className="evidence-tags">
                    {roadmap.structured_evidence.projects.map((p, i) => (
                      <span key={i} className="evidence-tag">{p}</span>
                    ))}
                  </div>
                </div>
              )}
              {roadmap.structured_evidence.strengths?.length > 0 && (
                <div className="evidence-section">
                  <span className="evidence-label">Strengths</span>
                  <div className="evidence-tags">
                    {roadmap.structured_evidence.strengths.map((s, i) => (
                      <span key={i} className="evidence-tag" style={{ borderColor: '#10b981' }}>{s}</span>
                    ))}
                  </div>
                </div>
              )}
              {roadmap.structured_evidence.gaps?.length > 0 && (
                <div className="evidence-section">
                  <span className="evidence-label">Areas to Grow</span>
                  <div className="evidence-tags">
                    {roadmap.structured_evidence.gaps.map((g, i) => (
                      <span key={i} className="evidence-tag" style={{ borderColor: '#f59e0b' }}>{g}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Fallback AI note if no deep-dive was completed */}
        {(!roadmap.annotations || roadmap.annotations.length === 0) && roadmap.ai_notes && (
          <motion.div
            className="roadmap-ai-note glass-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.5 }}
          >
            <span className="ai-note-icon">✨</span>
            <p>{roadmap.ai_notes}</p>
          </motion.div>
        )}

        {/* Other roadmaps */}
        <motion.div
          className="roadmap-explore"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.8 }}
        >
          <h4 style={{ textAlign: 'center', marginBottom: 'var(--space-4)' }}>
            Explore Other Domains
          </h4>
          <div className="roadmap-domain-pills">
            {Object.entries(DOMAIN_COLORS)
              .filter(([d]) => d !== domain)
              .map(([d, color]) => (
                <button
                  key={d}
                  className="domain-pill"
                  style={{ borderColor: color, color }}
                  onClick={() => navigate(`/roadmap/${d}`)}
                >
                  {d.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </button>
              ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
