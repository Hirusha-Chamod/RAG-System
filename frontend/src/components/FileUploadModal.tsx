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
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadStep, setUploadStep] = useState<string>('');
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setUploadStep('Uploading & parsing files...');

    try {
      setUploadStep('Extracting images & text chunking...');
      const res = await uploadFiles(selectedFiles, token);
      setResult(res);
      onSuccess(res);
    } catch (err: any) {
      setError(err.message || 'Ingestion failed');
    } finally {
      setLoading(false);
      setUploadStep('');
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>Upload Documents</h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', fontSize: '1.2rem', cursor: 'pointer' }}>
            ✕
          </button>
        </div>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '20px' }}>
          Upload your files — they'll be processed and made searchable by AI. Supports PDF, DOCX, XLSX, TXT, MD, and images.
        </p>

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${isDragging ? 'var(--accent-cyan)' : 'var(--border-glow)'}`,
            borderRadius: '12px',
            padding: '32px 20px',
            textAlign: 'center',
            background: isDragging ? 'rgba(6, 182, 212, 0.15)' : 'rgba(15, 23, 42, 0.5)',
            marginBottom: '20px',
            transition: 'all 0.2s ease',
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
            <div style={{ width: '44px', height: '44px', borderRadius: '50%', background: 'rgba(99, 102, 241, 0.15)', border: '1px solid rgba(99, 102, 241, 0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
            </div>
            <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px', fontSize: '0.9rem' }}>
              {isDragging ? 'Drop files here' : 'Drag & drop files here or click to browse'}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              PDF, DOCX, XLSX, TXT, MD, PNG, JPG (Max 50MB)
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

        {uploadStep && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: 'var(--accent-cyan)', fontSize: '0.82rem' }}>
            <div className="pulse-glow" style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-cyan)' }} />
            <span>{uploadStep}</span>
          </div>
        )}

        {error && (
          <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', fontSize: '0.85rem', marginBottom: '16px' }}>
            {error}
          </div>
        )}

        {result && (
          <div style={{ padding: '12px 16px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34d399', fontSize: '0.85rem', marginBottom: '16px' }}>
            <strong>Ingestion Complete</strong>
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
            {loading ? 'Processing...' : 'Upload & Process'}
          </button>
        </div>
      </div>
    </div>
  );
};
