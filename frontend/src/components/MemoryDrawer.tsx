import React, { useState, useEffect } from 'react';
import { fetchMemories, addMemory, deleteMemory } from '../api/client';
import type { MemoryEntry } from '../types';

interface Props {
  token: string;
  onClose: () => void;
}

export const MemoryDrawer: React.FC<Props> = ({ token, onClose }) => {
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMemories = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMemories(token);
      setMemories(data.memories);
    } catch (err: any) {
      setError(err.message || 'Failed to load memory');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMemories();
  }, [token]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newValue.trim()) return;

    try {
      await addMemory(newKey, newValue, token);
      setNewKey('');
      setNewValue('');
      loadMemories();
    } catch (err: any) {
      setError(err.message || 'Failed to add memory');
    }
  };

  const handleDelete = async (key?: string) => {
    try {
      await deleteMemory(token, key);
      loadMemories();
    } catch (err: any) {
      setError(err.message || 'Failed to delete memory');
    }
  };

  return (
    <div
      style={{
        position: 'fixed', top: 0, right: 0, bottom: 0, width: '420px',
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        backdropFilter: 'blur(16px)',
        borderLeft: '1px solid var(--border-color)',
        boxShadow: '-8px 0 32px rgba(0,0,0,0.5)',
        display: 'flex', flexDirection: 'column',
        zIndex: 1000,
        padding: '24px',
      }}
      className="animate-fade-in"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '34px', height: '34px', borderRadius: '8px', background: 'rgba(139, 92, 246, 0.15)', border: '1px solid rgba(139, 92, 246, 0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-purple)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"></path>
              <circle cx="12" cy="12" r="3"></circle>
            </svg>
          </div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-main)' }}>Long-Term User Memory</h2>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', fontSize: '1.2rem', cursor: 'pointer' }}>
          ✕
        </button>
      </div>

      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '20px' }}>
        User background, facts, and preferences stored across all chat sessions.
      </p>

      {error && (
        <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', fontSize: '0.85rem', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleAdd} style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px', background: 'rgba(255, 255, 255, 0.03)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
        <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--accent-purple)' }}>+ Add New User Fact / Preference</div>
        <input
          type="text"
          className="input-field"
          placeholder="Key (e.g. role, preferences, tech_stack)"
          value={newKey}
          onChange={(e) => setNewKey(e.target.value)}
          required
        />
        <input
          type="text"
          className="input-field"
          placeholder="Value (e.g. Corporate Lawyer, concise tone)"
          value={newValue}
          onChange={(e) => setNewValue(e.target.value)}
          required
        />
        <button type="submit" className="btn btn-primary" style={{ padding: '8px 12px', fontSize: '0.85rem' }}>
          Save Memory Entry
        </button>
      </form>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            Stored Memories ({memories.length})
          </span>
          {memories.length > 0 && (
            <button onClick={() => handleDelete()} style={{ background: 'none', border: 'none', color: '#fca5a5', fontSize: '0.75rem', cursor: 'pointer' }}>
              Clear All
            </button>
          )}
        </div>

        {loading ? (
          <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>Loading memories...</div>
        ) : memories.length === 0 ? (
          <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem', fontStyle: 'italic', padding: '16px 0' }}>
            No long-term memories stored yet. Add one above or chat for 5+ turns!
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {memories.map((m) => (
              <div
                key={m.key}
                style={{
                  padding: '12px',
                  borderRadius: '10px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: '8px',
                }}
              >
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
                    {m.key}
                  </div>
                  <div style={{ fontSize: '0.88rem', color: 'var(--text-main)', marginTop: '2px' }}>
                    {m.value.text}
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(m.key)}
                  style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', fontSize: '0.9rem' }}
                  title="Delete key"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
