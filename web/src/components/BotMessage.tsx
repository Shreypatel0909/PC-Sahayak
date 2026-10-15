import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage } from '../types';
import { parseReply } from '../lib/reply';
import { useReveal } from '../lib/useReveal';
import { prettyFile } from '../lib/format';
import { BotMark } from './icons';

type HastNode = { type: string; value?: string; children?: HastNode[] };
const textOf = (n?: HastNode): string => (n ? (n.value ?? '') + (n.children ?? []).map(textOf).join('') : '');
const WARNING = /^\s*(warning|caution|important|danger|risk)\b/i;

const mdComponents: Components = {
  // Only real warnings get the caution style; any other quote stays a plain quote.
  blockquote: ({ node, children }) =>
    WARNING.test(textOf(node as HastNode)) ? <div className="caution">{children}</div> : <blockquote>{children}</blockquote>,
  table: ({ children }) => <div className="table-wrap"><table>{children}</table></div>,
  a: ({ href, children }) => <a href={href} target="_blank" rel="noreferrer noopener">{children}</a>,
};

const Md = ({ text }: { text: string }) => (
  <div className="md"><ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>{text}</ReactMarkdown></div>
);

export const Avatar = () => <div className="avatar" aria-hidden="true"><BotMark /></div>;

interface Props {
  message: ChatMessage;
  stepNo: number;
  reveal: boolean;
  isLast: boolean;
  busy: boolean;
  locked: boolean;
  picked: string | null;
  isNew: boolean;
  onChip: (text: string) => void;
  onRetry: () => void;
  onResolve: () => void;
}

export function BotMessage({ message: m, stepNo, reveal, isLast, busy, locked, picked, isNew, onChip, onRetry, onResolve }: Props) {
  const { shown, done } = useReveal(m.content, reveal);
  const cls = `msg-bot${isNew ? ' new' : ''}`;

  if (m.kind === 'error') {
    return (
      <article className={cls}>
        <Avatar />
        <div className="bot-body">
          <div className="err" role="alert">
            <p><b>Couldn't get an answer.</b> {m.content}</p>
            {isLast && <button className="ghost" type="button" onClick={onRetry} disabled={busy}>Try again</button>}
          </div>
        </div>
      </article>
    );
  }

  if (m.tag === 'off_topic') {
    return (
      <article className={cls}>
        <Avatar />
        <div className="bot-body">
          <div className="notice"><span className="eyebrow">Outside what I can help with</span><Md text={shown} /></div>
        </div>
      </article>
    );
  }

  const sections = parseReply(shown);
  const body = sections.map((s, i) => {
    switch (s.kind) {
      case 'understand':
      case 'finding':
        return <div className="understand" key={i}><span className="eyebrow">{s.label}</span><Md text={s.md} /></div>;
      case 'step':
        return (
          <div className="step" key={i}>
            <div className="step-badge" aria-label={`Step ${stepNo}`}>{stepNo}</div>
            <h3>Next step</h3>
            <Md text={s.md} />
          </div>
        );
      case 'expect':
        return <div className="expect" key={i}><span className="eyebrow">Expected result</span><Md text={s.md} /></div>;
      case 'ask':
        return <div className="ask" key={i}><Md text={s.md} /></div>;
      default:
        return <Md text={s.md} key={i} />;
    }
  });

  if (m.tag === 'summary') {
    return (
      <article className={cls}>
        <Avatar />
        <div className="bot-body">
          <div className="summary">
            <div className="summary-head"><span className="tick" aria-hidden="true">✓</span>Problem solved</div>
            {body}
          </div>
        </div>
      </article>
    );
  }

  const live = isLast && !busy && !locked;
  // Offer to close the chat on the latest reply once there is something to have fixed.
  const canResolve = live && stepNo > 0;

  return (
    <article className={cls}>
      <Avatar />
      <div className="bot-body" aria-live={reveal ? 'polite' : undefined}>
        {body}

        {done && (m.suggestions.length > 0 || canResolve) && (
          <div className={`chips${live ? '' : ' answered'}${reveal ? ' blk-in' : ''}`}>
            {m.suggestions.map(s => live
              ? <button className="chip" type="button" key={s} onClick={() => onChip(s)}>{s}</button>
              : <span className={`chip${s === picked ? ' picked' : ''}`} key={s}>{s}</span>)}
            {canResolve && <button className="chip solved" type="button" onClick={onResolve}>✓ This solved it</button>}
          </div>
        )}

        {done && m.sources.length > 0 && (
          <div className={`sources${reveal ? ' blk-in' : ''}`} aria-label="Guides used">
            {m.sources.map(s => <span key={s.file + s.heading}>{prettyFile(s.file)}{s.heading ? ` › ${s.heading}` : ''}</span>)}
          </div>
        )}
      </div>
    </article>
  );
}
