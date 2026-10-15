import { useEffect, useRef } from 'react';
import type { ChatMessage } from '../types';
import { hasStep } from '../lib/reply';
import { when } from '../lib/format';
import { Avatar, BotMessage } from './BotMessage';

export interface Pending {
  text: string;
  imageUrl: string | null;
  retry?: boolean;
}

interface Props {
  messages: ChatMessage[];
  pending: Pending | null;
  freshFrom: number;
  revealIdx: number | null;
  locked: boolean;
  onChip: (text: string) => void;
  onRetry: () => void;
  onResolve: () => void;
}

export function Thread({ messages, pending, freshFrom, revealIdx, locked, onChip, onRetry, onResolve }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  // Keep the newest content in view while replies grow, unless the user scrolled up.
  useEffect(() => {
    const thread = ref.current;
    const scroller = thread?.closest('.scroll') as HTMLElement | null;
    if (!thread || !scroller) return;
    let stick = true;
    const onScroll = () => { stick = scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight < 140; };
    const ro = new ResizeObserver(() => { if (stick) scroller.scrollTop = scroller.scrollHeight; });
    scroller.addEventListener('scroll', onScroll, { passive: true });
    ro.observe(thread);
    scroller.scrollTop = scroller.scrollHeight;
    return () => { ro.disconnect(); scroller.removeEventListener('scroll', onScroll); };
  }, []);

  const shown = pending?.retry && messages.at(-1)?.kind === 'error' ? messages.slice(0, -1) : messages;
  let step = 0;

  return (
    <div className="thread" ref={ref}>
      {shown.length > 0 && <div className="day">{when(shown[0].timestamp)}</div>}
      {shown.map((m, i) => {
        const isNew = i >= freshFrom;
        if (m.role === 'user') {
          return (
            <div className={`msg-user${isNew ? ' new' : ''}`} key={i}>
              {m.image_url && <img className="shot" src={m.image_url} alt="Your screenshot" />}
              {m.content === '(screenshot attached)' && m.image_url ? null : m.content}
            </div>
          );
        }
        if (m.kind === 'normal' && !m.tag && hasStep(m.content)) step += 1;
        const next = shown[i + 1];
        return (
          <BotMessage
            key={i}
            message={m}
            stepNo={step}
            reveal={i === revealIdx}
            isLast={i === shown.length - 1 && !pending}
            busy={!!pending}
            locked={locked}
            picked={next?.role === 'user' ? next.content : null}
            isNew={isNew}
            onChip={onChip}
            onRetry={onRetry}
            onResolve={onResolve}
          />
        );
      })}
      {pending && !pending.retry && (pending.text || pending.imageUrl) && (
        <div className="msg-user new" key={shown.length}>
          {pending.imageUrl && <img className="shot" src={pending.imageUrl} alt="Your screenshot" />}
          {pending.text}
        </div>
      )}
      {pending && (
        <article className="msg-bot new">
          <Avatar />
          <div className="typing" role="status"><i /><i /><i /><em>PC-Sahayak is thinking…</em></div>
        </article>
      )}
    </div>
  );
}
