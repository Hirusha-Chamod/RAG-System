export interface User {
  user_id: string;
  username: string;
  email: string;
  access_token: string;
}

export interface ModelInfo {
  default_model: string;
  models: Record<string, string>;
}

export interface SourceDoc {
  content: string;
  score: number;
  source: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  sources?: SourceDoc[];
  relevance_action?: 'synthesize' | 'clarify' | 'fallback';
  model_used?: string;
  timestamp: string;
}

export interface IngestFileResult {
  filename: string;
  status: 'success' | 'error';
  chunks_created: number;
  images_processed: number;
  error_message?: string;
}

export interface IngestResponse {
  results: IngestFileResult[];
  total_chunks: number;
  total_images: number;
}

export interface MemoryEntry {
  key: string;
  value: { text: string };
  updated_at: number;
}
