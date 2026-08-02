import React, { useState, useEffect } from 'react';
import { Sidebar, type SessionItem } from './components/Sidebar';
import { Header } from './components/Header';
import { ChatWindow } from './components/ChatWindow';
import { AuthModal } from './components/AuthModal';
import { FileUploadModal } from './components/FileUploadModal';
import { MemoryDrawer } from './components/MemoryDrawer';
import { DocumentDrawer } from './components/DocumentDrawer';
import { ToastContainer, type ToastMessage } from './components/Toast';
import { getModels, sendChatMessageStream, fetchChatHistory, fetchUserSessions, deleteSession } from './api/client';
import type { User, ModelInfo, ChatMessage } from './types';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('nexus_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [sessionId, setSessionId] = useState<string>('session_default');
  const [sessions, setSessions] = useState<(string | SessionItem)[]>([
    { session_id: 'session_default', title: 'General Chat' }
  ]);
  const [modelsInfo, setModelsInfo] = useState<ModelInfo | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>('google/gemma-4-31b-it:free');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDocumentsModal, setShowDocumentsModal] = useState(false);
  const [showMemoryDrawer, setShowMemoryDrawer] = useState(false);

  const showToast = (text: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = `toast_${Date.now()}_${Math.random()}`;
    setToasts((prev) => [...prev, { id, text, type }]);
  };

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

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
      setSessions([{ session_id: 'session_default', title: 'General Chat' }]);
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
    const newSessItem: SessionItem = { session_id: newSessId, title: 'New Conversation' };
    setSessions((prev) => [newSessItem, ...prev]);
    setSessionId(newSessId);
    setMessages([]);
  };

  const handleDeleteSession = async (sessIdToDelete: string) => {
    if (!user || !user.access_token) return;
    try {
      await deleteSession(sessIdToDelete, user.access_token);
      setSessions((prev) => prev.filter((s) => (typeof s === 'string' ? s : s.session_id) !== sessIdToDelete));
      if (sessionId === sessIdToDelete) {
        setSessionId('session_default');
      }
      showToast('Chat conversation deleted', 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to delete session', 'error');
    }
  };

  const handleLoginSuccess = (userData: User) => {
    setUser(userData);
    localStorage.setItem('nexus_user', JSON.stringify(userData));
    setShowAuthModal(false);
    showToast(`Welcome back, ${userData.username}!`, 'success');
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('nexus_user');
    setMessages([]);
    setSessions([{ session_id: 'session_default', title: 'General Chat' }]);
    setSessionId('session_default');
    showToast('Logged out successfully', 'info');
  };

  const handleSendMessage = async (text: string) => {
    if (!user) {
      setShowAuthModal(true);
      return;
    }

    const cleanPrompt = text.trim();
    const promptTitle = cleanPrompt.slice(0, 26) + (cleanPrompt.length > 26 ? '...' : '');

    // Dynamically update active session title to user prompt preview
    setSessions((prev) => {
      const exists = prev.some((s) => (typeof s === 'string' ? s : s.session_id) === sessionId);
      if (!exists) {
        return [{ session_id: sessionId, title: promptTitle }, ...prev];
      }
      return prev.map((s) => {
        const id = typeof s === 'string' ? s : s.session_id;
        if (id === sessionId) {
          const currentTitle = typeof s === 'string' ? s : s.title;
          if (currentTitle === 'New Conversation' || currentTitle.startsWith('Session')) {
            return { session_id: id, title: promptTitle };
          }
        }
        return s;
      });
    });

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      sender: 'user',
      text,
      timestamp,
    };

    const assistantMsgId = `ast_${Date.now()}`;
    const initialAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      sender: 'assistant',
      text: '',
      timestamp,
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setChatLoading(true);

    try {
      await sendChatMessageStream(
        text,
        sessionId,
        selectedModel,
        user.access_token,
        (token: string) => {
          setChatLoading(false);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? { ...msg, text: msg.text + token }
                : msg
            )
          );
        },
        (metadata: any) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    sources: metadata.sources,
                    relevance_action: metadata.relevance_action,
                    model_used: metadata.model_used,
                  }
                : msg
            )
          );
        }
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                text: `⚠️ Request failed: ${err.message || 'Server error'}`,
                relevance_action: 'fallback',
              }
            : msg
        )
      );
      showToast(err.message || 'Stream error', 'error');
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* Toast Notification Container */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* ChatGPT Style Left Sidebar */}
      <Sidebar
        user={user}
        sessions={sessions}
        activeSession={sessionId}
        onSelectSession={setSessionId}
        onDeleteSession={handleDeleteSession}
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
          onSuccess={() => showToast('Files uploaded & processed successfully', 'success')}
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
