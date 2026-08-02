import type { IngestResponse, MemoryEntry, ModelInfo } from '../types';

const API_BASE = 'http://localhost:8000';

export async function login(username_or_email: string, password: string) {
  const resp = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username_or_email, password }),
  });
  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.detail || 'Login failed');
  }
  return resp.json();
}

export async function signup(username: string, email: string, password: string) {
  const resp = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  });
  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.detail || 'Signup failed');
  }
  return resp.json();
}

export async function getModels(): Promise<ModelInfo> {
  const resp = await fetch(`${API_BASE}/models`);
  if (!resp.ok) throw new Error('Failed to fetch models');
  return resp.json();
}

export async function uploadFiles(files: FileList | File[], token: string): Promise<IngestResponse> {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  const resp = await fetch(`${API_BASE}/ingest`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.detail || 'Ingestion failed');
  }
  return resp.json();
}

export async function fetchUserDocuments(token: string) {
  const resp = await fetch(`${API_BASE}/ingest/documents`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to fetch documents');
  return resp.json();
}

export async function deleteUserDocument(source: string, token: string) {
  const resp = await fetch(`${API_BASE}/ingest/documents?source=${encodeURIComponent(source)}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to delete document');
  return resp.json();
}

export async function sendChatMessage(
  message: string,
  sessionId: string,
  model: string,
  token: string
) {
  const resp = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      model,
    }),
  });
  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.detail || 'Chat request failed');
  }
  return resp.json();
}

export async function sendChatMessageStream(
  message: string,
  sessionId: string,
  model: string,
  token: string,
  onToken: (text: string) => void,
  onComplete: (metadata: any) => void
) {
  const resp = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      model,
    }),
  });

  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.detail || 'Chat streaming request failed');
  }

  const reader = resp.body?.getReader();
  if (!reader) throw new Error('Failed to readable stream reader');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const jsonStr = line.slice(6).trim();
        if (!jsonStr) continue;
        try {
          const payload = JSON.parse(jsonStr);
          if (payload.token) {
            onToken(payload.token);
          } else if (payload.type === 'metadata') {
            onComplete(payload);
          }
        } catch {
          // pass on partial parse errors
        }
      }
    }
  }

  if (buffer.startsWith('data: ')) {
    const jsonStr = buffer.slice(6).trim();
    if (jsonStr) {
      try {
        const payload = JSON.parse(jsonStr);
        if (payload.token) onToken(payload.token);
        else if (payload.type === 'metadata') onComplete(payload);
      } catch {}
    }
  }
}

export async function fetchChatHistory(sessionId: string, token: string) {
  const resp = await fetch(`${API_BASE}/chat/history?session_id=${encodeURIComponent(sessionId)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to fetch chat history');
  return resp.json();
}

export async function fetchUserSessions(token: string) {
  const resp = await fetch(`${API_BASE}/chat/sessions`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to fetch user sessions');
  return resp.json();
}

export async function deleteSession(sessionId: string, token: string) {
  const resp = await fetch(`${API_BASE}/chat/sessions?session_id=${encodeURIComponent(sessionId)}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to delete session');
  return resp.json();
}

export async function fetchMemories(token: string): Promise<{ user_id: string; memories: MemoryEntry[] }> {
  const resp = await fetch(`${API_BASE}/memory`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to fetch long-term memories');
  return resp.json();
}

export async function addMemory(key: string, value: string, token: string) {
  const resp = await fetch(`${API_BASE}/memory`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ key, value }),
  });
  if (!resp.ok) throw new Error('Failed to save memory');
  return resp.json();
}

export async function deleteMemory(token: string, key?: string) {
  const url = key ? `${API_BASE}/memory?key=${encodeURIComponent(key)}` : `${API_BASE}/memory`;
  const resp = await fetch(url, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to delete memory');
  return resp.json();
}
