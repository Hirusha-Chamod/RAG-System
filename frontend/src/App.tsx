import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { ChatWindow } from './components/ChatWindow';
import { AuthModal } from './components/AuthModal';
import { FileUploadModal } from './components/FileUploadModal';
import { MemoryDrawer } from './components/MemoryDrawer';
import { DocumentDrawer } from './components/DocumentDrawer';
import { getModels, sendChatMessage, fetchChatHistory, fetchUserSessions } from './api/client';
import type { User, ModelInfo, ChatMessage } from './types';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('nexus_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [sessionId, setSessionId] = useState<string>('session_default');
  const [sessions, setSessions] = useState<string[]>(['session_default']);
  const [modelsInfo, setModelsInfo] = useState<ModelInfo | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>('google/gemma-4-31b-it:free');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDocumentsModal, setShowDocumentsModal] = useState(false);
  const [showMemoryDrawer, setShowMemoryDrawer] = useState(false);

  // Load available models at startup
  useEffect(() => {
    getModels()
      .then((data) => {
        setModelsInfo(data);
        setSelectedModel(data.default_model);
      })
      .catch((err) => console.error('Error fetching models:', err));
  }, []);

  // Fetch list of user sessions when user changes
  useEffect(() => {
    if (user && user.access_token) {
      fetchUserSessions(user.access_token)
        .then((data) => {
          if (data && data.sessions) {
            setSessions(data.sessions);
          }
        })
        .catch((err) => console.error('Failed to fetch user sessions:', err));
    } else {
      setSessions(['session_default']);
    }
  }, [user]);

  // Fetch persisted chat history whenever user or sessionId changes
  useEffect(() => {
    if (user && user.access_token) {
      fetchChatHistory(sessionId, user.access_token)
        .then((data) => {
          if (data && data.messages) {
            setMessages(data.messages);
          }
        })
        .catch((err) => console.error('Failed to load chat history:', err));
    } else {
      setMessages([]);
    }
  }, [user, sessionId]);

  const handleNewChat = () => {
    const newSessId = `session_${Date.now().toString().slice(-6)}`;
    setSessions((prev) => [newSessId, ...prev]);
    setSessionId(newSessId);
    setMessages([]);
  };

  const handleLoginSuccess = (userData: User) => {
    setUser(userData);
    localStorage.setItem('nexus_user', JSON.stringify(userData));
    setShowAuthModal(false);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('nexus_user');
    setMessages([]);
    setSessions(['session_default']);
    setSessionId('session_default');
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

      // Ensure active session is present in sidebar list
      if (!sessions.includes(sessionId)) {
        setSessions((prev) => [sessionId, ...prev]);
      }
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
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* ChatGPT Style Left Sidebar */}
      <Sidebar
        user={user}
        sessions={sessions}
        activeSession={sessionId}
        onSelectSession={setSessionId}
        onNewChat={handleNewChat}
        onOpenUpload={() => setShowUploadModal(true)}
        onOpenDocuments={() => setShowDocumentsModal(true)}
        onOpenMemory={() => setShowMemoryDrawer(true)}
      />

      {/* Main Chat Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
        <Header
          user={user}
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
          modelsInfo={modelsInfo}
          onOpenAuth={() => setShowAuthModal(true)}
          onLogout={handleLogout}
        />

        <ChatWindow
          messages={messages}
          onSendMessage={handleSendMessage}
          loading={chatLoading}
          disabled={!user}
        />
      </div>

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

      {showDocumentsModal && user && (
        <DocumentDrawer
          token={user.access_token}
          onClose={() => setShowDocumentsModal(false)}
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
