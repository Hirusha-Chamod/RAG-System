import React, { useState } from 'react';
import { uploadFiles } from '../api/client';
import type { IngestResponse } from '../types';

interface Props {
  token: string;
  onClose: () => void;
  onSuccess: (res: IngestResponse) => void;
}

export const FileUploadModal: React.FC<Props> = ({ token, onClose, onSuccess }) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await uploadFiles(selectedFiles, token);
      setResult(res);
      onSuccess(res);
    } catch (err: any) {
      setError(err.message || 'Ingestion failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(5, 8, 16, 0.85)',
        backdropFilter: 'blur(8px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1000
      }}
    >
      <div className="glass-panel animate-fade-in" style={{ width: '520px', padding: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700 }}>📁 Multimodal Document Ingestion</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', fontSize: '1.2rem', cursor: 'pointer' }}>
            ✕
          </button>
        </div>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '20px' }}>
          Upload PDF, DOCX, XLSX, TXT, MD, or images. Supports parent-child chunking (~2000 / ~400 chars) and SHA-256 vision caching.
        </p>

        <div
          style={{
            border: '2px dashed var(--border-glow)',
            borderRadius: '12px',
            padding: '32px 20px',
            textAlign: 'center',
            background: 'rgba(15, 23, 42, 0.5)',
            marginBottom: '20px',
          }}
        >
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.xlsx,.txt,.md,.png,.jpg,.jpeg"
            onChange={handleFileChange}
            id="file-upload-input"
            style={{ display: 'none' }}
          />
          <label htmlFor="file-upload-input" style={{ cursor: 'pointer' }}>
            <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📤</div>
            <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
              Click to browse files
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              PDF, DOCX, XLSX, TXT, MD, PNG, JPG
            </div>
          </label>

          {selectedFiles.length > 0 && (
            <div style={{ marginTop: '16px', fontSize: '0.82rem', color: 'var(--accent-cyan)', textAlign: 'left', background: 'rgba(6, 182, 212, 0.1)', padding: '10px 14px', borderRadius: '8px' }}>
              <strong>Selected ({selectedFiles.length}):</strong>
              <ul style={{ marginTop: '4px', paddingLeft: '20px' }}>
                {selectedFiles.map((f, i) => (
                  <li key={i}>{f.name} ({(f.size / 1024).toFixed(1)} KB)</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {error && (
          <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', fontSize: '0.85rem', marginBottom: '16px' }}>
            {error}
          </div>
        )}

        {result && (
          <div style={{ padding: '12px 16px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34d399', fontSize: '0.85rem', marginBottom: '16px' }}>
            <strong>✅ Ingestion Complete!</strong>
            <div>Total Chunks Created: {result.total_chunks}</div>
            <div>Images Described: {result.total_images}</div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
          <button
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={loading || selectedFiles.length === 0}
          >
            {loading ? 'Processing & Vectorizing...' : 'Upload & Ingest'}
          </button>
        </div>
      </div>
    </div>
  );
};
