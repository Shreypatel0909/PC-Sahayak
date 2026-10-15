import type { Conversation, ConversationSummary, KbInfo, Meta, Specs } from './types';

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, init);
  } catch {
    throw new ApiError("Can't reach the PC Helper server. Check that it's running, then try again.");
  }
  if (!res.ok) {
    let detail = `The server returned an error (${res.status}).`;
    try {
      const body = await res.json();
      if (typeof body?.detail === 'string') detail = body.detail;
    } catch { /* not JSON */ }
    throw new ApiError(detail);
  }
  return res.json() as Promise<T>;
}

function form(fields: Record<string, string>, image?: File | null): FormData {
  const data = new FormData();
  for (const [k, v] of Object.entries(fields)) data.append(k, v);
  if (image) data.append('image', image, image.name || 'screenshot.png');
  return data;
}

export const api = {
  meta: () => request<Meta>('/api/meta'),
  list: () => request<ConversationSummary[]>('/api/conversations'),
  get: (id: string) => request<Conversation>(`/api/conversations/${encodeURIComponent(id)}`),
  start: (specs: Specs, issue: string, image?: File | null) =>
    request<Conversation>('/api/conversations', {
      method: 'POST',
      body: form({ specs: JSON.stringify(specs), issue }, image),
    }),
  send: (id: string, text: string, image?: File | null) =>
    request<Conversation>(`/api/conversations/${encodeURIComponent(id)}/messages`, {
      method: 'POST',
      body: form({ text }, image),
    }),
  resolve: (id: string) =>
    request<Conversation>(`/api/conversations/${encodeURIComponent(id)}/resolve`, { method: 'POST' }),
  unlock: (id: string) =>
    request<Conversation>(`/api/conversations/${encodeURIComponent(id)}/unlock`, { method: 'POST' }),
  retry: (id: string) =>
    request<Conversation>(`/api/conversations/${encodeURIComponent(id)}/retry`, { method: 'POST' }),
  remove: (id: string) =>
    request<{ deleted: number }>(`/api/conversations/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  removeAll: () => request<{ deleted: number }>('/api/conversations', { method: 'DELETE' }),
  reindex: () =>
    request<{ documents: number; chunks: number; kb: KbInfo }>('/api/reindex', { method: 'POST' }),
};
