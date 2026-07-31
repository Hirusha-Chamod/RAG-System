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
            <span style={{ fontSize: '1.4rem' }}>📄</span>
            <div>
              <h3 style={{ margin: 0, color: 'var(--text-main)', fontSize: '1.2rem' }}>My Document Library</h3>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                View and manage your ingested PDF, DOCX, XLSX, TXT & MD knowledge files
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
              <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📂</div>
              <div>No documents uploaded yet</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Click "Ingest Files" in your sidebar to upload PDF, DOCX, XLSX, TXT, or MD files.
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
                  <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.9rem', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                    📄 {doc.source}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                    Indexed parent chunks: <strong style={{ color: 'var(--accent-purple)' }}>{doc.parent_chunks}</strong>
                  </div>
                </div>

                <button
                  onClick={() => setConfirmTarget(doc.source)}
                  disabled={deletingSource === doc.source}
                  className="btn btn-danger"
                  style={{ padding: '6px 12px', fontSize: '0.78rem', borderRadius: '8px' }}
                >
                  {deletingSource === doc.source ? 'Deleting...' : '🗑️ Delete'}
                </button>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
          <button onClick={onClose} className="btn btn-secondary" style={{ padding: '8px 18px', fontSize: '0.85rem' }}>
            Close
          </button>
        </div>

        {/* Custom Confirmation Modal Overlay */}
        {confirmTarget && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(15, 23, 42, 0.92)',
              backdropFilter: 'blur(10px)',
              borderRadius: '16px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              textAlign: 'center',
              zIndex: 1100,
            }}
            className="animate-fade-in"
          >
            <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>⚠️</div>
            <h4 style={{ margin: '0 0 8px 0', fontSize: '1.2rem', color: '#fff' }}>
              Confirm Document Deletion
            </h4>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', maxWidth: '420px', lineHeight: '1.5', margin: '0 0 20px 0' }}>
              Are you sure you want to permanently delete <strong style={{ color: 'var(--accent-cyan)' }}>"{confirmTarget}"</strong> from your knowledge base? All vector embeddings and parent text chunks will be removed.
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
                style={{ padding: '8px 18px', fontSize: '0.85rem', fontWeight: 600 }}
              >
                Yes, Delete Document
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
