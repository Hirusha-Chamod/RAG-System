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
      {/* Message Header (Sender Name & Timestamp) */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
        <span style={{ fontWeight: 600, color: isUser ? 'var(--accent-cyan)' : 'var(--accent-purple)' }}>
          {isUser ? 'You' : 'AI Nexus'}
        </span>
        <span>•</span>
        <span>{message.timestamp}</span>
      </div>

      {/* Bubble Container */}
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

      {/* Clean Sources Accordion */}
      {!isUser && message.sources && message.sources.length > 0 && (
        <div style={{ marginTop: '8px', width: '100%' }}>
          <button
            onClick={() => setShowSources(!showSources)}
            style={{
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-color)',
              borderRadius: '20px',
              color: 'var(--text-dim)',
              fontSize: '0.75rem',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 12px',
              transition: 'all 0.2s ease',
            }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
            </svg>
            <span>Sources</span>
            <span style={{
              background: 'rgba(99, 102, 241, 0.2)',
              color: 'var(--accent-purple)',
              padding: '1px 6px',
              borderRadius: '10px',
              fontSize: '0.7rem',
              fontWeight: 600
            }}>
              {message.sources.length}
            </span>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ transform: showSources ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s ease' }}>
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>

          {showSources && (
            <div
              className="animate-fade-in"
              style={{
                marginTop: '8px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              {message.sources.map((src, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '10px 14px',
                    borderRadius: '10px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    fontSize: '0.8rem',
                  }}
                >
                  <div style={{ fontWeight: 600, color: 'var(--accent-cyan)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                    <span>{src.source}</span>
                  </div>
                  <div style={{ color: 'var(--text-dim)', lineHeight: '1.45' }}>
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
