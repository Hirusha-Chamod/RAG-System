import React from 'react';
import type { User, ModelInfo } from '../types';

interface Props {
  user: User | null;
  sessionId: string;
  onSessionChange: (session: string) => void;
  selectedModel: string;
  onModelChange: (model: string) => void;
  modelsInfo: ModelInfo | null;
  onOpenUpload: () => void;
  onOpenMemory: () => void;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Header: React.FC<Props> = ({
  user,
  sessionId,
  onSessionChange,
  selectedModel,
  onModelChange,
  modelsInfo,
  onOpenUpload,
  onOpenMemory,
  onOpenAuth,
  onLogout,
}) => {
  return (
    <header className="glass-panel" style={{ padding: '12px 24px', margin: '16px 16px 0 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'linear-gradient(135deg, var(--primary), var(--accent-cyan))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '1.1rem', color: '#fff' }}>
          NX
        </div>
        <div>
          <h1 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0, background: 'linear-gradient(135deg, #fff, #cbd5e1)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            AI Nexus RAG Engine
          </h1>
          <span style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
            v0.4.0 • Multimodal & 3-Way Decision Gate
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
        {modelsInfo && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Model:</span>
            <select
              value={selectedModel}
              onChange={(e) => onModelChange(e.target.value)}
              className="input-field"
              style={{ width: 'auto', padding: '6px 10px', fontSize: '0.8rem' }}
            >
              {Object.entries(modelsInfo.models).map(([id, desc]) => (
                <option key={id} value={id}>
                  {id.split('/')[1]} ({desc.split('(')[0].trim()})
                </option>
              ))}
            </select>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Session:</span>
          <input
            type="text"
            className="input-field"
            value={sessionId}
            onChange={(e) => onSessionChange(e.target.value)}
            style={{ width: '120px', padding: '6px 10px', fontSize: '0.8rem' }}
          />
        </div>

        {user && (
          <>
            <button className="btn btn-secondary" onClick={onOpenUpload} style={{ fontSize: '0.8rem', padding: '7px 12px' }}>
              📁 Ingest Files
            </button>
            <button className="btn btn-secondary" onClick={onOpenMemory} style={{ fontSize: '0.8rem', padding: '7px 12px' }}>
              🧠 Memory
            </button>
          </>
        )}

        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', paddingLeft: '8px', borderLeft: '1px solid var(--border-color)' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'var(--accent-purple)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', fontWeight: 700 }}>
              {user.username[0].toUpperCase()}
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}>
              {user.username}
            </span>
            <button className="btn btn-danger" onClick={onLogout} style={{ fontSize: '0.75rem', padding: '4px 8px', marginLeft: '4px' }}>
              Logout
            </button>
          </div>
        ) : (
          <button className="btn btn-primary" onClick={onOpenAuth} style={{ fontSize: '0.85rem', padding: '7px 14px' }}>
            Sign In
          </button>
        )}
      </div>
    </header>
  );
};
