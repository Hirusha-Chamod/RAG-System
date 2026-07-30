import React, { useState, useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import type { ChatMessage } from '../types';

interface Props {
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  loading: boolean;
  disabled?: boolean;
}

export const ChatWindow: React.FC<Props> = ({ messages, onSendMessage, loading, disabled }) => {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading || disabled) return;
    onSendMessage(inputText);
    setInputText('');
  };

  return (
    <div
      className="glass-panel"
      style={{
        flex: 1,
        margin: '16px',
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 120px)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          flex: 1,
          padding: '20px 24px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {messages.length === 0 ? (
          <div
            style={{
              margin: 'auto',
              textAlign: 'center',
              maxWidth: '440px',
              padding: '32px',
              color: 'var(--text-muted)',
            }}
          >
            <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>💬</div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>
              Welcome to AI Nexus RAG Engine
            </h3>
            <p style={{ fontSize: '0.85rem', lineHeight: '1.5', color: 'var(--text-muted)' }}>
              Sign in to ingest PDF, DOCX, XLSX, TXT, MD, or images. Ask questions grounded in your library with 3-way decision gates and multi-session memory!
            </p>
          </div>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: 'var(--accent-cyan)', fontSize: '0.85rem' }}>
            <div className="pulse-glow" style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-cyan)' }} />
            <span>AI Nexus is searching vector space & cross-encoder reranking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        style={{
          padding: '16px 20px',
          borderTop: '1px solid var(--border-color)',
          background: 'rgba(15, 23, 42, 0.4)',
          display: 'flex',
          gap: '12px',
        }}
      >
        <input
          type="text"
          className="input-field"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={disabled ? 'Please sign in to send chat messages...' : 'Ask a question grounded in your documents...'}
          disabled={disabled || loading}
          style={{ flex: 1, padding: '12px 16px', fontSize: '0.95rem' }}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={disabled || loading || !inputText.trim()}
          style={{ padding: '0 24px' }}
        >
          Send
        </button>
      </form>
    </div>
  );
};
