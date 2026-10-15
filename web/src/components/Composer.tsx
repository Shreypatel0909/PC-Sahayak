import { useCallback, useRef, useState } from 'react';
import { checkImage, usePasteImage } from '../lib/images';
import { Attachment } from './Attachment';
import { Arrow, Clip } from './icons';

interface Props {
  busy: boolean;
  placeholder: string;
  onSend: (text: string, image: File | null) => Promise<boolean>;
  onError: (message: string) => void;
}

export function Composer({ busy, placeholder, onSend, onError }: Props) {
  const [text, setText] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const box = useRef<HTMLTextAreaElement>(null);

  const take = useCallback((file: File) => {
    const problem = checkImage(file);
    if (problem) onError(problem); else setImage(file);
  }, [onError]);
  usePasteImage(!busy, take);

  function grow() {
    const el = box.current;
    if (!el) return;
    el.style.height = '';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }

  async function submit(e?: React.FormEvent) {
    e?.preventDefault();
    const t = text.trim();
    if (busy || (!t && !image)) return;
    const sentImage = image;
    setText(''); setImage(null);
    requestAnimationFrame(grow);
    const ok = await onSend(t, sentImage);
    if (!ok) { setText(t); setImage(sentImage); requestAnimationFrame(grow); }
  }

  function choose() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/png,image/jpeg,image/webp';
    input.onchange = () => { const f = input.files?.[0]; if (f) take(f); };
    input.click();
  }

  return (
    <div className="composer">
      <form onSubmit={submit}>
        {image && <Attachment file={image} onRemove={() => setImage(null)} />}
        <button className="attach" type="button" onClick={choose} aria-label="Attach a screenshot"><Clip /></button>
        <label className="sr" htmlFor="msg">Message</label>
        <textarea
          id="msg" ref={box} rows={1} maxLength={5000} value={text} placeholder={placeholder}
          onChange={e => { setText(e.target.value); grow(); }}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); submit(); } }}
        />
        <button className="send" type="submit" disabled={busy || (!text.trim() && !image)} aria-label="Send"><Arrow /></button>
      </form>
      <div className="hint"><kbd>Enter</kbd> to send · <kbd>Shift</kbd> + <kbd>Enter</kbd> for a new line · paste a screenshot with <kbd>Ctrl</kbd> + <kbd>V</kbd></div>
    </div>
  );
}
