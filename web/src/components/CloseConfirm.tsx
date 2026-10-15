import { useEffect, useRef, useState } from 'react';

interface Props {
  shared: boolean;
  anchor: React.RefObject<HTMLButtonElement>;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
}

/** "Close PC-Sahayak?" confirmation shown under the close button. */
export function CloseConfirm({ shared, anchor, onConfirm, onCancel }: Props) {
  const panel = useRef<HTMLElement>(null);
  const [closing, setClosing] = useState(false);

  useEffect(() => {
    const onDown = (e: PointerEvent) => {
      const t = e.target as Node;
      if (!panel.current?.contains(t) && !anchor.current?.contains(t)) onCancel();
    };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { onCancel(); anchor.current?.focus(); } };
    document.addEventListener('pointerdown', onDown);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('pointerdown', onDown); document.removeEventListener('keydown', onKey); };
  }, [anchor, onCancel]);

  async function close() {
    setClosing(true);
    try { await onConfirm(); } finally { setClosing(false); }
  }

  return (
    <section className="settings close-confirm" id="close-confirm" role="dialog" aria-label="Close PC-Sahayak" ref={panel}>
      <h2>Close PC-Sahayak?</h2>
      <p>This stops PC-Sahayak on this computer.{shared ? ' Phones and other devices using the network link will be disconnected too.' : ''} Your chats stay saved.</p>
      <div className="close-actions">
        <button className="solid-danger" type="button" onClick={close} disabled={closing} autoFocus>
          {closing ? 'Closing…' : 'Close PC-Sahayak'}
        </button>
        <button className="ghost" type="button" onClick={onCancel}>Cancel</button>
      </div>
    </section>
  );
}
