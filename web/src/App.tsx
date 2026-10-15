import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from './api';
import type { Conversation, ConversationSummary, Meta, Specs } from './types';
import { usePrefs } from './lib/prefs';
import { Sidebar } from './components/Sidebar';
import { Settings } from './components/Settings';
import { Intake } from './components/Intake';
import { Thread, type Pending } from './components/Thread';
import { Composer } from './components/Composer';
import { RoutePanel, RouteStrip } from './components/RoutePanel';
import { CloseConfirm } from './components/CloseConfirm';
import { Gear, Logo, Menu, Moon, Plus, Power, Sun } from './components/icons';

const idFromHash = () => decodeURIComponent(window.location.hash.slice(1)) || null;
const errorText = (e: unknown) => (e instanceof Error ? e.message : 'Something went wrong. Please try again.');

/** Index of the newest normal assistant reply at or after `from` (the one to animate). */
function newReply(c: Conversation, from: number): number | null {
  for (let i = c.messages.length - 1; i >= from; i--) {
    const m = c.messages[i];
    if (m.role === 'assistant' && m.kind === 'normal') return i;
  }
  return null;
}

function makeTitle(text: string) {
  const line = text.split(/\s+/).join(' ').trim();
  return line.length <= 60 ? line : line.slice(0, 57).trimEnd() + '…';
}

export function App() {
  const { prefs, update, isDark } = usePrefs();
  const [meta, setMeta] = useState<Meta | null>(null);
  const [bootError, setBootError] = useState<string | null>(null);
  const [bootTry, setBootTry] = useState(0);
  const [chats, setChats] = useState<ConversationSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(idFromHash);
  const [conv, setConv] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(false);
  // A turn in flight: which chat it belongs to ('new' while a chat is being started).
  const [pending, setPending] = useState<(Pending & { chat: string }) | null>(null);
  const [startTitle, setStartTitle] = useState<string | null>(null);
  const [freshFrom, setFreshFrom] = useState(Infinity);
  const [revealIdx, setRevealIdx] = useState<number | null>(null);
  const [intakeKey, setIntakeKey] = useState(0);
  const [drawer, setDrawer] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [closeOpen, setCloseOpen] = useState(false);
  const [closed, setClosed] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const gear = useRef<HTMLButtonElement>(null);
  const power = useRef<HTMLButtonElement>(null);
  const activeRef = useRef(activeId);
  activeRef.current = activeId;

  const say = useCallback((msg: string) => setToast(msg), []);
  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(() => setToast(null), 3200);
    return () => window.clearTimeout(t);
  }, [toast]);

  const refreshList = useCallback(() => api.list().then(setChats).catch(() => { /* keep the old list */ }), []);

  // Boot: options, models, knowledge-base info, and the saved chats.
  useEffect(() => {
    setBootError(null);
    Promise.all([api.meta(), api.list()])
      .then(([m, list]) => { setMeta(m); setChats(list); })
      .catch(e => setBootError(errorText(e)));
  }, [bootTry]);

  // Load the selected chat (skipped when we already hold it, e.g. right after starting it).
  useEffect(() => {
    if (!activeId) { setConv(null); return; }
    if (conv?.id === activeId) return;
    let cancelled = false;
    setLoading(true);
    api.get(activeId)
      .then(c => { if (!cancelled) { setConv(c); setFreshFrom(Infinity); setRevealIdx(null); } })
      .catch(e => { if (!cancelled) { say(errorText(e)); setActiveId(null); } })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeId]);

  // Keep #<chat id> in the address bar so a refresh or bookmark reopens the chat.
  useEffect(() => {
    const want = activeId ? '#' + encodeURIComponent(activeId) : '';
    if (window.location.hash !== want) {
      history.replaceState(null, '', want || window.location.pathname + window.location.search);
    }
  }, [activeId]);
  useEffect(() => {
    const onHash = () => setActiveId(idFromHash());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const shown = conv && conv.id === activeId ? conv : null;

  // The route colour follows the problem type the assistant assigned.
  useEffect(() => {
    document.documentElement.style.setProperty('--line', `var(--l-${shown?.category ?? 'other'})`);
  }, [shown?.category]);

  const title = startTitle ?? shown?.title ?? (activeId ? 'Loading…' : 'New problem');
  useEffect(() => { document.title = `${title} · PC-Sahayak`; }, [title]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setDrawer(false); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  function newProblem() {
    setActiveId(null);
    setConv(null);
    setIntakeKey(k => k + 1);
    setDrawer(false);
  }

  function openChat(id: string) {
    setDrawer(false);
    if (id === activeId) return;
    setConv(null);
    setActiveId(id);
  }

  async function start(specs: Specs, issue: string, image: File | null) {
    if (pending) return;
    const imageUrl = image ? URL.createObjectURL(image) : null;
    setStartTitle(issue ? makeTitle(issue) : 'Screenshot troubleshooting');
    setPending({ chat: 'new', text: issue, imageUrl });
    try {
      const c = await api.start(specs, issue, image);
      setFreshFrom(1);
      setConv(c);
      setActiveId(c.id);
      setRevealIdx(newReply(c, 0));
      setMeta(m => (m ? { ...m, last_specs: specs } : m));
      refreshList();
    } catch (e) {
      say(errorText(e));
    } finally {
      setPending(null);
      setStartTitle(null);
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    }
  }

  async function send(text: string, image: File | null): Promise<boolean> {
    if (!shown || pending) return false;
    const id = shown.id;
    const before = shown.messages.length;
    const imageUrl = image ? URL.createObjectURL(image) : null;
    setPending({ chat: id, text, imageUrl });
    try {
      const c = await api.send(id, text, image);
      if (activeRef.current === id) {
        setFreshFrom(before + 1);
        setConv(c);
        setRevealIdx(newReply(c, before));
      }
      refreshList();
      return true;
    } catch (e) {
      say(errorText(e));
      return false;
    } finally {
      setPending(null);
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    }
  }

  async function resolve() {
    if (!shown || pending) return;
    const id = shown.id;
    const before = shown.messages.length;
    setPending({ chat: id, text: 'This solved my problem.', imageUrl: null });
    try {
      const c = await api.resolve(id);
      if (activeRef.current === id) {
        setFreshFrom(before + 1);
        setConv(c);
        setRevealIdx(newReply(c, before));
      }
      refreshList();
    } catch (e) {
      say(errorText(e));
    } finally {
      setPending(null);
    }
  }

  async function unlock() {
    if (!shown) return;
    try {
      const c = await api.unlock(shown.id);
      setFreshFrom(Infinity);
      setRevealIdx(null);
      setConv(c);
    } catch (e) {
      say(errorText(e));
    }
  }

  async function retry() {
    if (!shown || pending) return;
    const id = shown.id;
    const at = shown.messages.length - 1;
    setPending({ chat: id, text: '', imageUrl: null, retry: true });
    try {
      const c = await api.retry(id);
      if (activeRef.current === id) {
        setFreshFrom(at);
        setConv(c);
        setRevealIdx(newReply(c, at));
      }
      refreshList();
    } catch (e) {
      say(errorText(e));
    } finally {
      setPending(null);
    }
  }

  async function remove(id: string) {
    try {
      await api.remove(id);
      say('Chat deleted');
    } catch (e) {
      say(errorText(e));
    }
    await refreshList();
    if (id === activeRef.current) newProblem();
  }

  async function removeAll() {
    try {
      const r = await api.removeAll();
      setChats([]);
      newProblem();
      say(r.deleted === 1 ? '1 chat deleted' : `${r.deleted} chats deleted`);
    } catch (e) {
      say(errorText(e));
    }
  }

  async function reindex() {
    try {
      const r = await api.reindex();
      setMeta(m => (m ? { ...m, kb: r.kb } : m));
      say(`Knowledge base rebuilt: ${r.documents} guides, ${r.chunks} sections`);
    } catch (e) {
      say(errorText(e));
    }
  }

  const closeSettings = useCallback(() => setSettingsOpen(false), []);
  const cancelClose = useCallback(() => setCloseOpen(false), []);

  async function closeApp() {
    try {
      await api.shutdown();
      setCloseOpen(false);
      setClosed(true);
      window.close(); // only works if the browser allows it; otherwise the closed screen stays
    } catch (e) {
      say(errorText(e));
    }
  }

  if (closed) {
    return (
      <div className="app">
        <div className="loading" role="status">
          <div className="closed-screen">
            <Logo />
            <h1>PC-Sahayak is closed</h1>
            <p>It has stopped running on this computer and your chats are saved. You can close this tab.</p>
            <p className="muted">To use it again, double-click <b>Start PC-Sahayak</b>.</p>
          </div>
        </div>
      </div>
    );
  }

  if (bootError || !meta) {
    return (
      <div className="app">
        <div className="loading" role={bootError ? 'alert' : 'status'}>
          {bootError ? (
            <div style={{ textAlign: 'center', maxWidth: 420, display: 'grid', gap: 12, justifyItems: 'center' }}>
              <p style={{ margin: 0 }}>{bootError}</p>
              <p style={{ margin: 0, fontSize: 14 }}>Start it from the pc-helper folder with <code>uvicorn api.main:app --port 8000</code>.</p>
              <button className="ghost" type="button" onClick={() => setBootTry(n => n + 1)}>Try again</button>
            </div>
          ) : <span>Loading PC-Sahayak…</span>}
        </div>
      </div>
    );
  }

  const starting = pending?.chat === 'new';
  const threadPending = pending && (starting || pending.chat === activeId) ? pending : null;
  const busy = !!pending;
  const placeholder = shown?.route.fixed
    ? 'Anything else about this problem?'
    : shown?.route.current ? 'Tell me what happened, or ask a question' : 'Message PC-Sahayak';

  return (
    <div className="app">
      <header className="top">
        <button className="iconbtn only-narrow" type="button" onClick={() => setDrawer(true)}
          aria-label="Show past problems" aria-controls="routes" aria-expanded={drawer}>
          <Menu />
        </button>
        <div className="brand"><Logo />PC-Sahayak</div>
        <button className="iconbtn" type="button" onClick={() => update({ theme: isDark ? 'light' : 'dark' })}
          aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}>
          {isDark ? <Moon /> : <Sun />}
        </button>
        <button className="iconbtn" type="button" ref={gear} onClick={() => { setCloseOpen(false); setSettingsOpen(o => !o); }}
          aria-label="Settings" aria-expanded={settingsOpen} aria-controls="settings">
          <Gear />
        </button>
        <button className="btn-new" type="button" onClick={newProblem}><Plus /><span>New problem</span></button>
        {meta.is_host && (
          <button className="iconbtn power" type="button" ref={power} onClick={() => { setSettingsOpen(false); setCloseOpen(o => !o); }}
            aria-label="Close PC-Sahayak" title="Close PC-Sahayak" aria-expanded={closeOpen} aria-controls="close-confirm">
            <Power />
          </button>
        )}
        {closeOpen && (
          <CloseConfirm shared={(meta.share_urls ?? []).length > 0} anchor={power} onConfirm={closeApp} onCancel={cancelClose} />
        )}
        {settingsOpen && (
          <Settings
            meta={meta} prefs={prefs} chatCount={chats.length} anchor={gear}
            onPrefs={update} onReindex={reindex} onDeleteAll={removeAll} onClose={closeSettings}
          />
        )}
      </header>

      <div className="panes">
        <Sidebar
          chats={chats} activeId={activeId} open={drawer}
          onOpen={openChat} onDelete={remove} onClose={() => setDrawer(false)}
        />

        <main className="pane convo">
          <div className="convo-head">
            <h1>{title}</h1>
            {shown && <span className="ticket">chat #{shown.id.slice(0, 6)}</span>}
          </div>
          {shown && !starting && shown.route.origin && <RouteStrip conv={shown} />}

          <div className="scroll">
            {!meta.llm.configured && (
              <div className="warn-key" role="alert" style={{ maxWidth: 700, margin: '0 auto 20px' }}>
                <b>No Groq API key found.</b>
                <span>Add <code>GROQ_API_KEY</code> to the <code>.env</code> file in the pc-helper folder, then restart the server.</span>
              </div>
            )}
            {(shown || starting) ? (
              <Thread
                messages={starting ? [] : shown!.messages}
                pending={threadPending}
                freshFrom={freshFrom}
                revealIdx={prefs.animate ? revealIdx : null}
                locked={!!shown?.locked}
                onChip={text => { send(text, null); }}
                onRetry={retry}
                onResolve={resolve}
              />
            ) : activeId && loading ? (
              <div className="loading">Loading chat…</div>
            ) : null}
            {!activeId && (
              <Intake key={intakeKey} meta={meta} active={!starting} busy={busy} onStart={start} onError={say} />
            )}
          </div>

          {shown && !starting && (shown.locked ? (
            <div className="locked-bar" role="status">
              <p><b>This problem is solved, so the chat is closed.</b> Unlock it if the problem comes back or you have a follow-up question.</p>
              <button className="ghost" type="button" onClick={unlock}>Unlock chat</button>
            </div>
          ) : (
            <Composer key={shown.id} busy={busy} placeholder={placeholder} onSend={send} onError={say} />
          ))}
        </main>

        <RoutePanel conv={starting ? null : shown} />
      </div>

      {drawer && <div className="scrim" onClick={() => setDrawer(false)} />}
      {toast && <div className="toast" role="status">{toast}</div>}
    </div>
  );
}
