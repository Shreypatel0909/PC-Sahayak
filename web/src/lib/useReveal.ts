import { useEffect, useState } from 'react';

const TOTAL_MS = 2500;   // upper bound for a whole reply
const MAX_STEP_MS = 40;  // never slower than this per word

/** Return `text` revealed word by word (the whole text at once when inactive). */
export function useReveal(text: string, active: boolean): { shown: string; done: boolean } {
  const [count, setCount] = useState(active ? 0 : Infinity);

  useEffect(() => {
    if (!active) { setCount(Infinity); return; }
    const tokens = text.match(/\s*\S+\s*/g) ?? [];
    if (!tokens.length) { setCount(Infinity); return; }
    setCount(0);
    const delay = Math.min(MAX_STEP_MS, TOTAL_MS / tokens.length);
    const perTick = Math.max(1, Math.round(16 / delay));
    let n = 0;
    const id = window.setInterval(() => {
      n += perTick;
      if (n >= tokens.length) { setCount(Infinity); window.clearInterval(id); }
      else setCount(n);
    }, Math.max(delay, 16));
    return () => window.clearInterval(id);
  }, [text, active]);

  if (count === Infinity) return { shown: text, done: true };
  const tokens = text.match(/\s*\S+\s*/g) ?? [];
  return { shown: tokens.slice(0, count).join(''), done: false };
}
