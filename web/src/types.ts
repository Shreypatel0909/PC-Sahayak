// Shapes returned by the Python API (api/main.py).

export type Category = 'network' | 'performance' | 'hardware' | 'software' | 'boot' | 'security' | 'other';

export const CATEGORY_NAMES: Record<Category, string> = {
  network: 'Network',
  performance: 'Performance',
  hardware: 'Hardware',
  software: 'Software',
  boot: 'Startup',
  security: 'Security',
  other: 'General',
};

export interface Source {
  file: string;
  heading: string | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  kind: 'normal' | 'error';
  timestamp: number;
  image_url: string | null;
  sources: Source[];
  suggestions: string[];
  tag: 'off_topic' | 'summary' | null;
}

export interface Specs {
  device_type: string | null;
  os: string | null;
  os_version: string | null;
  ram_size: string | null;
  ram_type: string | null;
  storage_size: string | null;
  storage_type: string | null;
}

export interface Route {
  origin: string;
  done: string[];
  current: string | null;
  fixed: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  status: string;
  category: Category;
  locked: boolean;
  created_at: number;
  updated_at: number;
  specs: Specs | null;
  route: Route;
  messages: ChatMessage[];
  sources: Source[];
}

export interface ConversationSummary {
  id: string;
  title: string;
  status: string;
  category: Category;
  updated_at: number;
  steps: number;
}

export interface KbInfo {
  documents: number;
  chunks: number;
  embedder: string;
  built_at: string | null;
}

export interface Meta {
  name: string;
  starter_suggestions: string[];
  options: {
    device_types: string[];
    os: string[];
    ram_sizes: string[];
    ram_types: string[];
    storage_sizes: string[];
    storage_types: string[];
  };
  llm: { configured: boolean; text_model: string; vision_model: string; rag: boolean };
  kb: KbInfo;
  last_specs: Specs | null;
  version: string;
  share_urls: string[];
}
