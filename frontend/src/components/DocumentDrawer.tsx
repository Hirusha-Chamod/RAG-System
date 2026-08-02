import React, { useState, useEffect } from 'react';
import { fetchUserDocuments, deleteUserDocument } from '../api/client';

interface Props {
  token: string;
  onClose: () => void;
}

interface DocEntry {
  source: string;
  parent_chunks: number;
}

export const DocumentDrawer: React.FC<Props> = ({ token, onClose }) => {
  const [documents, setDocuments] = useState<DocEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deletingSource, setDeletingSource] = useState<string | null>(null);

  // Confirmation modal state
  const [confirmTarget, setConfirmTarget] = useState<string | null>(null);

  const loadDocs = () => {
    setLoading(true);
    fetchUserDocuments(token)
      .then((data) => {
        setDocuments(data.documents || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load documents');
        setLoading(false);
      });
  };

  useEffect(() => {
    loadDocs();
  }, [token]);

  const confirmDelete = async () => {
    if (!confirmTarget) return;
    const source = confirmTarget;
    setConfirmTarget(null);
    setDeletingSource(source);

    try {
      await deleteUserDocument(source, token);
      loadDocs();
    } catch (err: any) {
      setError(`Delete failed: ${err.message}`);
    } finally {
      setDeletingSource(null);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
    >
      <div
        className="glass-panel animate-fade-in"
        style={{
          width: '560px',
          maxHeight: '80vh',
          display: 'flex',
          flexDirection: 'column',
          padding: '24px',
          borderRadius: '16px',
          position: 'relative',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.15)', border: '1px solid rgba(99, 102, 241, 0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
            </div>
            <div>
              <h3 style={{ margin: 0, color: 'var(--text-main)', fontSize: '1.15rem', fontWeight: 700 }}>Document Library</h3>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                View and manage your knowledge files
              </div>
            </div>
          </div>
          <button onClick={onClose} className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.85rem' }}>
            ✕
          </button>
        </div>

        {/* Content Area */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px', paddingRight: '4px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '24px' }}>
              Loading document library...
            </div>
          ) : error ? (
            <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', padding: '12px' }}>
              {error}
            </div>
          ) : documents.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '36px 12px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-dim)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                </svg>
              </div>
              <div>No documents uploaded yet</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Click "Upload Files" in your sidebar to add PDF, DOCX, XLSX, TXT, or MD files.
              </div>
            </div>
          ) : (
            documents.map((doc, idx) => (
              <div
                key={idx}
                style={{
                  padding: '12px 16px',
                  borderRadius: '10px',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div style={{ flex: 1, overflow: 'hidden', paddingRight: '12px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.88rem', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{doc.source}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }}></span>
                    <span>Ready for search</span>
                  </div>
                </div>

                <button
                  onClick={() => setConfirmTarget(doc.source)}
                  disabled={deletingSource === doc.source}
                  className="btn btn-danger"
                  style={{ padding: '6px 12px', fontSize: '0.78rem', borderRadius: '8px', gap: '6px' }}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                  {deletingSource === doc.source ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            ))
          )}
        </div>

        {/* Delete Confirmation Modal Overlay */}
        {confirmTarget && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(5, 8, 16, 0.9)',
              backdropFilter: 'blur(4px)',
              borderRadius: '16px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '32px',
              textAlign: 'center',
              zIndex: 1100,
            }}
          >
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--accent-red)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
              </svg>
            </div>
            <h4 style={{ color: 'var(--text-main)', margin: '0 0 8px 0', fontSize: '1.1rem' }}>
              Delete Document?
            </h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0 0 20px 0', maxWidth: '380px', lineHeight: '1.4' }}>
              Are you sure you want to delete <strong style={{ color: '#fff' }}>"{confirmTarget}"</strong>? This will remove all parent context and vector search chunks.
            </p>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setConfirmTarget(null)}
                className="btn btn-secondary"
                style={{ padding: '8px 18px', fontSize: '0.85rem' }}
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="btn btn-danger"
                style={{ padding: '8px 18px', fontSize: '0.85rem' }}
              >
                Confirm Delete
              </button>
            </div>
          </div>
        )}

        {/* Footer */}
        <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
          <button onClick={onClose} className="btn btn-secondary" style={{ padding: '8px 18px', fontSize: '0.85rem' }}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
