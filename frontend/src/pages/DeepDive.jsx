/**
 * DeepDive — Gemini-powered conversational deep-dive chat.
 *
 * §8: The domain is fetched from the backend (session.primary_domain),
 * NOT from the URL. This ensures the user always deep-dives into their
 * backend-ranked #1 domain.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { deepDiveAPI } from '../api/client';
import './DeepDive.css';

const DOMAIN_META = {
  backend:      { label: 'Backend Engineering',  icon: '⚙️', color: '#8b5cf6' },
  frontend:     { label: 'Frontend Engineering',  icon: '🎨', color: '#06b6d4' },
  devops:       { label: 'DevOps Engineering',    icon: '🛡️', color: '#10b981' },
  data_eng:     { label: 'Data Engineering',      icon: '📊', color: '#f59e0b' },
  ai_ml:        { label: 'AI/ML Engineering',     icon: '🤖', color: '#ec4899' },
  cybersecurity:{ label: 'Cybersecurity',          icon: '🔒', color: '#ef4444' },
  product_eng:  { label: 'Product Engineering',    icon: '🎯', color: '#3b82f6' },
};

const MAX_WORDS = 60;

export default function DeepDive() {
  const { domain: urlDomain } = useParams(); // optional fallback
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const [domain, setDomain] = useState(urlDomain || null);
  const [messages, setMessages] = useState([]);
  const [chatStatus, setChatStatus] = useState('loading'); // loading | chatting | completed | error
  const [isTyping, setIsTyping] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [aiTurnCount, setAiTurnCount] = useState(0);
  const [userTurnCount, setUserTurnCount] = useState(0);
  const [error, setError] = useState(null);

  const meta = DOMAIN_META[domain] || { label: domain || 'Loading…', icon: '💬', color: '#8b5cf6' };
  const wordCount = inputValue.trim() ? inputValue.trim().split(/\s+/).length : 0;

  // ── Auto-scroll to latest message ──
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  // ── Fetch domain from backend, then start deep dive ──
  useEffect(() => {
    const initDeepDive = async () => {
      try {
        // §8: Always fetch the backend-owned domain
        let resolvedDomain = urlDomain;
        if (!resolvedDomain) {
          const domainRes = await deepDiveAPI.getDomain();
          resolvedDomain = domainRes.data.domain;
        }
        setDomain(resolvedDomain);

        // Start the deep dive chat
        const res = await deepDiveAPI.start(resolvedDomain);
        const chat = res.data.chat;

        // Use the domain returned by the server (may differ from URL param)
        if (res.data.domain) {
          setDomain(res.data.domain);
        }

        setMessages(chat.transcript || []);
        setAiTurnCount(chat.ai_turn_count || 0);
        setUserTurnCount(chat.user_turn_count || 0);

        if (chat.status === 'completed' || chat.status === 'skipped' || chat.status === 'terminated') {
          setChatStatus('completed');
        } else {
          // Show typing animation for opening message if freshly started
          if (res.data.message === 'Deep-dive started.' && chat.transcript?.length === 1) {
            setMessages([]);
            setIsTyping(true);
            const delay = 700 + Math.random() * 700;
            setTimeout(() => {
              setIsTyping(false);
              setMessages(chat.transcript);
              setChatStatus('chatting');
            }, delay);
          } else {
            setChatStatus('chatting');
          }
        }
      } catch (err) {
        setError('Could not start the deep-dive. Please try again.');
        setChatStatus('error');
      }
    };
    initDeepDive();
  }, [urlDomain]);

  // ── Send user message ──
  const handleSend = async () => {
    if (!inputValue.trim() || wordCount > MAX_WORDS || isSending || !domain) return;

    const content = inputValue.trim();
    setInputValue('');
    setIsSending(true);

    // Optimistically add user message
    const userMsg = { role: 'user', content, turn: userTurnCount + 1 };
    setMessages((prev) => [...prev, userMsg]);

    // Show typing indicator with random delay
    setIsTyping(true);

    try {
      const res = await deepDiveAPI.sendMessage(domain, { content });
      const chat = res.data.chat;

      // Wait for min typing delay
      const minDelay = 700 + Math.random() * 700;
      await new Promise((resolve) => setTimeout(resolve, minDelay));

      setIsTyping(false);
      setMessages(chat.transcript || []);
      setAiTurnCount(chat.ai_turn_count || 0);
      setUserTurnCount(chat.user_turn_count || 0);

      if (chat.status !== 'in_progress') {
        setChatStatus('completed');
      }
    } catch (err) {
      setIsTyping(false);
      // Add error message inline
      setMessages((prev) => [
        ...prev,
        { role: 'ai', content: "Something went wrong. Let's move on to your roadmap!", turn: -1 },
      ]);
      setChatStatus('completed');
    } finally {
      setIsSending(false);
    }
  };

  // ── Skip deep dive ──
  const handleSkip = async () => {
    try {
      if (domain) await deepDiveAPI.skip(domain);
    } catch {
      // Skip silently
    }
    navigate(`/roadmap/${domain}`);
  };

  // ── Navigate to roadmap ──
  const goToRoadmap = () => {
    navigate(`/roadmap/${domain}`);
  };

  // ── Handle textarea input ──
  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ── Word counter style ──
  const getWordCounterClass = () => {
    if (wordCount > MAX_WORDS) return 'word-counter danger';
    if (wordCount > MAX_WORDS * 0.8) return 'word-counter warning';
    return 'word-counter safe';
  };

  // ── Loading state ──
  if (chatStatus === 'loading') {
    return (
      <div className="deep-dive-page deep-dive-loading">
        <motion.div
          className="loading-orb"
          style={{ background: `radial-gradient(circle, ${meta.color}40, transparent)` }}
          animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
        <h2>Starting your deep-dive…</h2>
      </div>
    );
  }

  // ── Error state ──
  if (chatStatus === 'error') {
    return (
      <div className="deep-dive-page deep-dive-error">
        <h2>⚠️ {error}</h2>
        <button className="btn btn-primary" onClick={() => navigate('/thinking-styles')}>
          Back to Thinking Styles
        </button>
      </div>
    );
  }

  return (
    <motion.div
      className="deep-dive-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
    >
      <div className="container container-sm">
        {/* Header */}
        <motion.div
          className="deep-dive-header"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div
            className="deep-dive-header-accent"
            style={{ background: `radial-gradient(circle, ${meta.color}, transparent)` }}
          />
          <span
            className="deep-dive-domain-badge"
            style={{ color: meta.color, borderColor: `${meta.color}40`, background: `${meta.color}10` }}
          >
            {meta.icon} {meta.label}
          </span>
          <h1>
            Let's <span className="gradient-text">Deep Dive</span>
          </h1>
          <p className="deep-dive-subtitle">
            A quick chat to personalise your roadmap. Answer naturally — there are no wrong answers.
          </p>
        </motion.div>

        {/* Turn Progress */}
        {chatStatus === 'chatting' && (
          <motion.div
            className="deep-dive-progress"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className={`progress-dot ${
                  i < aiTurnCount ? 'completed' : i === aiTurnCount ? 'active' : ''
                }`}
                style={{ color: meta.color }}
              />
            ))}
            <span className="progress-label">
              Turn {Math.min(userTurnCount + 1, 4)} of 4
            </span>
          </motion.div>
        )}

        {/* Messages */}
        <div className="deep-dive-chat-container">
          <div className="deep-dive-messages">
            <AnimatePresence>
              {messages.map((msg, i) => (
                <motion.div
                  key={`${msg.role}-${i}`}
                  className={`chat-message ${msg.role}`}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: i === messages.length - 1 ? 0.05 : 0 }}
                >
                  <div className={`chat-avatar ${msg.role === 'ai' ? 'ai-avatar' : 'user-avatar'}`}>
                    {msg.role === 'ai' ? '✨' : '👤'}
                  </div>
                  <div
                    className={`chat-bubble ${msg.role === 'ai' ? 'ai-bubble' : 'user-bubble'}`}
                    style={msg.role === 'ai' ? { borderLeftColor: meta.color } : undefined}
                  >
                    {msg.content}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Typing Indicator */}
            {isTyping && (
              <div className="typing-indicator">
                <div className="chat-avatar ai-avatar">✨</div>
                <div className="typing-dots" style={{ borderLeftColor: meta.color }}>
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area — only show during active chat */}
          {chatStatus === 'chatting' && (
            <motion.div
              className="deep-dive-input-area"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
            >
              <textarea
                ref={textareaRef}
                className="deep-dive-textarea"
                placeholder="Share your thoughts…"
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                disabled={isSending}
                rows={2}
                id="deep-dive-input"
              />
              <div className="deep-dive-input-footer">
                <span className={getWordCounterClass()}>
                  {wordCount}/{MAX_WORDS} words
                </span>
                <div className="input-actions">
                  <button
                    className="btn-skip"
                    onClick={handleSkip}
                    disabled={isSending}
                  >
                    Skip Chat →
                  </button>
                  <button
                    className="btn-send"
                    style={{ background: meta.color }}
                    onClick={handleSend}
                    disabled={!inputValue.trim() || wordCount > MAX_WORDS || isSending}
                    id="deep-dive-send"
                  >
                    {isSending ? '…' : 'Send'}
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* Completed / Navigation */}
        {chatStatus === 'completed' && (
          <motion.div
            className="deep-dive-completed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            <span className="completed-icon">🎯</span>
            <p className="completed-text">
              Your roadmap has been personalised. Let's see what's next!
            </p>
            <motion.button
              className="btn-roadmap"
              style={{ background: meta.color }}
              onClick={goToRoadmap}
              whileHover={{ scale: 1.03, y: -2 }}
              whileTap={{ scale: 0.98 }}
              id="continue-to-roadmap"
            >
              Continue to Roadmap →
            </motion.button>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
