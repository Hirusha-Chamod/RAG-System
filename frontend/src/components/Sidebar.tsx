import React from 'react';

interface Props {
  user: any;
  sessions: string[];
  activeSession: string;
  onSelectSession: (session: string) => void;
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
  onNewChat,
  onOpenUpload,
  onOpenDocuments,
  onOpenMemory,
}) => {
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
        <div style={{ width: '34px', height: '34px', borderRadius: '8px', background: 'linear-gradient(135deg, var(--primary), var(--accent-cyan))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '1rem', color: '#fff' }}>
          NX
        </div>
        <div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>AI Nexus RAG</div>
          <div style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>v0.4.0 • Enterprise</div>
        </div>
      </div>

      {/* New Chat Button */}
      <button
        onClick={onNewChat}
        className="btn btn-primary"
        style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', justifyContent: 'flex-start', fontSize: '0.9rem' }}
        disabled={!user}
      >
        <span style={{ fontSize: '1.2rem', lineHeight: 1 }}>+</span> New Chat
      </button>

      {/* Action Buttons: Ingest, Documents & Memory */}
      {user && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <button
            onClick={onOpenUpload}
            className="btn btn-secondary"
            style={{ width: '100%', justifyContent: 'flex-start', padding: '8px 12px', fontSize: '0.82rem' }}
          >
            📁 Ingest Files
          </button>
          <button
            onClick={onOpenDocuments}
            className="btn btn-secondary"
            style={{ width: '100%', justifyContent: 'flex-start', padding: '8px 12px', fontSize: '0.82rem' }}
          >
            📄 My Documents
          </button>
          <button
            onClick={onOpenMemory}
            className="btn btn-secondary"
            style={{ width: '100%', justifyContent: 'flex-start', padding: '8px 12px', fontSize: '0.82rem' }}
          >
            🧠 Long-Term Memory
          </button>
        </div>
      )}

      {/* Chat Sessions History List */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '6px', letterSpacing: '0.05em' }}>
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
            const isActive = sess === activeSession;
            return (
              <button
                key={sess}
                onClick={() => onSelectSession(sess)}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  border: isActive ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid transparent',
                  background: isActive ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                  color: isActive ? '#fff' : 'var(--text-muted)',
                  fontSize: '0.83rem',
                  fontWeight: isActive ? 600 : 400,
                  cursor: 'pointer',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease',
                }}
              >
                💬 {sess.replace('session_', 'Session ')}
              </button>
            );
          })
        )}
      </div>

      {/* User Profile Footer */}
      {user && (
        <div style={{ paddingTop: '12px', borderTop: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '30px', height: '30px', borderRadius: '50%', background: 'var(--accent-purple)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.85rem' }}>
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
