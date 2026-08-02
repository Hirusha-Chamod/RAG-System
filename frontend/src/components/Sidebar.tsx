import React, { useState } from 'react';

export interface SessionItem {
  session_id: string;
  title: string;
}

interface Props {
  user: any;
  sessions: (string | SessionItem)[];
  activeSession: string;
  onSelectSession: (session: string) => void;
  onDeleteSession?: (session: string) => void;
  onNewChat: () => void;
  onOpenUpload: () => void;
  onOpenDocuments: () => void;
  onOpenMemory: () => void;
}

export const Sidebar: React.FC<Props> = ({
  user,
  sessions,
  activeSession,
  onSelectSession,
  onDeleteSession,
  onNewChat,
  onOpenUpload,
  onOpenDocuments,
  onOpenMemory,
}) => {
  const [hoveredSession, setHoveredSession] = useState<string | null>(null);

  return (
    <aside
      className="glass-panel"
      style={{
        width: '260px',
        margin: '16px 0 16px 16px',
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 32px)',
        padding: '16px',
        gap: '16px',
      }}
    >
      {/* Brand & App Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ width: '34px', height: '34px', borderRadius: '8px', background: 'linear-gradient(135deg, var(--primary), var(--accent-cyan))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.95rem', color: '#fff', letterSpacing: '-0.02em' }}>
          NX
        </div>
        <div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)' }}>AI Nexus RAG</div>
          <div style={{ fontSize: '0.68rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>v0.4.0 • Enterprise</div>
        </div>
      </div>

      {/* New Chat Button */}
      <button
        onClick={onNewChat}
        className="btn btn-primary"
        style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', justifyContent: 'flex-start', fontSize: '0.88rem', gap: '8px' }}
        disabled={!user}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        New Chat
      </button>

      {/* Action Buttons: Upload Files, Documents & Memory */}
      {user && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <button
            onClick={onOpenUpload}
            className="btn btn-secondary"
            style={{ width: '100%', justifyContent: 'flex-start', padding: '8px 12px', fontSize: '0.82rem', gap: '8px' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            Upload Files
          </button>
          <button
            onClick={onOpenDocuments}
            className="btn btn-secondary"
            style={{ width: '100%', justifyContent: 'flex-start', padding: '8px 12px', fontSize: '0.82rem', gap: '8px' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            My Documents
          </button>
          <button
            onClick={onOpenMemory}
            className="btn btn-secondary"
            style={{ width: '100%', justifyContent: 'flex-start', padding: '8px 12px', fontSize: '0.82rem', gap: '8px' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"></path>
              <circle cx="12" cy="12" r="3"></circle>
            </svg>
            Long-Term Memory
          </button>
        </div>
      )}

      {/* Chat Sessions History List */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '6px', letterSpacing: '0.05em' }}>
          Recent Conversations
        </div>

        {!user ? (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontStyle: 'italic', padding: '8px 0' }}>
            Sign in to view past chat threads
          </div>
        ) : sessions.length === 0 ? (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontStyle: 'italic', padding: '8px 0' }}>
            No chat sessions yet
          </div>
        ) : (
          sessions.map((sess) => {
            const id = typeof sess === 'string' ? sess : sess.session_id;
            let displayTitle = typeof sess === 'string' 
              ? sess.replace('session_', 'Session ') 
              : sess.title;

            if (id === 'session_default' && displayTitle.startsWith('Session')) {
              displayTitle = 'General Chat';
            }

            const isActive = id === activeSession;
            const isHovered = hoveredSession === id;

            return (
              <div
                key={id}
                onMouseEnter={() => setHoveredSession(id)}
                onMouseLeave={() => setHoveredSession(null)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  width: '100%',
                  borderRadius: '8px',
                  border: isActive ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid transparent',
                  background: isActive ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                  transition: 'all 0.15s ease',
                  overflow: 'hidden',
                }}
              >
                <button
                  onClick={() => onSelectSession(id)}
                  style={{
                    flex: 1,
                    textAlign: 'left',
                    padding: '8px 10px',
                    background: 'none',
                    border: 'none',
                    color: isActive ? '#fff' : 'var(--text-muted)',
                    fontSize: '0.82rem',
                    fontWeight: isActive ? 600 : 400,
                    cursor: 'pointer',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: isActive ? 1 : 0.6, flexShrink: 0 }}>
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{displayTitle}</span>
                </button>

                {onDeleteSession && (isHovered || isActive) && id !== 'session_default' && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(id);
                    }}
                    title="Delete session"
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-dim)',
                      padding: '4px 6px',
                      cursor: 'pointer',
                      borderRadius: '4px',
                      opacity: 0.7,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
                    onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.7')}
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* User Profile Footer */}
      {user && (
        <div style={{ paddingTop: '12px', borderTop: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '30px', height: '30px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent-purple), var(--primary))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.85rem', color: '#fff' }}>
            {user.username[0].toUpperCase()}
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
              {user.username}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
              {user.email}
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
