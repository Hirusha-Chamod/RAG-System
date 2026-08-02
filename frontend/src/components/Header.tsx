import React, { useState } from 'react';

interface Props {
  user: any;
  selectedModel: string;
  onModelChange: (model: string) => void;
  modelsInfo: any;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Header: React.FC<Props> = ({
  user,
  selectedModel,
  onModelChange,
  modelsInfo,
  onOpenAuth,
  onLogout,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const availableModels = modelsInfo?.models || {
    'google/gemma-4-31b-it:free': 'Google Gemma 4 31B (Default)',
    'inclusionai/ling-3.0-flash:free': 'Ling 3.0 Flash (Fast)',
    'nvidia/nemotron-3-super-120b-a12b:free': 'Nemotron 3 Super (Long context)',
    'google/gemma-4-26b-a4b-it:free': 'Gemma 4 26B (Lightweight)',
  };

  const currentShortName = selectedModel.split('/')[1] || selectedModel;

  return (
    <header
      className="glass-panel"
      style={{
        margin: '16px 16px 0 0',
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '64px',
        zIndex: 100,
        position: 'relative',
      }}
    >
      {/* Sleek Custom Model Selector Dropdown */}
      <div style={{ position: 'relative' }}>
        <div
          onClick={() => setDropdownOpen(!dropdownOpen)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border-color)',
            padding: '8px 14px',
            borderRadius: '12px',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            userSelect: 'none',
          }}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
            <rect x="9" y="9" width="6" height="6"></rect>
            <line x1="9" y1="1" x2="9" y2="4"></line>
            <line x1="15" y1="1" x2="15" y2="4"></line>
            <line x1="9" y1="20" x2="9" y2="23"></line>
            <line x1="15" y1="20" x2="15" y2="23"></line>
            <line x1="20" y1="9" x2="23" y2="9"></line>
            <line x1="20" y1="15" x2="23" y2="15"></line>
            <line x1="1" y1="9" x2="4" y2="9"></line>
            <line x1="1" y1="15" x2="4" y2="15"></line>
          </svg>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)', fontWeight: 600 }}>Model:</span>
          <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
            {currentShortName}
          </span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--text-dim)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: '4px', transform: dropdownOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s ease' }}>
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </div>

        {/* Dropdown Menu */}
        {dropdownOpen && (
          <div
            className="glass-panel animate-fade-in"
            style={{
              position: 'absolute',
              top: '48px',
              left: 0,
              width: '320px',
              background: '#0f172a',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: '12px',
              boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
              padding: '8px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              zIndex: 200,
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-dim)', padding: '6px 8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Select Active OpenRouter LLM
            </div>
            {Object.entries(availableModels).map(([modelId, desc]) => {
              const isSelected = modelId === selectedModel;
              const shortName = modelId.split('/')[1] || modelId;
              return (
                <div
                  key={modelId}
                  onClick={() => {
                    onModelChange(modelId);
                    setDropdownOpen(false);
                  }}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '8px',
                    background: isSelected ? 'rgba(99, 102, 241, 0.25)' : 'transparent',
                    border: isSelected ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: isSelected ? '#fff' : 'var(--text-main)' }}>
                      {shortName}
                    </span>
                    {isSelected && <span style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', fontWeight: 700 }}>Active</span>}
                  </div>
                  <div style={{ fontSize: '0.73rem', color: 'var(--text-dim)', lineHeight: '1.3' }}>
                    {desc as string}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* User Auth Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {!user ? (
          <button onClick={onOpenAuth} className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '0.85rem' }}>
            Sign In / Register
          </button>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Logged in as <strong style={{ color: '#fff' }}>{user.username}</strong>
            </div>
            <button onClick={onLogout} className="btn btn-secondary" style={{ padding: '6px 14px', fontSize: '0.8rem' }}>
              Sign Out
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
