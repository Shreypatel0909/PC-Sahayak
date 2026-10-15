import { useState } from 'react';
import { CATEGORY_NAMES, type ConversationSummary } from '../types';
import { clip, when } from '../lib/format';
import { Close, Trash } from './icons';

interface Props {
  chats: ConversationSummary[];
  activeId: string | null;
  open: boolean;
  onOpen: (id: string) => void;
  onDelete: (id: string) => Promise<void>;
  onClose: () => void;
}

function progress(c: ConversationSummary) {
  if (c.status === 'resolved') return 'Fixed';
  return c.steps ? `Step ${c.steps}` : 'Just started';
}

export function Sidebar({ chats, activeId, open, onOpen, onDelete, onClose }: Props) {
  const [confirming, setConfirming] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function remove(id: string) {
    setBusy(true);
    try { await onDelete(id); } finally { setBusy(false); setConfirming(null); }
  }

  return (
    <nav className={`pane routes${open ? ' open' : ''}`} id="routes" aria-label="Past problems">
      <div className="routes-head">
        <span className="eyebrow">Your problems</span>
        <button className="x" type="button" onClick={onClose} aria-label="Close"><Close /></button>
      </div>
      <div className="route-list">
        {chats.length === 0 && <p className="empty-list">No saved problems yet. Describe one to get started.</p>}
        {chats.map(c => confirming === c.id ? (
          <div className="confirm" role="group" aria-label="Confirm delete" key={c.id}>
            <p>Delete <b>{clip(c.title, 40)}</b> permanently?</p>
            <div>
              <button className="solid-danger" type="button" disabled={busy} onClick={() => remove(c.id)}>Delete</button>
              <button className="ghost" type="button" autoFocus onClick={() => setConfirming(null)}>Cancel</button>
            </div>
          </div>
        ) : (
          <div className="route-row" key={c.id}>
            <button
              className="route-item" type="button" onClick={() => onOpen(c.id)}
              aria-current={c.id === activeId} style={{ '--c': `var(--l-${c.category})` } as React.CSSProperties}
            >
              <i className={`pip${c.status === 'resolved' ? ' fixed' : ''}`} />
              <b>{c.title}</b>
              <small>{CATEGORY_NAMES[c.category]} · {progress(c)} · {when(c.updated_at)}</small>
            </button>
            <button className="del" type="button" onClick={() => setConfirming(c.id)} aria-label={`Delete ${c.title}`}>
              <Trash />
            </button>
          </div>
        ))}
      </div>
      <p className="local-note">Chats are saved on this computer only.</p>
    </nav>
  );
}
