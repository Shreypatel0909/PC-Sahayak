import { useEffect, useRef, useState } from 'react';
import type { Meta } from '../types';
import type { Prefs, ThemePref } from '../lib/prefs';

interface Props {
  meta: Meta;
  prefs: Prefs;
  chatCount: number;
  anchor: React.RefObject<HTMLButtonElement>;
  onPrefs: (patch: Partial<Prefs>) => void;
  onReindex: () => Promise<void>;
  onDeleteAll: () => Promise<void>;
  onClose: () => void;
}

const THEMES: Array<[ThemePref, string]> = [['system', 'Match system'], ['light', 'Light'], ['dark', 'Dark']];

function builtLabel(iso: string | null) {
  if (!iso) return 'Index ready';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? 'Index ready' : `Indexed ${d.toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}`;
}

export function Settings({ meta, prefs, chatCount, anchor, onPrefs, onReindex, onDeleteAll, onClose }: Props) {
  const panel = useRef<HTMLElement>(null);
  const [rebuilding, setRebuilding] = useState(false);
  const [confirmAll, setConfirmAll] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    panel.current?.querySelector<HTMLInputElement>('input:checked')?.focus();
    const onDown = (e: PointerEvent) => {
      const t = e.target as Node;
      if (!panel.current?.contains(t) && !anchor.current?.contains(t)) onClose();
    };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { onClose(); anchor.current?.focus(); } };
    document.addEventListener('pointerdown', onDown);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('pointerdown', onDown); document.removeEventListener('keydown', onKey); };
  }, [anchor, onClose]);

  async function rebuild() {
    setRebuilding(true);
    try { await onReindex(); } finally { setRebuilding(false); }
  }

  async function copy(url: string) {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(url);
    } catch {
      window.prompt('Copy this link:', url);
    }
  }

  async function deleteAll() {
    setDeleting(true);
    try { await onDeleteAll(); } finally { setDeleting(false); setConfirmAll(false); }
  }

  return (
    <section className="settings" id="settings" role="dialog" aria-label="Settings" ref={panel}>
      <h2>Settings</h2>

      {meta.share_urls.length > 0 && (
        <div className="set">
          <span className="eyebrow">Shared on your network</span>
          <small>Open one of these links on a phone or another PC on the same Wi-Fi. Anyone with the link can use PC-Sahayak and see its chats.</small>
          {meta.share_urls.map(url => (
            <div className="share-row" key={url}>
              <code>{url}</code>
              <button className="ghost" type="button" onClick={() => copy(url)}>{copied === url ? 'Copied' : 'Copy'}</button>
            </div>
          ))}
        </div>
      )}

      <div className="set">
        <span className="eyebrow">Theme</span>
        <div className="seg" role="radiogroup" aria-label="Theme">
          {THEMES.map(([value, label]) => (
            <label key={value}>
              <input type="radio" name="theme" value={value} checked={prefs.theme === value} onChange={() => onPrefs({ theme: value })} />
              <span>{label}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="set">
        <span className="eyebrow">Replies</span>
        <div className="set-row">
          <label htmlFor="animToggle"><p>Show replies word by word</p><small>Turn off to show each reply at once.</small></label>
          <input className="switch" type="checkbox" id="animToggle" checked={prefs.animate} onChange={e => onPrefs({ animate: e.target.checked })} />
        </div>
      </div>

      <div className="set">
        <span className="eyebrow">Knowledge base</span>
        <div className="set-row">
          <div>
            <p>{meta.kb.documents} guides · {meta.kb.chunks} sections</p>
            <small>{builtLabel(meta.kb.built_at)}</small>
          </div>
          <button className="ghost" type="button" onClick={rebuild} disabled={rebuilding}>
            {rebuilding ? <><span className="spin" />Rebuilding…</> : 'Rebuild index'}
          </button>
        </div>
        <small>Rebuild after adding or editing guides in the knowledge_base folder.</small>
      </div>

      <div className="set">
        <span className="eyebrow">Assistant</span>
        <div className="set-row">
          <div>
            <p><span className={`status-dot${meta.llm.configured ? '' : ' off'}`} />{meta.llm.configured ? 'Groq API key found' : 'No Groq API key'}</p>
            <small>{meta.llm.text_model} · screenshots: {meta.llm.vision_model}</small>
          </div>
        </div>
        {!meta.llm.configured && <small>Add <code>GROQ_API_KEY</code> to the <code>.env</code> file, then restart the server.</small>}
      </div>

      <div className="set">
        <span className="eyebrow">Your chats</span>
        {confirmAll ? (
          <div className="confirm">
            <p>Delete all {chatCount} saved problems? This can't be undone.</p>
            <div>
              <button className="solid-danger" type="button" disabled={deleting} onClick={deleteAll}>Delete all</button>
              <button className="ghost" type="button" autoFocus onClick={() => setConfirmAll(false)}>Cancel</button>
            </div>
          </div>
        ) : (
          <div className="set-row">
            <div><p>Saved on this computer</p><small>{chatCount ? `${chatCount} saved problem${chatCount === 1 ? '' : 's'}` : 'No saved problems'}</small></div>
            <button className="ghost danger" type="button" disabled={!chatCount} onClick={() => setConfirmAll(true)}>Delete all</button>
          </div>
        )}
      </div>
      <small className="version">PC-Sahayak version {meta.version}</small>
    </section>
  );
}
