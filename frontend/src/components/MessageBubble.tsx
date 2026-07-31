import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import type { ChatMessage } from '../types';

interface Props {
  message: ChatMessage;
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const isUser = message.sender === 'user';
  const [showSources, setShowSources] = useState(false);

  return (
    <div
      className="animate-fade-in"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '16px',
        maxWidth: '85%',
        alignSelf: isUser ? 'flex-end' : 'flex-start',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
        <span style={{ fontWeight: 600, color: isUser ? 'var(--accent-cyan)' : 'var(--accent-purple)' }}>
          {isUser ? 'You' : 'AI Nexus'}
        </span>
        <span>•</span>
        <span>{message.timestamp}</span>

        {!isUser && message.relevance_action && (
          <span className={`badge badge-${message.relevance_action}`} style={{ marginLeft: '4px' }}>
            {message.relevance_action === 'synthesize' && '✓ Grounded Pass'}
            {message.relevance_action === 'clarify' && '⚡ Clarification'}
            {message.relevance_action === 'fallback' && '🛡️ Fallback (FR-10)'}
          </span>
        )}
      </div>

      <div
        className="glass-panel markdown-content"
        style={{
          padding: '14px 18px',
          borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          background: isUser
            ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(139, 92, 246, 0.25))'
            : 'rgba(21, 27, 43, 0.85)',
          border: isUser
            ? '1px solid rgba(99, 102, 241, 0.4)'
            : '1px solid var(--border-color)',
          color: 'var(--text-main)',
          fontSize: '0.92rem',
          lineHeight: '1.6',
          wordBreak: 'break-word',
          boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
        }}
      >
        {isUser ? (
          <div style={{ whiteSpace: 'pre-wrap' }}>{message.text}</div>
        ) : (
          <ReactMarkdown>{message.text}</ReactMarkdown>
        )}
      </div>

      {!isUser && message.sources && message.sources.length > 0 && (
        <div style={{ marginTop: '8px', width: '100%' }}>
          <button
            onClick={() => setShowSources(!showSources)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--accent-cyan)',
              fontSize: '0.78rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 0',
            }}
          >
            {showSources ? '▼ Hide' : '▶ Show'} Grounding Sources ({message.sources.length} matching parent documents)
          </button>

          {showSources && (
            <div
              className="animate-fade-in"
              style={{
                marginTop: '6px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              {message.sources.map((src, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '8px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    fontSize: '0.8rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontWeight: 600, color: 'var(--text-muted)' }}>
                    <span>📄 {src.source}</span>
                    <span style={{ color: 'var(--accent-purple)', fontFamily: 'var(--font-mono)' }}>
                      Relevance score: {src.score}
                    </span>
                  </div>
                  <div style={{ color: 'var(--text-dim)', fontStyle: 'italic', lineHeight: '1.4' }}>
                    "{src.content}"
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
