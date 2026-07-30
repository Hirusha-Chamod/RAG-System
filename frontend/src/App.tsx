import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ChatWindow } from './components/ChatWindow';
import { AuthModal } from './components/AuthModal';
import { FileUploadModal } from './components/FileUploadModal';
import { MemoryDrawer } from './components/MemoryDrawer';
import { getModels, sendChatMessage } from './api/client';
import type { User, ModelInfo, ChatMessage } from './types';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('nexus_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [sessionId, setSessionId] = useState<string>('session_default');
  const [modelsInfo, setModelsInfo] = useState<ModelInfo | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>('tencent/hy3:free');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showMemoryDrawer, setShowMemoryDrawer] = useState(false);

  // Load available OpenRouter models at startup
  useEffect(() => {
    getModels()
      .then((data) => {
        setModelsInfo(data);
        setSelectedModel(data.default_model);
      })
      .catch((err) => console.error('Error fetching models:', err));
  }, []);

  const handleLoginSuccess = (userData: User) => {
    setUser(userData);
    localStorage.setItem('nexus_user', JSON.stringify(userData));
    setShowAuthModal(false);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('nexus_user');
    setMessages([]);
  };

  const handleSendMessage = async (text: string) => {
    if (!user) {
      setShowAuthModal(true);
      return;
    }

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setChatLoading(true);

    try {
      const resp = await sendChatMessage(text, sessionId, selectedModel, user.access_token);

      const assistantMsg: ChatMessage = {
        id: `ast_${Date.now()}`,
        sender: 'assistant',
        text: resp.answer,
        sources: resp.sources,
        relevance_action: resp.relevance_action,
        model_used: resp.model_used,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err_${Date.now()}`,
        sender: 'assistant',
        text: `⚠️ Request failed: ${err.message || 'Server error'}`,
        relevance_action: 'fallback',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw' }}>
      <Header
        user={user}
        sessionId={sessionId}
        onSessionChange={setSessionId}
        selectedModel={selectedModel}
        onModelChange={setSelectedModel}
        modelsInfo={modelsInfo}
        onOpenUpload={() => setShowUploadModal(true)}
        onOpenMemory={() => setShowMemoryDrawer(true)}
        onOpenAuth={() => setShowAuthModal(true)}
        onLogout={handleLogout}
      />

      <ChatWindow
        messages={messages}
        onSendMessage={handleSendMessage}
        loading={chatLoading}
        disabled={!user}
      />

      {showAuthModal && (
        <AuthModal
          onLoginSuccess={handleLoginSuccess}
          onClose={() => setShowAuthModal(false)}
        />
      )}

      {showUploadModal && user && (
        <FileUploadModal
          token={user.access_token}
          onClose={() => setShowUploadModal(false)}
          onSuccess={() => {}}
        />
      )}

      {showMemoryDrawer && user && (
        <MemoryDrawer
          token={user.access_token}
          onClose={() => setShowMemoryDrawer(false)}
        />
      )}
    </div>
  );
};

export default App;
